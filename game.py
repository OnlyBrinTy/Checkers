from random import choice
from time import process_time, sleep
from PyQt5.QtCore import QThread, pyqtSignal
from minimax import minimax
from piece import Piece

PHRASES = {'start': ('Эта игра не на жизнь, а насмерть! Всё, что ты имеешь в своей жизни на кону.',
                     'Не стоило тебе со своей семьёй гулять по заброшенной школе. Кто вообще сюда с семьёй ходит?'
                     ' Неважно. Теперь твоя семья и ты стоят на кону!',
                     'Один ошибочный ход, и ты вместе со своей семьёй отправляешься к Опостолу Петру'),
           'you_are_losing': ('Не зря меня папа в детстве научил играть!', 'Ты на одну шашку ближе к смерти!',
                              'Хорошо, что мне от мамы перешёл высокий интелект... и маньяческие наклонности.',
                              'Выкуси, победа точно за мной!', 'Узри мою истинную мощь!'),
           'enemy_is_losing': (
               'Да чтоб на тебя бюст Ленина упал!', '@#!&#@!', 'Я смотрю папа тоже тебя учил играть в детстве.',
               'Как ты это умудряешься делать?', 'Ты задолбал хорошо играть'),
           'you_won': ('Ладно. Иди на свободу, заслужил',
                       'Поздравляю! Ты остался в живых. Я тебя не удерживаю тут, теперь ты свободен.',
                       'Уходи! Я пока ещё добрый.'),
           'enemy_won': ('Твои последние слова?\n...\nМолчишь?\n...\nТогда у меня плохие новости.',
                         'Я сегодня добрый, так что оставлю тебя при жизни. Не благодари.')}

MESSAGES = ()
AI_DELAY = 1
TECH_DELAY = 10 ** -5
PHRASE_PROBABILITY = (True,) + (False,) * 4
WHITE_MOVE = True
AI_IS_WHITE = True


class Game(QThread):
    update_widget = pyqtSignal()
    manage_moves = pyqtSignal(bool)
    send_message = pyqtSignal(str)
    make_move = pyqtSignal(tuple)

    def __init__(self, widget, difficulty):
        super().__init__()

        self.widget = widget
        self.complexity = difficulty
        self.widget_is_done = False  # Класс будет Game ждать пока функция из MainWindow не выполнилась
        self.first_run = True

    def run(self):
        if self.first_run:
            self.first_run = False
            self.send_message.emit(choice(PHRASES['start']))  # Отправляем сообщение на другой поток
            self.next_move(first_move=True)  # Начинаем следующий ход
        else:
            self.your_move(self.pressed_button)  # По нажатию одной из кнопок

    def next_move(self, first_move=False, prev_combo_move=None, previous_score=None):
        if first_move:
            self.previous_score = self.widget.board.score()
            self.white_move = WHITE_MOVE
            self.selected_piece = None
        else:
            new_score = self.widget.board.score()

            if choice(PHRASE_PROBABILITY):  # Иногда соперник будет говорть с вами
                if self.previous_score > new_score:  # Противник начинает проигрывать
                    self.send_message.emit(choice(PHRASES['enemy_is_losing']))
                elif self.previous_score < new_score:  # Противник начинает побеждать
                    self.send_message.emit(choice(PHRASES['you_are_losing']))

            self.previous_score = previous_score

            if not prev_combo_move:  # Вслучае комбо-ходов не меняем параметр "кто сейчас ходит"
                self.white_move = not self.white_move

        self.update_widget.emit()  # обновляем экран

        if self.white_move == AI_IS_WHITE:  # Если ход противника
            self.machines_move()
        else:
            self.selected_moves = {}
            self._all_moves = self.widget.board.get_all_valid_moves(self.white_move, prev_combo_move=prev_combo_move)
            # Находим все возможные для себя ходы

    def machines_move(self):
        start = process_time()  # Начало таймера
        score, result = minimax(self.widget.board, self.complexity, self.white_move)  # Алгоритм для нахождения ходов
        end = process_time()  # Конец таймера

        sleep(max(0, AI_DELAY - start + end))  # делаем задержку в зависимости от потраченного времени

        if type(result) is list:  # Если игра не закончилась
            piece_cord, cord_to_move, piece_to_delete = choice(result)  # случайно выбираем из одинаково ценных ходов
            piece_to_move = Piece(*piece_cord, self.widget.board[piece_cord])
            # piece_cord - координаты шашки для хода, cord_to_move - куда ходить, piece_to_delete - кого перепрыгнули

            self.make_move.emit((piece_to_move, *cord_to_move, piece_to_delete, self.white_move))

            self.wait_for_answer()  # Ждём ответа от другого потока
            # self.out - это ответ от другого потока. Пока мы ждали поменялась доска в БД
            # self.out - это координаты после съедения, пересекающиеся с координатами начала
            # съедения следующего потенцального комбо-хода. То есть если вы сходите-съедите
            # на клетку откуда начинается следующее съедение, будет комбо-ход
            self.next_move(prev_combo_move=self.out, previous_score=score)

        new_score = self.widget.board.score(white_move=self.white_move)
        if new_score:
            self.send_message.emit(choice(PHRASES['enemy_won']))
        elif new_score is not None:
            self.send_message.emit(choice(PHRASES['you_won']))

    def your_move(self, cords):
        if self.white_move != AI_IS_WHITE:
            self.manage_moves.emit(True)  # Очищаем выделение возможных ходов на экране
            self.wait_for_answer()  # Ждём когда закончит

            if cords in self.selected_moves:  # Если нажали на выделенную клетку
                self.make_move.emit((self.selected_piece, *cords, self.selected_moves[cords], self.white_move))
                score = self.widget.board.score()

                self.wait_for_answer()
                self.next_move(prev_combo_move=self.out, previous_score=score)

                if self.out:
                    self.select_piece(self.out)
            else:  # Ещё не выбрали ход
                self.selected_moves = {}
                self.select_piece(cords)

    def select_piece(self, cords):
        cell_kind = self.widget.board.get_cell_kind(*cords)

        if cell_kind and cell_kind % 2 != self.white_move:  # Если это не пустая клетка и не вражеская шашка
            self.selected_piece = Piece(*cords, cell_kind)
            self.selected_moves = self._all_moves[self.selected_piece()]

            self.manage_moves.emit(False)  # Подсвечиваем возможные ходы
            self.wait_for_answer()

    def wait_for_answer(self):
        while not self.widget_is_done:
            sleep(TECH_DELAY)

        self.widget_is_done = False
