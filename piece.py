class Piece:
    def __init__(self, row, col, kind=0):
        self.row = row  # ряд
        self.col = col  # колонка
        self.kind = kind  # тип от 0 до 4
        # 0 - черная клетка; 1 - черная шашка; 2 - белая шашка; 3 - черный король; 4 - белый король

    def __call__(self):
        return self.row, self.col

    def __eq__(self, other):
        return self() == other() and self.kind == other.kind
