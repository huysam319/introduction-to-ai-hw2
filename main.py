import pygame
import threading
from mcts import GameState, mcts, reset_search_state

pygame.init()

#  CONFIG 
WIDTH, HEIGHT = 640, 640
SQ = WIDTH // 8

WHITE        = (240, 240, 240)
GREEN        = (118, 150, 86)
HIGHLIGHT    = (246, 246, 105)
RED          = (220, 50, 50)
CASTLE_COLOR = (100, 180, 255)
AI_MOVE_CLR  = (255, 165, 0)   # màu cam: hiển thị nước AI vừa đi

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess – MCTS AI (bạn = Trắng, AI = Đen)")


def get_ui_font(size, bold=False):
    for name in ["Segoe UI", "Tahoma", "Arial", "DejaVu Sans", "Noto Sans"]:
        font_path = pygame.font.match_font(name, bold=bold)
        if font_path:
            return pygame.font.Font(font_path, size)
    return pygame.font.SysFont(None, size, bold=bold)

#  LOAD 
IMAGES = {}

def load_images():
    pieces = ["wp","wr","wn","wb","wq","wk",
              "bp","br","bn","bb","bq","bk"]
    for p in pieces:
        IMAGES[p] = pygame.transform.scale(
            pygame.image.load(f"assets/{p}.png"),
            (SQ, SQ)
        )

#  BOARD 
def create_board():
    return [
        ["br","bn","bb","bq","bk","bb","bn","br"],
        ["bp","bp","bp","bp","bp","bp","bp","bp"],
        ["","","","","","","",""],
        ["","","","","","","",""],
        ["","","","","","","",""],
        ["","","","","","","",""],
        ["wp","wp","wp","wp","wp","wp","wp","wp"],
        ["wr","wn","wb","wq","wk","wb","wn","wr"],
    ]

#  STATE 
castle_rights     = {"w": {"K": True, "Q": True}, "b": {"K": True, "Q": True}}
en_passant_target = None
halfmove_clock    = 0
position_history  = []


def compose_position_key(board, turn, cr, ep):
    board_key = tuple(tuple(row) for row in board)
    cr_key = (cr["w"]["K"], cr["w"]["Q"], cr["b"]["K"], cr["b"]["Q"])
    return board_key, turn, cr_key, ep


def record_position(board, turn, cr, ep):
    position_history.append(compose_position_key(board, turn, cr, ep))

#  AI CONFIG 
AI_COLOR      = "b"          # AI chơi quân Đen
AI_TIME_LIMIT = 2.0          # giây suy nghĩ mỗi nước

_ai_move   = [None]          # nước AI đã tính xong
_ai_busy   = [False]         # đang tính?
_ai_last   = [None]          # (from, to) nước AI vừa đi – để vẽ highlight
_ai_job_id = [0]             # id công việc AI hiện tại (chống kết quả thread cũ)

def _ai_worker(state: GameState, job_id: int):
    """Chạy MCTS trong thread riêng."""
    move = mcts(state, AI_COLOR, time_limit=AI_TIME_LIMIT)
    if job_id != _ai_job_id[0]:
        return
    _ai_move[0]  = move
    _ai_busy[0]  = False

def trigger_ai(board, turn, cr, ep):
    """Khởi động thread tính nước AI (nếu chưa bận)."""
    if _ai_busy[0]:
        return
    _ai_job_id[0] += 1
    job_id = _ai_job_id[0]
    _ai_busy[0] = True
    _ai_move[0] = None
    state = GameState(
        board,
        turn,
        cr,
        ep,
        halfmove_clock=halfmove_clock,
        history=tuple(position_history),
    )
    t = threading.Thread(target=_ai_worker, args=(state, job_id), daemon=True)
    t.start()

#  DRAW 
def draw_board():
    for r in range(8):
        for c in range(8):
            color = WHITE if (r + c) % 2 == 0 else GREEN
            pygame.draw.rect(screen, color, (c*SQ, r*SQ, SQ, SQ))

def draw_pieces(board):
    for r in range(8):
        for c in range(8):
            if board[r][c]:
                screen.blit(IMAGES[board[r][c]], (c*SQ, r*SQ))

def highlight_moves(moves, board, piece, from_pos):
    fr, fc = from_pos
    for r, c in moves:
        rect = (c*SQ, r*SQ, SQ, SQ)
        if piece[1] == "k" and abs(c - fc) == 2:
            color = CASTLE_COLOR
        elif board[r][c] and board[r][c][0] != piece[0]:
            color = RED
        else:
            color = HIGHLIGHT
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1)

