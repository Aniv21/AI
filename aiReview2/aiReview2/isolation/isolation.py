import random
import timeit
from copy import copy

TIME_LIMIT_MILLIS = 150


class Board(object):
    BLANK = 0
    NOT_MOVED = None

    def __init__(self, player_1, player_2, width=7, height=7):
        self.width = width
        self.height = height
        self.move_count = 0
        self._player_1 = player_1
        self._player_2 = player_2
        self._active_player = player_1
        self._inactive_player = player_2

        self._board_state = [Board.BLANK] * (width * height + 3)
        self._board_state[-1] = Board.NOT_MOVED
        self._board_state[-2] = Board.NOT_MOVED

    def hash(self):
        return str(self._board_state).__hash__()

    @property
    def active_player(self):
        return self._active_player

    @property
    def inactive_player(self):
        return self._inactive_player

    def get_opponent(self, player):
        """Return the opponent of the supplied player.
        """
        if player == self._active_player:
            return self._inactive_player
        elif player == self._inactive_player:
            return self._active_player
        raise RuntimeError("`player` must be an object registered as a player in the current game.")

    def copy(self):
        new_board = Board(self._player_1, self._player_2, width=self.width, height=self.height)
        new_board.move_count = self.move_count
        new_board._active_player = self._active_player
        new_board._inactive_player = self._inactive_player
        new_board._board_state = copy(self._board_state)
        return new_board

    def forecast_move(self, move):
        new_board = self.copy()
        new_board.apply_move(move)
        return new_board

    def move_is_legal(self, move):
        idx = move[0] + move[1] * self.height
        return (0 <= move[0] < self.height and 0 <= move[1] < self.width and
                self._board_state[idx] == Board.BLANK)

    def get_blank_spaces(self):
        return [(i, j) for j in range(self.width) for i in range(self.height)
                if self._board_state[i + j * self.height] == Board.BLANK]

    def get_player_location(self, player):
        if player == self._player_1:
            if self._board_state[-1] == Board.NOT_MOVED:
                return Board.NOT_MOVED
            idx = self._board_state[-1]
        elif player == self._player_2:
            if self._board_state[-2] == Board.NOT_MOVED:
                return Board.NOT_MOVED
            idx = self._board_state[-2]
        else:
            raise RuntimeError(
                "Invalid player in get_player_location: {}".format(player))
        w = idx // self.height
        h = idx % self.height
        return (h, w)

    def get_legal_moves(self, player=None):
        if player is None:
            player = self.active_player
        return self.__get_moves(self.get_player_location(player))

    def apply_move(self, move):
        idx = move[0] + move[1] * self.height
        last_move_idx = int(self.active_player == self._player_2) + 1
        self._board_state[-last_move_idx] = idx
        self._board_state[idx] = 1
        self._board_state[-3] ^= 1
        self._active_player, self._inactive_player = self._inactive_player, self._active_player
        self.move_count += 1

    def is_winner(self, player):
        """ Test whether the specified player has won the game. """
        return player == self._inactive_player and not self.get_legal_moves(self._active_player)

    def is_loser(self, player):
        """ Test whether the specified player has lost the game. """
        return player == self._active_player and not self.get_legal_moves(self._active_player)

    def utility(self, player):
        if not self.get_legal_moves(self._active_player):

            if player == self._inactive_player:
                return float("inf")

            if player == self._active_player:
                return float("-inf")

        return 0.

    def __get_moves(self, loc):
        if loc == Board.NOT_MOVED:
            return self.get_blank_spaces()

        r, c = loc
        directions = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                      (1, -2), (1, 2), (2, -1), (2, 1)]
        valid_moves = [(r + dr, c + dc) for dr, dc in directions
                       if self.move_is_legal((r + dr, c + dc))]
        random.shuffle(valid_moves)
        return valid_moves

    def print_board(self):
        return self.to_string()

    def to_string(self, symbols=['1', '2']):
        p1_loc = self._board_state[-1]
        p2_loc = self._board_state[-2]

        col_margin = len(str(self.height - 1)) + 1
        prefix = "{:<" + "{}".format(col_margin) + "}"
        offset = " " * (col_margin + 3)
        out = offset + '   '.join(map(str, range(self.width))) + '\n\r'
        for i in range(self.height):
            out += prefix.format(i) + ' | '
            for j in range(self.width):
                idx = i + j * self.height
                if not self._board_state[idx]:
                    out += ' '
                elif p1_loc == idx:
                    out += symbols[0]
                elif p2_loc == idx:
                    out += symbols[1]
                else:
                    out += '-'
                out += ' | '
            out += '\n\r'

        return out

    def play(self, time_limit=TIME_LIMIT_MILLIS):
        move_history = []

        time_millis = lambda: 1000 * timeit.default_timer()

        while True:

            legal_player_moves = self.get_legal_moves()
            game_copy = self.copy()

            move_start = time_millis()
            time_left = lambda : time_limit - (time_millis() - move_start)
            curr_move = self._active_player.get_move(game_copy, time_left)
            move_end = time_left()

            if curr_move is None:
                curr_move = Board.NOT_MOVED

            if move_end < 0:
                return self._inactive_player, move_history, "timeout"

            if curr_move not in legal_player_moves:
                if len(legal_player_moves) > 0:
                    return self._inactive_player, move_history, "forfeit"
                return self._inactive_player, move_history, "illegal move"

            move_history.append(list(curr_move))

            self.apply_move(curr_move)
