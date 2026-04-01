"""Simple test runner for minimax - ASCII only, no unicode."""
import time
from mcts import GameState
from minimax import minimax_alpha_beta, get_alpha_beta_move


def make_initial_state():
    board = [
        ["br","bn","bb","bq","bk","bb","bn","br"],
        ["bp","bp","bp","bp","bp","bp","bp","bp"],
        ["","","","","","","",""],
        ["","","","","","","",""],
        ["","","","","","","",""],
        ["","","","","","","",""],
        ["wp","wp","wp","wp","wp","wp","wp","wp"],
        ["wr","wn","wb","wq","wk","wb","wn","wr"],
    ]
    cr = {"w": {"K": True, "Q": True}, "b": {"K": True, "Q": True}}
    return GameState(board, "w", cr, None)


print("="*60)
print("TEST 1: Valid move from starting position (White, depth=3)")
print("="*60)
state = make_initial_state()
t0 = time.time()
move = get_alpha_beta_move(state, "w", depth=3)
elapsed = time.time() - t0

if move is not None:
    fr, to = move
    print("  Best move: {} -> {}".format(fr, to))
    legal = state.all_moves()
    assert move in legal, "ERROR: returned move {} not in legal moves!".format(move)
    print("  Move is legal: OK")
else:
    print("  WARNING: No move returned")
print("  Time: {:.3f}s".format(elapsed))


print()
print("="*60)
print("TEST 2: AI plays as Black after 1.e4")
print("="*60)
board2 = [
    ["br","bn","bb","bq","bk","bb","bn","br"],
    ["bp","bp","bp","bp","bp","bp","bp","bp"],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["","","","","wp","","",""],
    ["","","","","","","",""],
    ["wp","wp","wp","wp","","wp","wp","wp"],
    ["wr","wn","wb","wq","wk","wb","wn","wr"],
]
cr2 = {"w": {"K": True, "Q": True}, "b": {"K": True, "Q": True}}
state2 = GameState(board2, "b", cr2, None)
t0 = time.time()
move2 = get_alpha_beta_move(state2, "b", depth=3)
elapsed2 = time.time() - t0

if move2 is not None:
    fr, to = move2
    print("  Best move: {} -> {}".format(fr, to))
    legal2 = state2.all_moves()
    assert move2 in legal2, "ERROR: returned move {} not in legal moves!".format(move2)
    print("  Move is legal: OK")
else:
    print("  WARNING: No move returned")
print("  Time: {:.3f}s".format(elapsed2))


print()
print("="*60)
print("TEST 3: Mate-in-1 position")
print("   wq at (1,5), wr at (0,0), bk at (0,7), wk at (7,4)")
print("="*60)
board3 = [
    ["wr","","","","","","","bk"],
    ["","","","","","wq","",""],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["","","","","","","",""],
    ["","","","","wk","","",""],
]
cr3 = {"w": {"K": False, "Q": False}, "b": {"K": False, "Q": False}}
state3 = GameState(board3, "w", cr3, None)

t0 = time.time()
move3 = get_alpha_beta_move(state3, "w", depth=3)
elapsed3 = time.time() - t0

if move3 is not None:
    fr, to = move3
    print("  Best move: {} -> {}".format(fr, to))
    child3 = state3.apply(fr, to, track_history=False)
    terminal3 = child3.terminal_result_for("w")
    if terminal3 == 1.0:
        print("  Checkmate delivered! PASS")
    else:
        print("  Note: move delivered terminal={} (not immediate checkmate)".format(terminal3))
else:
    print("  WARNING: No move returned")
print("  Time: {:.3f}s".format(elapsed3))


print()
print("="*60)
print("TEST 4: Alpha-Beta result consistency vs plain minimax (depth=2)")
print("="*60)


def minimax_plain(state, depth, is_maximizing, perspective):
    terminal_res = state.terminal_result_for(perspective)
    if depth == 0 or terminal_res is not None:
        return state.evaluate(perspective), None
    moves = state.ordered_moves()
    if not moves:
        return state.evaluate(perspective), None
    best_move = None
    if is_maximizing:
        best = float('-inf')
        for move in moves:
            child = state.apply(move[0], move[1], track_history=False)
            s, _ = minimax_plain(child, depth - 1, False, perspective)
            if s > best:
                best = s
                best_move = move
        return best, best_move
    else:
        best = float('inf')
        for move in moves:
            child = state.apply(move[0], move[1], track_history=False)
            s, _ = minimax_plain(child, depth - 1, True, perspective)
            if s < best:
                best = s
                best_move = move
        return best, best_move


state4 = make_initial_state()
t0 = time.time()
score_ab, move_ab = minimax_alpha_beta(state4, 2, float('-inf'), float('inf'), True, "w")
t_ab = time.time() - t0

t0 = time.time()
score_plain, move_plain = minimax_plain(state4, 2, True, "w")
t_plain = time.time() - t0

print("  Alpha-Beta:    score={:.2f}, move={}, time={:.3f}s".format(score_ab, move_ab, t_ab))
print("  Plain Minimax: score={:.2f}, move={}, time={:.3f}s".format(score_plain, move_plain, t_plain))
if abs(score_ab - score_plain) < 1e-6:
    print("  Scores match: PASS")
else:
    print("  WARNING: scores differ by {:.4f}".format(abs(score_ab - score_plain)))

speedup = t_plain / t_ab if t_ab > 0 else float('inf')
print("  Alpha-Beta speedup: {:.1f}x faster than plain minimax".format(speedup))

print()
print("All tests completed.")