def highlight_ai_last_move():
    """Đánh dấu ô nguồn + đích của nước AI vừa đi."""
    if _ai_last[0]:
        (fr, fc), (tr, tc) = _ai_last[0]
        for r, c in [(fr, fc), (tr, tc)]:
            rect = (c*SQ, r*SQ, SQ, SQ)
            pygame.draw.rect(screen, AI_MOVE_CLR, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 2)

def highlight_king_in_check(board, turn):
    if is_in_check(board, turn):
        pos = find_king(board, turn)
        if pos:
            r, c = pos
            pygame.draw.rect(screen, (255, 0, 0), (c*SQ, r*SQ, SQ, SQ), 4)

def draw_grid():
    for i in range(9):
        pygame.draw.line(screen, (0, 0, 0), (0, i*SQ), (WIDTH, i*SQ), 1)
        pygame.draw.line(screen, (0, 0, 0), (i*SQ, 0), (i*SQ, HEIGHT), 1)

def draw_thinking_indicator():
    """Hiển thị 'AI đang suy nghĩ…' trong khi MCTS chạy."""
    font  = get_ui_font(34, bold=True)
    label = font.render("AI đang suy nghĩ...", True, (255, 255, 50))
    bg    = pygame.Surface((label.get_width() + 16, label.get_height() + 10))
    bg.set_alpha(200)
    bg.fill((30, 30, 30))
    x = WIDTH // 2 - bg.get_width() // 2
    y = HEIGHT - bg.get_height() - 8
    screen.blit(bg, (x, y))
    screen.blit(label, (x + 8, y + 5))

def draw_popup(text):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    font  = get_ui_font(60, bold=True)
    label = font.render(text, True, (255, 255, 255))
    rect  = label.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
    screen.blit(label, rect)

    btn_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 200, 60)
    pygame.draw.rect(screen, (200, 200, 200), btn_rect)
    pygame.draw.rect(screen, (0, 0, 0), btn_rect, 2)

    btn_font = get_ui_font(40, bold=True)
    btn_text = btn_font.render("Chơi lại", True, (0, 0, 0))
    btn_text_rect = btn_text.get_rect(center=btn_rect.center)
    screen.blit(btn_text, btn_text_rect)
    return btn_rect

def draw_promotion_menu(color):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    for i, p in enumerate(["q", "r", "b", "n"]):
        x = WIDTH//2 - 2*SQ + i*SQ
        y = HEIGHT//2 - SQ//2
        rect = pygame.Rect(x, y, SQ, SQ)
        pygame.draw.rect(screen, (200, 200, 200), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)
        screen.blit(IMAGES[color + p], (x, y))

#  UTIL 
def in_bounds(r, c): return 0 <= r < 8 and 0 <= c < 8
def is_enemy(a, b):  return a[0] != b[0]

#  CORE 
def find_king(board, color):
    for r in range(8):
        for c in range(8):
            if board[r][c] == color + "k":
                return (r, c)

def is_in_check(board, color):
    king  = find_king(board, color)
    enemy = "b" if color == "w" else "w"
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0] == enemy:
                if king in get_moves(board, r, c, False):
                    return True
    return False

def simulate(board, fr, to):
    new = [row[:] for row in board]
    new[to[0]][to[1]] = new[fr[0]][fr[1]]
    new[fr[0]][fr[1]] = ""
    return new

def get_valid_moves(board, r, c):
    piece = board[r][c]
    if piece == "": return []
    color = piece[0]
    return [m for m in get_moves(board, r, c)
            if not is_in_check(simulate(board, (r, c), m), color)]

def has_valid_moves(board, color):
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0] == color:
                if get_valid_moves(board, r, c):
                    return True
    return False

def check_game_over(board, turn):
    if is_in_check(board, turn):
        if not has_valid_moves(board, turn):
            return "Chiếu hết! " + ("Bạn thắng!" if turn == AI_COLOR else "AI thắng!")
    else:
        if not has_valid_moves(board, turn):
            return "Bế tắc – Hòa!"

    state = GameState(
        board,
        turn,
        castle_rights,
        en_passant_target,
        halfmove_clock=halfmove_clock,
        history=tuple(position_history),
    )
    if state.is_draw():
        if state.halfmove_clock >= 100:
            return "Hòa theo luật 50 nước!"
        if state.repetition_count() >= 3:
            return "Hòa do lặp lại vị trí 3 lần!"
        return "Hòa do không đủ vật liệu chiếu hết!"

    return None

def update_castle_rights_on_capture(board, r, c):
    piece = board[r][c]
    if piece == "wr":
        if (r, c) == (7, 0): castle_rights["w"]["Q"] = False
        if (r, c) == (7, 7): castle_rights["w"]["K"] = False
    if piece == "br":
        if (r, c) == (0, 0): castle_rights["b"]["Q"] = False
        if (r, c) == (0, 7): castle_rights["b"]["K"] = False

