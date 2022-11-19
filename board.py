from piece import Piece
from sqlite3 import connect
from numpy import array, where, transpose, count_nonzero, int8


class Board:
    def __init__(self, copied_table=None):
        # copied_table нужен, если мы создаём тестовыю доску скопированную с другой доски для просчёта minimax
        # доска с copied_table никак не связана с sql БД
        if copied_table is None:
            self._cur = connect('other files/data.db').cursor()
            self._table = self._get_board()
        else:
            self._table = copied_table

        self.is_copy = copied_table is not None

    def score(self, white_move=None):
        # Количества шашек всех типов
        bl_checkers, wh_checkers, bl_kings, wh_kings = map(lambda i: count_nonzero(self() == i), range(1, 5))

        if white_move is not None:  # Если нужно узнать, кто выиграл
            if not wh_checkers + wh_kings or not bl_checkers + bl_kings or not any(self.get_all_valid_moves(white_move).values()):
                return wh_checkers + wh_kings > bl_checkers + bl_kings
        else:  # Если нужно узнать счёт, который высчитывается по следующей формуле
            return wh_checkers - bl_checkers + (wh_kings - bl_kings) / 2

    def move(self, piece, row, col, piece_to_delete, white_move):
        deleted_piece = (Piece(*piece_to_delete()),) if piece_to_delete else ()  # Приводим piece_to_delete в форму
        new_king = row == (1 - piece.kind % 2) * 7 and piece.kind <= 2  # Теперь это дамка
        next_piece_kind = piece.kind + int(new_king) * 2  # Изменяем тип на дамку

        # Все изменения доски приводим в кортеж
        changes = (Piece(*piece()), Piece(row, col, next_piece_kind)) + deleted_piece
        self._change(changes)

        # Об этом я говорил в 98 строке Game. Если следующий ход станет комбо-ходом или
        # если мы стали дамкой. По правилу после становления дамкой даётся дополнительный ход, но только этой дамке.
        # То есть ситуация такая же, как и с комбо-ходом. Мы выбираем Единственную шашку, которая может ходить.
        if piece_to_delete and any(self.get_all_valid_moves(white_move)[(row, col)].values()) or new_king:
            return row, col

    # Следующие три метода по вычислению возможных ходов будет проще понять при отладке
    def get_all_valid_moves(self, white_move, eat_moves=False, prev_combo_move=None):
        def clear_empties(moves):
            return dict(filter(lambda t: t[1], moves.items()))

        all_valid_moves = {}
        for cord in self.loop_through(lambda t: (t > 0) & (t % 2 != white_move)):
            current_piece = Piece(*cord, self[tuple(cord)])
            piece_moves = {}

            if not prev_combo_move:
                piece_moves = self._valid_moves(current_piece)

                if eat_moves:
                    piece_moves = clear_empties(piece_moves)
                elif piece_moves and any(piece_moves.values()):
                    return self.get_all_valid_moves(white_move, eat_moves=True)
            elif current_piece() == prev_combo_move:
                piece_moves = self._valid_moves(current_piece)

                if any(piece_moves.values()):
                    piece_moves = clear_empties(piece_moves)

            all_valid_moves[current_piece()] = piece_moves

        return all_valid_moves

    def _valid_moves(self, piece):
        moves = {}
        row, col, kind = *piece(), piece.kind

        if kind <= 2:
            v_min, v_max = max(piece.row - 3, -1), min(piece.row + 3, 8)
            h_min, h_max = max(piece.col - 3, -1), min(piece.col + 3, 8)
            eat_only = piece.kind % 2 == 0
        else:
            v_min, v_max = h_min, h_max = -1, 8
            eat_only = False

        moves.update(self._check_diagonal((row - 1, v_min, -1), (col - 1, h_min, -1), kind, eat_only))
        moves.update(self._check_diagonal((row - 1, v_min, -1), (col + 1, h_max, 1), kind, eat_only))

        eat_only = not eat_only if kind <= 2 else eat_only

        moves.update(self._check_diagonal((row + 1, v_max, 1), (col - 1, h_min, -1), kind, eat_only))
        moves.update(self._check_diagonal((row + 1, v_max, 1), (col + 1, h_max, 1), kind, eat_only))

        return moves

    def _check_diagonal(self, v_range, h_range, kind, eat_only):
        moves = {}
        next_piece = None

        for cord in zip(range(*v_range), range(*h_range)):
            cell = Piece(*cord, self[cord])

            if cell.kind:
                if cell.kind % 2 == kind % 2 or next_piece:
                    break

                next_piece = cell
            else:
                if next_piece or not eat_only:
                    moves[cord] = next_piece

                if kind <= 2:
                    break

        return moves

    def _get_board(self):
        return array(self._cur.execute("""SELECT * FROM data""").fetchall(), dtype=int8)

    def _change(self, changes):
        if self.is_copy:
            for piece in changes:
                self._table[piece()] = piece.kind
        else:
            for piece in changes:
                self._cur.execute(f"""UPDATE data
                            SET '{piece.col}' = {piece.kind}
                            WHERE rowid = {piece.row + 1}""")

            self._table = self._get_board()

    def loop_through(self, condition):  # Возвращает координаты доски удовлетворяющие условию
        return transpose(where(condition(self())))

    def get_cell_kind(self, *cord):
        return self[cord]

    def copy(self):
        return Board(copied_table=self._table.copy())

    def __call__(self):
        return self._table

    def __getitem__(self, item):
        return self._table[item]


def get_btn_number(row, col):  # Формула нахождения номера кнопки в виджете по координатам
    if col % 2:
        addon = row // 2 + 1
    else:
        addon = (row + 1) // 2

    return col * 4 + addon


def get_btn_row_col(btn_number):  # Формула нахождения координат кнопки по номеру в виджете
    col = (btn_number - 1) // 4

    if col % 2 == 0:
        row = btn_number % 4 * 2 - 1
    else:
        row = (btn_number % 4 - 1) * 2

    if row < 0:
        row = 8 + row

    return row, col
