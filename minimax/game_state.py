import math
import random

PIECE_VAL = {
    "p": 100,
    "n": 320,
    "b": 330,
    "r": 500,
    "q": 900,
    "k": 0,
}

# Piece-square tables from White perspective (row 0 = Black back rank).
PST = {
    "p": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 35, 35, 20, 10, 10],
        [5, 5, 10, 25, 25, 10, 5, 5],
        [0, 0, 0, 20, 20, 0, 0, 0],
        [5, -5, -10, 0, 0, -10, -5, 5],
        [5, 10, 10, -25, -25, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ],
    "n": [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20, 0, 0, 0, 0, -20, -40],
        [-30, 0, 10, 15, 15, 10, 0, -30],
        [-30, 5, 15, 20, 20, 15, 5, -30],
        [-30, 0, 15, 20, 20, 15, 0, -30],
        [-30, 5, 10, 15, 15, 10, 5, -30],
        [-40, -20, 0, 5, 5, 0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50],
    ],
    "b": [
        [-20, -10, -10, -10, -10, -10, -10, -20],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-10, 0, 5, 10, 10, 5, 0, -10],
        [-10, 5, 5, 10, 10, 5, 5, -10],
        [-10, 0, 10, 10, 10, 10, 0, -10],
        [-10, 10, 10, 10, 10, 10, 10, -10],
        [-10, 5, 0, 0, 0, 0, 5, -10],
        [-20, -10, -10, -10, -10, -10, -10, -20],
    ],
    "r": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [5, 10, 10, 10, 10, 10, 10, 5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [0, 0, 0, 5, 5, 0, 0, 0],
    ],
    "q": [
        [-20, -10, -10, -5, -5, -10, -10, -20],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-10, 0, 5, 5, 5, 5, 0, -10],
        [-5, 0, 5, 5, 5, 5, 0, -5],
        [0, 0, 5, 5, 5, 5, 0, -5],
        [-10, 5, 5, 5, 5, 5, 0, -10],
        [-10, 0, 5, 0, 0, 0, 0, -10],
        [-20, -10, -10, -5, -5, -10, -10, -20],
    ],
    "k": [
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-20, -30, -30, -40, -40, -30, -30, -20],
        [-10, -20, -20, -20, -20, -20, -20, -10],
        [20, 20, 0, 0, 0, 0, 20, 20],
        [20, 30, 10, 0, 0, 10, 30, 20],
    ],
}

CENTER4 = {(3, 3), (3, 4), (4, 3), (4, 4)}
CENTER16 = {
    (2, 2), (2, 3), (2, 4), (2, 5),
    (3, 2), (3, 5),
    (4, 2), (4, 5),
    (5, 2), (5, 3), (5, 4), (5, 5),
}


