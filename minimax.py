from piece import Piece


#   Это слишком сложно объяснить принцип работы minimax, так что придётся поискать в интернете
def minimax(board, depth, white_move, prev_combo_move=None):
    game_over = board.score(white_move=white_move)
    if not depth or game_over is not None:  # Дошли до нижнего уровня глубины или появилась выигрышная ситуация
        return board.score(), game_over

    best_moves = [float('-inf' if white_move else 'inf'), []]
    for piece_cord, move in board.get_all_valid_moves(white_move, prev_combo_move=prev_combo_move).items():
        for cord_to_move, piece_to_delete in move.items():  # Итерируем все возможные ходы
            new_board = board.copy()    # создаём тестовую доску
            piece_to_move = Piece(*piece_cord, new_board[piece_cord])
            out = new_board.move(piece_to_move, *cord_to_move, piece_to_delete, white_move)  # Делаем на ней ход

            # Вслучае комбо-ходов не меняем параметр "кто сейчас ходит"
            new_white_move = white_move if out else not white_move
            curr_move = piece_cord, cord_to_move, piece_to_delete
            new_score = minimax(new_board, depth - 1, new_white_move, prev_combo_move=out)[0]   # рекурсия
            #   Чем больше new_score, тем лучше ход для противника и тем хуже ход для нас

            if best_moves[0] == new_score:  # если новый ход оказался таким же хорошим, как и все остальные лучшие ходы
                best_moves[1].append(curr_move)
            elif (best_moves[0] < new_score) == white_move:  # нашёлся лучший ход
                best_moves[0] = new_score
                best_moves[1] = [curr_move]

    return best_moves[0], best_moves[1]