def check_promotion(board, r, c):
    return (board[r][c] == "wp" and r == 0) or (board[r][c] == "bp" and r == 7)

#  MOVE GEN 
def get_moves(board, r, c, include_castle=True):
    global en_passant_target

    piece = board[r][c]
    if piece == "": return []
    color, p = piece[0], piece[1]
    moves = []

    if p == "p":
        dir = -1 if color == "w" else 1
        if in_bounds(r+dir, c) and board[r+dir][c] == "":
            moves.append((r+dir, c))
            if (r == 6 and color == "w") or (r == 1 and color == "b"):
                if board[r+2*dir][c] == "":
                    moves.append((r+2*dir, c))
        for dc in [-1, 1]:
            nr, nc = r+dir, c+dc
            if in_bounds(nr, nc) and board[nr][nc] and is_enemy(piece, board[nr][nc]):
                moves.append((nr, nc))
        if en_passant_target:
            if (r+dir, c-1) == en_passant_target or (r+dir, c+1) == en_passant_target:
                moves.append(en_passant_target)

    if p in ["r", "b", "q"]:
        dirs = []
        if p in ["r", "q"]: dirs += [(1,0),(-1,0),(0,1),(0,-1)]
        if p in ["b", "q"]: dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr, dc in dirs:
            nr, nc = r, c
            while True:
                nr += dr; nc += dc
                if not in_bounds(nr, nc): break
                if board[nr][nc] == "":
                    moves.append((nr, nc))
                else:
                    if is_enemy(piece, board[nr][nc]):
                        moves.append((nr, nc))
                    break

    if p == "n":
        for dr, dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            nr, nc = r+dr, c+dc
            if in_bounds(nr, nc) and (board[nr][nc] == "" or is_enemy(piece, board[nr][nc])):
                moves.append((nr, nc))

    if p == "k":
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr or dc:
                    nr, nc = r+dr, c+dc
                    if in_bounds(nr, nc) and (board[nr][nc] == "" or is_enemy(piece, board[nr][nc])):
                        moves.append((nr, nc))

        if include_castle and not is_in_check(board, color):
            row = 7 if color == "w" else 0
            if not (r == row and c == 4):
                return moves
            if castle_rights[color]["K"] and board[row][7] == color+"r":
                if board[row][5] == "" and board[row][6] == "":
                    if not is_in_check(simulate(board, (r,c), (row,5)), color):
                        if not is_in_check(simulate(board, (r,c), (row,6)), color):
                            moves.append((row, 6))
            if castle_rights[color]["Q"] and board[row][0] == color+"r":
                if board[row][1] == "" and board[row][2] == "" and board[row][3] == "":
                    if not is_in_check(simulate(board, (r,c), (row,3)), color):
                        if not is_in_check(simulate(board, (r,c), (row,2)), color):
                            moves.append((row, 2))

    return moves

