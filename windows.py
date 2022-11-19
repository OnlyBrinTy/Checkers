from PyQt5.QtWidgets import QMainWindow, QWidget

DIFFICULTIES = {'Easy': 1, 'Medium': 3, 'Hard': 5}
NAMES = {1: 'black_checker', 2: 'white_checker', 3: 'black_king', 4: 'white_king'}


class StartWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi('other files/start_window.ui', self)
        self.setWindowIcon(QIcon('pictures/icon.png'))
        self.background.setPixmap(QPixmap('pictures/start_menu_background.jpg'))
        self.comboBox.addItems(DIFFICULTIES)

        self.pushButton.clicked.connect(self.launch_checkers)

    def launch_checkers(self):
        self.game_window = MainWidget(DIFFICULTIES[self.comboBox.currentText()])
        # передаём выбранный уровень сложности
        self.game_window.show()
        self.close()


class MainWidget(QWidget):
    def __init__(self, difficulty):
        super().__init__()

        uic.loadUi('other files/game_window.ui', self)

        self.board = Board()
        self.game = Game(self, difficulty)  # передаём QWidget и выбранный уровень сложности

        # Так как здесь используется многопоточность,
        # для связи с классом Game, который находится в другом потоке
        # будем использовать сигналы, объявленные на строчках 34-37 Game

        self.game.update_widget.connect(self.update)
        self.game.manage_moves.connect(self.manage_selected_moves)
        self.game.make_move.connect(self._send_move_result)
        self.game.send_message.connect(self.show_text)
        self.piecesButtons.buttonClicked.connect(self._go_to_next_move)

        self.game.start()
        # Стартуем run в Game

    def update(self):
        eval("self.setStyleSheet('QPushButton {background-color: rgb(75, 75, 75)}')")

        for cord in self.board.loop_through(lambda t: t != -1):
            button_number = get_btn_number(*cord)
            cell = self.board[tuple(cord)]

            if not cell:
                eval(f"self.pushButton_{button_number}.setStyleSheet('')")
            elif cell:
                eval(f"self.pushButton_{button_number}"
                     f".setStyleSheet(f'background-image: url(pictures/{NAMES[cell]}.png)')")

    def manage_selected_moves(self, clear_moves):
        if self.game.selected_moves and self.game.selected_piece:
            eval("self.setStyleSheet('QPushButton {background-color: rgb(75, 75, 75)}"
                 f"QPushButton#pushButton_{get_btn_number(*self.game.selected_piece())}"
                 " {background-color: rgb(255, 255, 255)}')")
        else:
            self.setStyleSheet('QPushButton {background-color: rgb(75, 75, 75)}')

        for cell in self.game.selected_moves:
            button_number = get_btn_number(*cell)

            if not clear_moves:
                eval(f"self.pushButton_{button_number}."
                     f"setStyleSheet('background-image: url(pictures/move_selection.png)')")
            else:
                eval(f"self.pushButton_{button_number}.setStyleSheet('')")

        self.game.widget_is_done = True

    def show_text(self, message):
        processed_text = []
        for part in message.split('\n'):    # не оставляем куски длиннее 20 символов
            for text_piece in wrap(part, 20):
                processed_text.append(text_piece)

        self.label.setText(f"<p>{'</p><p>'.join(processed_text)}</p>")

    def _send_move_result(self, args):
        self.game.out = self.board.move(*args)
        self.game.widget_is_done = True

    def _go_to_next_move(self, btn):
        cords = get_btn_row_col(int(btn.objectName()[11:]))
        self.game.pressed_button = cords

        self.game.start()


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QPixmap, QIcon
    from PyQt5 import uic
    from textwrap import wrap
    from board import *
    from game import Game

    app = QApplication([])
    sw = StartWindow()
    sw.show()
    app.exec()
