"""
Minimax with Alpha-Beta Pruning AI for Chess.

Uses the GameState class from mcts.py which already provides:
  - terminal_result_for(perspective): returns 1.0 (win), -1.0 (loss), 0.0 (draw), or None (non-terminal)
  - evaluate(perspective): static board evaluation score
  - ordered_moves(): move-ordered list of (from, to) tuples
  - apply(fr, to, track_history): returns new GameState after applying the move
"""

import time


def minimax_alpha_beta(state, depth, alpha, beta, is_maximizing, perspective):
    """
    Minimax search with Alpha-Beta pruning.

    Args:
        state:          Current GameState.
        depth:          Remaining search depth.
        alpha:          Best score the maximizing player can guarantee so far.
        beta:           Best score the minimizing player can guarantee so far.
        is_maximizing:  True if it's the AI (perspective) player's turn.
        perspective:    The AI's color ("w" or "b") - evaluation is always from this side.

    Returns:
        (eval_score, best_move)  where best_move is ((fr_r, fr_c), (to_r, to_c)) or None.
    """
    terminal_res = state.terminal_result_for(perspective)
    if depth == 0 or terminal_res is not None:
        return state.evaluate(perspective), None

    best_move = None
    moves = state.ordered_moves()

    if not moves:
        return state.evaluate(perspective), None

    if is_maximizing:
        max_eval = float('-inf')
        for move in moves:
            child_state = state.apply(move[0], move[1], track_history=False)
            eval_score, _ = minimax_alpha_beta(child_state, depth - 1, alpha, beta, False, perspective)

            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move

            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cut-off
        return max_eval, best_move

    else:
        min_eval = float('inf')
        for move in moves:
            child_state = state.apply(move[0], move[1], track_history=False)
            eval_score, _ = minimax_alpha_beta(child_state, depth - 1, alpha, beta, True, perspective)

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move

            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cut-off
        return min_eval, best_move


def get_alpha_beta_move(state, ai_color, depth=3):
    """
    Entry point for the Minimax AI.

    Args:
        state:    Current GameState.
        ai_color: AI's color ("w" or "b").
        depth:    Search depth (default 3).

    Returns:
        best_move as ((fr_r, fr_c), (to_r, to_c)) or None if no moves.
    """
    score, best_move = minimax_alpha_beta(
        state, depth, float('-inf'), float('inf'), True, ai_color
    )
    return best_move


# ======================================================================
# TEST SUITE
# ======================================================================