#  APPLY MOVE HELPER 
def apply_move(board, fr, to):
    """
    Áp dụng nước đi (fr → to) lên board (in-place).
    Xử lý: en passant, nhập thành, cập nhật quyền nhập thành, phong cấp thành Hậu (cho AI).
    Trả về: (cần_phong_cấp, en_passant_target_mới)
    """
    global castle_rights, en_passant_target, halfmove_clock

    pr, pc = fr
    r,  c  = to
    piece  = board[pr][pc]
    captured_any = False

    if board[r][c]:
        captured_any = True
        update_castle_rights_on_capture(board, r, c)

    # En passant capture
    if piece[1] == "p" and (r, c) == en_passant_target:
        captured_any = True
        board[pr][c] = ""

    board[r][c]   = piece
    board[pr][pc] = ""

    # Nhập thành
    if piece[1] == "k":
        castle_rights[piece[0]] = {"K": False, "Q": False}
        if (pr, pc) == (7, 4) and piece[0] == "w" and c == 6:
            board[r][5] = board[r][7]
            board[r][7] = ""
        elif (pr, pc) == (7, 4) and piece[0] == "w" and c == 2:
            board[r][3] = board[r][0]
            board[r][0] = ""
        elif (pr, pc) == (0, 4) and piece[0] == "b" and c == 6:
            board[r][5] = board[r][7]
            board[r][7] = ""
        elif (pr, pc) == (0, 4) and piece[0] == "b" and c == 2:
            board[r][3] = board[r][0]
            board[r][0] = ""

    if piece == "wr":
        if (pr, pc) == (7, 0): castle_rights["w"]["Q"] = False
        if (pr, pc) == (7, 7): castle_rights["w"]["K"] = False
    if piece == "br":
        if (pr, pc) == (0, 0): castle_rights["b"]["Q"] = False
        if (pr, pc) == (0, 7): castle_rights["b"]["K"] = False

    # En passant target mới
    if piece[1] == "p" and abs(r - pr) == 2:
        en_passant_target = ((r + pr) // 2, c)
    else:
        en_passant_target = None

    if piece[1] == "p" or captured_any:
        halfmove_clock = 0
    else:
        halfmove_clock += 1

    needs_promotion = check_promotion(board, r, c)
    return needs_promotion

#  RESET 
def reset_game():
    global castle_rights, en_passant_target, halfmove_clock, position_history
    board             = create_board()
    castle_rights     = {"w": {"K": True, "Q": True}, "b": {"K": True, "Q": True}}
    en_passant_target = None
    halfmove_clock    = 0
    position_history  = []
    _ai_job_id[0]    += 1
    record_position(board, "w", castle_rights, en_passant_target)
    reset_search_state()
    _ai_move[0]       = None
    _ai_busy[0]       = False
    _ai_last[0]       = None
    return board, "w", None, [], False, None, None

#  MAIN 
def main():
    global en_passant_target

    load_images()
    board, turn, selected, valid, promotion, promotion_pos, game_over = reset_game()

    running = True
    while running:
        #  Vẽ 
        draw_board()
        highlight_ai_last_move()     # highlight nước AI vừa đi (màu cam)
        draw_grid()

        if selected:
            highlight_moves(valid, board, board[selected[0]][selected[1]], selected)

        draw_pieces(board)
        highlight_king_in_check(board, turn)

        if promotion:
            draw_promotion_menu(board[promotion_pos[0]][promotion_pos[1]][0])

        btn_rect = None
        if game_over:
            btn_rect = draw_popup(game_over)
        elif _ai_busy[0]:
            draw_thinking_indicator()

        pygame.display.update()

        #  AI áp dụng nước đi khi tính xong 
        if (not game_over and not promotion
                and turn == AI_COLOR
                and not _ai_busy[0]
                and _ai_move[0] is not None):

            ai_fr, ai_to = _ai_move[0]
            _ai_move[0]  = None

            needs_promo = apply_move(board, ai_fr, ai_to)
            _ai_last[0] = (ai_fr, ai_to)   # lưu để vẽ highlight

            if needs_promo:
                # AI tự phong Hậu
                r, c = ai_to
                board[r][c] = AI_COLOR + "q"

            turn      = "w" if turn == "b" else "b"
            record_position(board, turn, castle_rights, en_passant_target)
            game_over = check_game_over(board, turn)

        #  Sự kiện 
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                # Nút "Chơi lại"
                if game_over:
                    if btn_rect and btn_rect.collidepoint(mx, my):
                        board, turn, selected, valid, promotion, promotion_pos, game_over = reset_game()
                    continue

                # Đang phong cấp (người)
                if promotion:
                    for i, p in enumerate(["q", "r", "b", "n"]):
                        x = WIDTH//2 - 2*SQ + i*SQ
                        y = HEIGHT//2 - SQ//2
                        if pygame.Rect(x, y, SQ, SQ).collidepoint(mx, my):
                            r, c = promotion_pos
                            board[r][c] = board[r][c][0] + p
                            promotion   = False
                            turn        = "b" if turn == "w" else "w"
                            record_position(board, turn, castle_rights, en_passant_target)
                            game_over   = check_game_over(board, turn)
                            # Kích hoạt AI nếu đến lượt
                            if not game_over and turn == AI_COLOR:
                                trigger_ai(board, turn, castle_rights, en_passant_target)
                    continue

                # Đang chờ AI → bỏ qua click của người
                if turn == AI_COLOR:
                    continue

                r, c = my // SQ, mx // SQ

                if selected:
                    if (r, c) in valid:
                        needs_promo = apply_move(board, selected, (r, c))
                        _ai_last[0] = None  # xóa highlight nước AI cũ

                        if needs_promo:
                            promotion     = True
                            promotion_pos = (r, c)
                        else:
                            turn      = "b" if turn == "w" else "w"
                            record_position(board, turn, castle_rights, en_passant_target)
                            game_over = check_game_over(board, turn)
                            # Kích hoạt AI
                            if not game_over and turn == AI_COLOR:
                                trigger_ai(board, turn, castle_rights, en_passant_target)

                        selected = None
                        valid    = []
                    else:
                        # Chọn quân khác (hoặc bỏ chọn)
                        if board[r][c] and board[r][c][0] == turn:
                            selected = (r, c)
                            valid    = get_valid_moves(board, r, c)
                        else:
                            selected = None
                            valid    = []
                else:
                    if board[r][c] and board[r][c][0] == turn:
                        selected = (r, c)
                        valid    = get_valid_moves(board, r, c)

    pygame.quit()


if __name__ == "__main__":
    main()