def _ib(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def _enemy(a, b):
    return bool(a and b and a[0] != b[0])


def _other(color):
    return "b" if color == "w" else "w"


def _pst_value(color, piece_type, r, c):
    table = PST[piece_type]
    if color == "w":
        return table[r][c]
    return table[7 - r][c]


class GameState:
    """
    Immutable-style game state used by MCTS.

    Includes enough metadata to model draw rules inside search:
    - halfmove clock for 50-move rule
    - position history for threefold repetition
    """

    __slots__ = [
        "board",
        "turn",
        "cr",
        "ep",
        "halfmove_clock",
        "history",
        "_position_key_cache",
        "_search_key_cache",
        "_repetition_cache",
        "_in_check_cache",
        "_raw_cache",
        "_legal_cache",
        "_all_moves_cache",
        "_ordered_moves_cache",
        "_mobility_cache",
        "_eval_cache",
        "_terminal_cache",
    ]

    def __init__(
        self,
        board,
        turn,
        cr,
        ep,
        halfmove_clock=0,
        history=None,
        assume_copied=False,
    ):
        self.board = board if assume_copied else [row[:] for row in board]
        self.turn = turn
        self.cr = {"w": dict(cr["w"]), "b": dict(cr["b"])}
        self.ep = ep
        self.halfmove_clock = halfmove_clock

        self._position_key_cache = None
        self._search_key_cache = None
        self._repetition_cache = None
        self._in_check_cache = {}
        self._raw_cache = {}
        self._legal_cache = {}
        self._all_moves_cache = None
        self._ordered_moves_cache = None
        self._mobility_cache = {}
        self._eval_cache = {}
        self._terminal_cache = {}

        if history is None:
            self.history = (self.position_key(),)
        else:
            self.history = tuple(history)

    @staticmethod
    def _compose_position_key(board, turn, cr, ep):
        board_key = tuple(tuple(row) for row in board)
        cr_key = (cr["w"]["K"], cr["w"]["Q"], cr["b"]["K"], cr["b"]["Q"])
        return board_key, turn, cr_key, ep

    def position_key(self):
        if self._position_key_cache is None:
            self._position_key_cache = self._compose_position_key(
                self.board, self.turn, self.cr, self.ep
            )
        return self._position_key_cache

    def repetition_count(self):
        if self._repetition_cache is None:
            k = self.position_key()
            self._repetition_cache = sum(1 for x in self.history if x == k)
        return self._repetition_cache

    def search_key(self):
        if self._search_key_cache is None:
            # Include draw-relevant counters so reused nodes do not cross incompatible states.
            self._search_key_cache = (
                self.position_key(),
                self.halfmove_clock,
                min(3, self.repetition_count()),
            )
        return self._search_key_cache

    def clone(self):
        return GameState(
            self.board,
            self.turn,
            self.cr,
            self.ep,
            halfmove_clock=self.halfmove_clock,
            history=self.history,
        )

    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == color + "k":
                    return (r, c)
        return None

    def _raw(self, r, c, castle=True):
        key = (r, c, castle)
        if key in self._raw_cache:
            return self._raw_cache[key]

        b = self.board
        p = b[r][c]
        if not p:
            self._raw_cache[key] = ()
            return ()

        color, pt = p[0], p[1]
        moves = []

        if pt == "p":
            d = -1 if color == "w" else 1
            if _ib(r + d, c) and not b[r + d][c]:
                moves.append((r + d, c))
                start_row = 6 if color == "w" else 1
                if r == start_row and not b[r + 2 * d][c]:
                    moves.append((r + 2 * d, c))

            for dc in (-1, 1):
                nr, nc = r + d, c + dc
                if _ib(nr, nc) and _enemy(p, b[nr][nc]):
                    moves.append((nr, nc))

            if self.ep:
                er, ec = self.ep
                if r + d == er and abs(c - ec) == 1:
                    moves.append(self.ep)

        if pt in ("r", "b", "q"):
            dirs = []
            if pt in ("r", "q"):
                dirs += [(1, 0), (-1, 0), (0, 1), (0, -1)]
            if pt in ("b", "q"):
                dirs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]

            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while _ib(nr, nc):
                    if not b[nr][nc]:
                        moves.append((nr, nc))
                    else:
                        if _enemy(p, b[nr][nc]):
                            moves.append((nr, nc))
                        break
                    nr += dr
                    nc += dc

        if pt == "n":
            jumps = [
                (2, 1), (2, -1), (-2, 1), (-2, -1),
                (1, 2), (1, -2), (-1, 2), (-1, -2),
            ]
            for dr, dc in jumps:
                nr, nc = r + dr, c + dc
                if _ib(nr, nc) and (not b[nr][nc] or _enemy(p, b[nr][nc])):
                    moves.append((nr, nc))

        if pt == "k":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr or dc:
                        nr, nc = r + dr, c + dc
                        if _ib(nr, nc) and (not b[nr][nc] or _enemy(p, b[nr][nc])):
                            moves.append((nr, nc))

            if castle and not self.in_check(color):
                row = 7 if color == "w" else 0
                if r == row and c == 4:
                    if self.cr[color]["K"] and b[row][7] == color + "r":
                        if not b[row][5] and not b[row][6]:
                            s1 = self.apply((r, c), (row, 5), track_history=False)
                            s2 = self.apply((r, c), (row, 6), track_history=False)
                            if not s1.in_check(color) and not s2.in_check(color):
                                moves.append((row, 6))

                    if self.cr[color]["Q"] and b[row][0] == color + "r":
                        if not b[row][1] and not b[row][2] and not b[row][3]:
                            s1 = self.apply((r, c), (row, 3), track_history=False)
                            s2 = self.apply((r, c), (row, 2), track_history=False)
                            if not s1.in_check(color) and not s2.in_check(color):
                                moves.append((row, 2))

        res = tuple(moves)
        self._raw_cache[key] = res
        return res

    def in_check(self, color):
        if color in self._in_check_cache:
            return self._in_check_cache[color]

        king = self.find_king(color)
        if not king:
            self._in_check_cache[color] = True
            return True

        enemy = _other(color)
        for r in range(8):
            for c in range(8):
                pc = self.board[r][c]
                if pc and pc[0] == enemy:
                    if king in self._raw(r, c, castle=False):
                        self._in_check_cache[color] = True
                        return True

        self._in_check_cache[color] = False
        return False

    def legal_moves(self, r, c):
        key = (r, c)
        if key in self._legal_cache:
            return self._legal_cache[key]

        p = self.board[r][c]
        if not p:
            self._legal_cache[key] = ()
            return ()

        color = p[0]
        valid = []
        for move in self._raw(r, c, castle=True):
            child = self.apply((r, c), move, track_history=False)
            if not child.in_check(color):
                valid.append(move)

        res = tuple(valid)
        self._legal_cache[key] = res
        return res

    def all_moves(self):
        if self._all_moves_cache is not None:
            return self._all_moves_cache

        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece[0] == self.turn:
                    for to in self.legal_moves(r, c):
                        moves.append(((r, c), to))

        self._all_moves_cache = tuple(moves)
        return self._all_moves_cache

    def move_heuristic(self, move):
        (r0, c0), (r1, c1) = move
        p = self.board[r0][c0]
        target = self.board[r1][c1]

        score = 0

        if target:
            score += 1200 + 15 * PIECE_VAL[target[1]] - PIECE_VAL[p[1]]

        if p[1] == "p" and (r1 == 0 or r1 == 7):
            score += 900

        if p[1] == "k" and abs(c1 - c0) == 2:
            score += 90

        if self.ep and p[1] == "p" and (r1, c1) == self.ep:
            score += 450

        if (r1, c1) in CENTER4:
            score += 35
        elif (r1, c1) in CENTER16:
            score += 12

        child = self.apply((r0, c0), (r1, c1), track_history=False)
        if child.in_check(child.turn):
            score += 180

        return score

    def ordered_moves(self):
        if self._ordered_moves_cache is not None:
            return self._ordered_moves_cache

        moves = list(self.all_moves())
        moves.sort(key=self.move_heuristic, reverse=True)
        self._ordered_moves_cache = tuple(moves)
        return self._ordered_moves_cache

    def apply(self, fr, to, track_history=True):
        r0, c0 = fr
        r1, c1 = to

        b = [row[:] for row in self.board]
        p = b[r0][c0]
        captured = b[r1][c1]

        cr = {"w": dict(self.cr["w"]), "b": dict(self.cr["b"])}

        if captured == "wr":
            if (r1, c1) == (7, 0):
                cr["w"]["Q"] = False
            if (r1, c1) == (7, 7):
                cr["w"]["K"] = False
        if captured == "br":
            if (r1, c1) == (0, 0):
                cr["b"]["Q"] = False
            if (r1, c1) == (0, 7):
                cr["b"]["K"] = False

        if p[1] == "p" and self.ep and (r1, c1) == self.ep and not captured:
            captured = b[r0][c1]
            b[r0][c1] = ""

        b[r1][c1] = p
        b[r0][c0] = ""

        if p[1] == "k":
            cr[p[0]] = {"K": False, "Q": False}
            if c1 == 6:
                b[r1][5] = b[r1][7]
                b[r1][7] = ""
            elif c1 == 2:
                b[r1][3] = b[r1][0]
                b[r1][0] = ""

        if p == "wr":
            if (r0, c0) == (7, 0):
                cr["w"]["Q"] = False
            if (r0, c0) == (7, 7):
                cr["w"]["K"] = False
        if p == "br":
            if (r0, c0) == (0, 0):
                cr["b"]["Q"] = False
            if (r0, c0) == (0, 7):
                cr["b"]["K"] = False

        if p[1] == "p" and abs(r1 - r0) == 2:
            ep = ((r1 + r0) // 2, c1)
        else:
            ep = None

        if p == "wp" and r1 == 0:
            b[r1][c1] = "wq"
        elif p == "bp" and r1 == 7:
            b[r1][c1] = "bq"

        halfmove = 0 if (p[1] == "p" or bool(captured)) else self.halfmove_clock + 1
        next_turn = _other(self.turn)

        if track_history:
            next_key = self._compose_position_key(b, next_turn, cr, ep)
            history = self.history + (next_key,)
        else:
            history = self.history

        return GameState(
            b,
            next_turn,
            cr,
            ep,
            halfmove_clock=halfmove,
            history=history,
            assume_copied=True,
        )

    def _is_passed_pawn(self, color, r, c):
        enemy = _other(color)
        step = -1 if color == "w" else 1
        rr = r + step
        while 0 <= rr < 8:
            for cc in (c - 1, c, c + 1):
                if _ib(rr, cc) and self.board[rr][cc] == enemy + "p":
                    return False
            rr += step
        return True

    def _pseudo_mobility(self, color):
        if color in self._mobility_cache:
            return self._mobility_cache[color]

        count = 0
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p[0] == color:
                    count += len(self._raw(r, c, castle=False))

        self._mobility_cache[color] = count
        return count

    def _insufficient_material(self):
        side = {"w": [], "b": []}

        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p[1] != "k":
                    side[p[0]].append(p[1])

        w = sorted(side["w"])
        b = sorted(side["b"])

        if not w and not b:
            return True

        if len(w) == 1 and not b and w[0] in ("b", "n"):
            return True
        if len(b) == 1 and not w and b[0] in ("b", "n"):
            return True

        if not b and w == ["n", "n"]:
            return True
        if not w and b == ["n", "n"]:
            return True

        if len(w) == 1 and len(b) == 1 and w[0] in ("b", "n") and b[0] in ("b", "n"):
            return True

        return False

    def is_draw(self):
        if self.halfmove_clock >= 100:
            return True
        if self.repetition_count() >= 3:
            return True
        if self._insufficient_material():
            return True
        return False

    def terminal_result_for(self, perspective):
        if perspective in self._terminal_cache:
            return self._terminal_cache[perspective]

        if self.is_draw():
            self._terminal_cache[perspective] = 0.0
            return 0.0

        moves = self.all_moves()
        if moves:
            self._terminal_cache[perspective] = None
            return None

        if self.in_check(self.turn):
            winner = _other(self.turn)
            res = 1.0 if winner == perspective else -1.0
            self._terminal_cache[perspective] = res
            return res

        self._terminal_cache[perspective] = 0.0
        return 0.0

    def _pawn_structure_score(self, perspective, pawns_by_file, pawn_positions):
        score = 0

        for side in ("w", "b"):
            sign = 1 if side == perspective else -1

            files = pawns_by_file[side]
            for file_idx, cnt in enumerate(files):
                if cnt > 1:
                    score += sign * (-14 * (cnt - 1))

            for r, c in pawn_positions[side]:
                left = files[c - 1] if c > 0 else 0
                right = files[c + 1] if c < 7 else 0
                if left == 0 and right == 0:
                    score += sign * -10

                if self._is_passed_pawn(side, r, c):
                    advanced = (6 - r) if side == "w" else (r - 1)
                    score += sign * (20 + 6 * max(0, advanced))

        return score

    def evaluate(self, perspective):
        if perspective in self._eval_cache:
            return self._eval_cache[perspective]

        terminal = self.terminal_result_for(perspective)
        if terminal is not None:
            val = terminal * 100000.0
            self._eval_cache[perspective] = val
            return val

        score = 0.0
        bishops = {"w": 0, "b": 0}
        pawns_by_file = {"w": [0] * 8, "b": [0] * 8}
        pawn_positions = {"w": [], "b": []}

        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if not p:
                    continue

                color, pt = p[0], p[1]
                sign = 1 if color == perspective else -1

                piece_score = PIECE_VAL[pt] + _pst_value(color, pt, r, c)
                score += sign * piece_score

                if pt == "b":
                    bishops[color] += 1
                if pt == "p":
                    pawns_by_file[color][c] += 1
                    pawn_positions[color].append((r, c))

                if (r, c) in CENTER4:
                    score += sign * 16
                elif (r, c) in CENTER16:
                    score += sign * 6

        if bishops[perspective] >= 2:
            score += 35
        if bishops[_other(perspective)] >= 2:
            score -= 35

        score += self._pawn_structure_score(perspective, pawns_by_file, pawn_positions)

        my_mob = self._pseudo_mobility(perspective)
        op_mob = self._pseudo_mobility(_other(perspective))
        score += 2.0 * (my_mob - op_mob)

        if self.in_check(perspective):
            score -= 70
        if self.in_check(_other(perspective)):
            score += 70

        self._eval_cache[perspective] = score
        return score


# Global caches for reuse between turns.
_TT_STATS = {}
_LAST_ROOT = None
_DEBUG = False


def reset_search_state():
    """Clear global search caches between games."""
    global _LAST_ROOT
    _TT_STATS.clear()
    _LAST_ROOT = None


class Node:
    C = 1.25
    PRIOR_SCALE = 0.08
    ROLLOUT_DEPTH = 16

    __slots__ = [
        "state",
        "parent",
        "move",
        "children",
        "visits",
        "wins",
        "untried",
        "prior",
    ]

    def __init__(self, state, parent=None, move=None, prior=0.0):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.wins = 0.0
        self.prior = prior

        key = state.search_key()
        if parent is not None and key in _TT_STATS:
            old_wins, old_visits = _TT_STATS[key]
            # Decayed warm start from transposition stats.
            self.wins = old_wins * 0.35
            self.visits = int(old_visits * 0.35)

        # Best moves are popped first from the end of this reversed list.
        self.untried = list(reversed(state.ordered_moves()))

    def ucb(self):
        if self.visits == 0:
            return float("inf")

        exploit = self.wins / self.visits
        explore = self.C * math.sqrt(math.log(self.parent.visits + 1) / self.visits)
        prior_bonus = self.PRIOR_SCALE * (self.prior / (1.0 + self.visits))
        return exploit + explore + prior_bonus

    def expand(self):
        move = self.untried.pop()
        raw_prior = self.state.move_heuristic(move)
        norm_prior = math.tanh(raw_prior / 1200.0)
        child = Node(self.state.apply(*move), parent=self, move=move, prior=norm_prior)
        self.children.append(child)
        return child

    def rollout(self, max_depth=None):
        if max_depth is None:
            max_depth = self.ROLLOUT_DEPTH

        state = self.state
        start_color = state.turn

        for ply in range(max_depth):
            terminal = state.terminal_result_for(start_color)
            if terminal is not None:
                return terminal

            ordered = state.ordered_moves()
            if not ordered:
                terminal = state.terminal_result_for(start_color)
                return 0.0 if terminal is None else terminal

            width = 8 if ply < 4 else 5
            candidates = ordered[: min(width, len(ordered))]

            if len(candidates) == 1:
                move = candidates[0]
            elif random.random() < 0.82:
                move = candidates[0]
            else:
                move = random.choice(candidates)

            state = state.apply(*move)

        # Cutoff evaluation from rollout starter perspective.
        return math.tanh(state.evaluate(start_color) / 900.0)

    def backprop(self, result):
        self.visits += 1
        # Keep wins from parent viewpoint (sign-flipped convention).
        self.wins -= result

        if len(_TT_STATS) > 200000:
            _TT_STATS.clear()
        _TT_STATS[self.state.search_key()] = (self.wins, self.visits)

        if self.parent:
            self.parent.backprop(-result)


def _reuse_root_or_new(state):
    global _LAST_ROOT

    if _LAST_ROOT is None:
        return Node(state)

    target = state.search_key()

    if _LAST_ROOT.state.search_key() == target:
        _LAST_ROOT.parent = None
        return _LAST_ROOT

    for child in _LAST_ROOT.children:
        if child.state.search_key() == target:
            child.parent = None
            _LAST_ROOT = child
            return child

    # Try one extra ply to capture a full turn transition if available.
    for child in _LAST_ROOT.children:
        for grandchild in child.children:
            if grandchild.state.search_key() == target:
                grandchild.parent = None
                _LAST_ROOT = grandchild
                return grandchild

    return Node(state)