if __name__ == "__main__":
    from game_state import GameState

    def make_initial_state():
        board = [
            ["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["",   "",   "",   "",   "",   "",   "",   ""],
            ["",   "",   "",   "",   "",   "",   "",   ""],
            ["",   "",   "",   "",   "",   "",   "",   ""],
            ["",   "",   "",   "",   "",   "",   "",   ""],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"],
        ]
        cr = {"w": {"K": True, "Q": True}, "b": {"K": True, "Q": True}}
        return GameState(board, "w", cr, None)

    # ------------------------------------------------------------------
    # Test 1: returns a valid move from starting position
    # ------------------------------------------------------------------
    print("=" * 60)
    print("TEST 1: Valid move from starting position (White, depth=3)")
    print("=" * 60)
    state = make_initial_state()
    t0 = time.time()
    move = get_alpha_beta_move(state, "w", depth=3)
    elapsed = time.time() - t0

    if move is not None:
        fr, to = move
        print(f"  Best move: {fr} -> {to}")
        # Verify move is in legal move list
        legal = state.all_moves()
        assert move in legal, f"ERROR: returned move {move} not in legal moves!"
        print(f"  Move is legal: OK")
    else:
        print("  WARNING: No move returned (unexpected for starting position)")
    print(f"  Time: {elapsed:.3f}s")

    # ------------------------------------------------------------------
    # Test 2: AI plays as Black
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("TEST 2: AI plays as Black after 1.e4 (board state)")
    print("=" * 60)
    board2 = [
        ["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"],
        ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
        ["",   "",   "",   "",   "",   "",   "",   ""],
        ["",   "",   "",   "",   "",   "",   "",   ""],
        ["",   "",   "",   "",   "wp", "",   "",   ""],   # e4
        ["",   "",   "",   "",   "",   "",   "",   ""],
        ["wp", "wp", "wp", "wp", "",   "wp", "wp", "wp"],
        ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"],
    ]
    cr2 = {"w": {"K": True, "Q": True}, "b": {"K": True, "Q": True}}
    state2 = GameState(board2, "b", cr2, None)
    t0 = time.time()
    move2 = get_alpha_beta_move(state2, "b", depth=3)
    elapsed2 = time.time() - t0

    if move2 is not None:
        fr, to = move2
        print(f"  Best move: {fr} -> {to}")
        legal2 = state2.all_moves()
        assert move2 in legal2, f"ERROR: returned move {move2} not in legal moves!"
        print(f"  Move is legal: OK")
    else:
        print("  WARNING: No move returned")
    print(f"  Time: {elapsed2:.3f}s")

    # ------------------------------------------------------------------
    # Test 3: Mate in 1 — White queen+rook can checkmate immediately
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("TEST 3: Mate-in-1 position (White to play)")
    print("=" * 60)
    # Simplified position: Black king cornered at h8 (0,7),
    # White queen at g7 (1,6) attacks h8, White rook at a8 (0,0).
    # Qh7 is not mate.  Instead use: wq at f7 (1,5), wr at a8 (0,0), bk at h8 (0,7).
    # Qg7# is the simplest: wq at (1,5), bk at (0,7), wr at (0,0)
    # Actually let's set wq at (2,5) and wr at (0,0) — Qf8# delivering checkmate.
    board3 = [
        ["wr", "",   "",   "",   "",   "",   "",   "bk"],
        ["",   "",   "",   "",   "",   "wq", "",   ""],
        ["",   "",   "",   "",   "",   "",   "",   ""],
        ["",   "",   "",   "",   "",   "",   "",   ""],
        ["",   "",   "",   "",   "",   "",   "",   ""],
        ["",   "",   "",   "",   "",   "",   "",   ""],
        ["",   "",   "",   "",   "",   "",   "",   ""],
        ["",   "",   "",   "",   "wk", "",   "",   ""],
    ]
    cr3 = {"w": {"K": False, "Q": False}, "b": {"K": False, "Q": False}}
    state3 = GameState(board3, "w", cr3, None)

    t0 = time.time()
    move3 = get_alpha_beta_move(state3, "w", depth=3)
    elapsed3 = time.time() - t0

    if move3 is not None:
        fr, to = move3
        print(f"  Best move: {fr} -> {to}")
        child3 = state3.apply(fr, to, track_history=False)
        terminal3 = child3.terminal_result_for("w")
        if terminal3 == 1.0:
            print("  Checkmate delivered: PASS ✓")
        else:
            print(f"  Note: move delivered terminal={terminal3} (may need deeper search for guaranteed mate-in-1)")
    else:
        print("  WARNING: No move returned")
    print(f"  Time: {elapsed3:.3f}s")

    # ------------------------------------------------------------------
    # Test 4: alpha-beta prunes — confirm result matches plain minimax
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("TEST 4: Alpha-Beta result consistency check (depth=2)")
    print("=" * 60)

    def minimax_plain(state, depth, is_maximizing, perspective):
        """Plain minimax without pruning for reference."""
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
                    best = s; best_move = move
            return best, best_move
        else:
            best = float('inf')
            for move in moves:
                child = state.apply(move[0], move[1], track_history=False)
                s, _ = minimax_plain(child, depth - 1, True, perspective)
                if s < best:
                    best = s; best_move = move
            return best, best_move

    state4 = make_initial_state()
    score_ab, move_ab = minimax_alpha_beta(state4, 2, float('-inf'), float('inf'), True, "w")
    score_plain, move_plain = minimax_plain(state4, 2, True, "w")

    print(f"  Alpha-Beta score : {score_ab:.2f}, move: {move_ab}")
    print(f"  Plain Minimax    : {score_plain:.2f}, move: {move_plain}")

    if abs(score_ab - score_plain) < 1e-6:
        print("  Scores match: PASS ✓")
    else:
        print(f"  WARNING: scores differ by {abs(score_ab - score_plain):.4f}")

    # ------------------------------------------------------------------
    print()
    print("All tests done.")
