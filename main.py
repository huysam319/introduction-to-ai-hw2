import pygame

pygame.init()

# ================= CONFIG =================
WIDTH, HEIGHT = 640, 640
ROWS, COLS = 8, 8
SQ = WIDTH // COLS

WHITE = (240, 240, 240)
GREEN = (118, 150, 86)
HIGHLIGHT = (246, 246, 105)
RED = (220, 50, 50)
CASTLE_COLOR = (100, 180, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess")

# ================= LOAD =================
IMAGES = {}

def load_images():
    pieces = ["wp","wr","wn","wb","wq","wk",
              "bp","br","bn","bb","bq","bk"]
    for p in pieces:
        IMAGES[p] = pygame.transform.scale(
            pygame.image.load(f"assets/{p}.png"),
            (SQ, SQ)
        )

# ================= BOARD =================
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

# ================= STATE =================
castle_rights = {
    "w": {"K": True, "Q": True},
    "b": {"K": True, "Q": True}
}
en_passant_target = None

# ================= DRAW =================
def draw_board():
    for r in range(8):
        for c in range(8):
            color = WHITE if (r+c)%2==0 else GREEN
            pygame.draw.rect(screen, color, (c*SQ, r*SQ, SQ, SQ))

def draw_pieces(board):
    for r in range(8):
        for c in range(8):
            if board[r][c]!="":
                screen.blit(IMAGES[board[r][c]], (c*SQ, r*SQ))

def highlight_moves(moves, board, piece, from_pos):
    fr, fc = from_pos

    for r, c in moves:
        rect = (c*SQ, r*SQ, SQ, SQ)

        # 🔵 CASTLING (vua đi 2 ô ngang)
        if piece[1] == "k" and abs(c - fc) == 2:
            color = CASTLE_COLOR

        # 🔴 ăn quân
        elif board[r][c] != "" and board[r][c][0] != piece[0]:
            color = RED

        # 🟡 đi thường
        else:
            color = HIGHLIGHT

        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (0,0,0), rect, 1)

def draw_grid():
    for i in range(9):
        pygame.draw.line(screen, (0,0,0), (0,i*SQ),(WIDTH,i*SQ),1)
        pygame.draw.line(screen, (0,0,0), (i*SQ,0),(i*SQ,HEIGHT),1)

def draw_popup(text):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0,0,0))
    screen.blit(overlay,(0,0))

    font = pygame.font.SysFont(None, 60)
    label = font.render(text, True, (255,255,255))
    rect = label.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(label, rect)

def draw_promotion_menu(color):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill((0,0,0))
    screen.blit(overlay,(0,0))

    pieces = ["q","r","b","n"]
    for i,p in enumerate(pieces):
        x = WIDTH//2 - 2*SQ + i*SQ
        y = HEIGHT//2 - SQ//2
        rect = pygame.Rect(x,y,SQ,SQ)

        pygame.draw.rect(screen,(200,200,200),rect)
        pygame.draw.rect(screen,(0,0,0),rect,2)

        screen.blit(IMAGES[color+p],(x,y))

# ================= UTIL =================
def in_bounds(r,c): return 0<=r<8 and 0<=c<8
def is_enemy(a,b): return a[0]!=b[0]

# ================= CORE =================
def find_king(board,color):
    for r in range(8):
        for c in range(8):
            if board[r][c]==color+"k":
                return (r,c)

def is_in_check(board,color):
    king=find_king(board,color)
    enemy="b" if color=="w" else "w"
    for r in range(8):
        for c in range(8):
            if board[r][c]!="" and board[r][c][0]==enemy:
                if king in get_moves(board,r,c,False):
                    return True
    return False

def simulate(board,fr,to):
    new=[row[:] for row in board]
    new[to[0]][to[1]]=new[fr[0]][fr[1]]
    new[fr[0]][fr[1]]=""
    return new

def get_valid_moves(board,r,c):
    piece=board[r][c]
    if piece=="": return []
    color=piece[0]
    valid=[]
    for move in get_moves(board,r,c):
        if not is_in_check(simulate(board,(r,c),move),color):
            valid.append(move)
    return valid

def has_valid_moves(board,color):
    for r in range(8):
        for c in range(8):
            if board[r][c]!="" and board[r][c][0]==color:
                if get_valid_moves(board,r,c):
                    return True
    return False

def check_game_over(board,turn):
    if is_in_check(board,turn):
        if not has_valid_moves(board,turn):
            return "checkmate"
    else:
        if not has_valid_moves(board,turn):
            return "stalemate"
    return None

def update_castle_rights_on_capture(board,r,c):
    piece=board[r][c]
    if piece=="wr":
        if r==7 and c==0: castle_rights["w"]["Q"]=False
        elif r==7 and c==7: castle_rights["w"]["K"]=False
    elif piece=="br":
        if r==0 and c==0: castle_rights["b"]["Q"]=False
        elif r==0 and c==7: castle_rights["b"]["K"]=False

def check_promotion(board,r,c):
    return (board[r][c]=="wp" and r==0) or (board[r][c]=="bp" and r==7)

# ================= MOVE =================
def get_moves(board,r,c,include_castle=True):
    global en_passant_target

    piece=board[r][c]
    if piece=="": return []
    color,p=piece
    moves=[]

    if p=="p":
        dir=-1 if color=="w" else 1

        if in_bounds(r+dir,c) and board[r+dir][c]=="":
            moves.append((r+dir,c))
            if (r==6 and color=="w") or (r==1 and color=="b"):
                if board[r+2*dir][c]=="":
                    moves.append((r+2*dir,c))

        for dc in [-1,1]:
            nr,nc=r+dir,c+dc
            if in_bounds(nr,nc):
                if board[nr][nc]!="" and is_enemy(piece,board[nr][nc]):
                    moves.append((nr,nc))

        if en_passant_target:
            if (r+dir,c-1)==en_passant_target or (r+dir,c+1)==en_passant_target:
                moves.append(en_passant_target)

    if p in ["r","b","q"]:
        dirs=[]
        if p in ["r","q"]:
            dirs+=[(1,0),(-1,0),(0,1),(0,-1)]
        if p in ["b","q"]:
            dirs+=[(1,1),(1,-1),(-1,1),(-1,-1)]

        for dr,dc in dirs:
            nr,nc=r,c
            while True:
                nr+=dr; nc+=dc
                if not in_bounds(nr,nc): break
                if board[nr][nc]=="":
                    moves.append((nr,nc))
                else:
                    if is_enemy(piece,board[nr][nc]):
                        moves.append((nr,nc))
                    break

    if p=="n":
        for dr,dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            nr,nc=r+dr,c+dc
            if in_bounds(nr,nc) and (board[nr][nc]=="" or is_enemy(piece,board[nr][nc])):
                moves.append((nr,nc))

    if p=="k":
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr or dc:
                    nr,nc=r+dr,c+dc
                    if in_bounds(nr,nc) and (board[nr][nc]=="" or is_enemy(piece,board[nr][nc])):
                        moves.append((nr,nc))

        if include_castle and not is_in_check(board,color):
            row = 7 if color=="w" else 0

            if castle_rights[color]["K"]:
                if board[row][5]=="" and board[row][6]=="":
                    if not is_in_check(simulate(board,(r,c),(row,5)),color):
                        if not is_in_check(simulate(board,(r,c),(row,6)),color):
                            moves.append((row,6))

            if castle_rights[color]["Q"]:
                if board[row][1]=="" and board[row][2]=="" and board[row][3]=="":
                    if not is_in_check(simulate(board,(r,c),(row,3)),color):
                        if not is_in_check(simulate(board,(r,c),(row,2)),color):
                            moves.append((row,2))

    return moves

# ================= MAIN =================
def main():
    global en_passant_target

    load_images()
    board=create_board()

    selected=None
    valid=[]
    turn="w"

    promotion=False
    promotion_pos=None

    game_over=None

    running=True
    while running:
        draw_board()
        draw_grid()

        if selected:
            highlight_moves(valid, board, board[selected[0]][selected[1]], selected)

        draw_pieces(board)

        if promotion:
            color=board[promotion_pos[0]][promotion_pos[1]][0]
            draw_promotion_menu(color)

        if game_over:
            draw_popup(game_over)

        pygame.display.update()

        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                running=False

            if e.type==pygame.MOUSEBUTTONDOWN:

                if game_over:
                    continue

                # promotion click
                if promotion:
                    mx,my=pygame.mouse.get_pos()
                    for i,p in enumerate(["q","r","b","n"]):
                        x=WIDTH//2-2*SQ+i*SQ
                        y=HEIGHT//2-SQ//2
                        rect=pygame.Rect(x,y,SQ,SQ)

                        if rect.collidepoint(mx,my):
                            r,c=promotion_pos
                            color=board[r][c][0]
                            board[r][c]=color+p

                            promotion=False
                            promotion_pos=None

                            turn="b" if turn=="w" else "w"
                            game_over = check_game_over(board, turn)

                    continue

                r,c=pygame.mouse.get_pos()[1]//SQ, pygame.mouse.get_pos()[0]//SQ

                if selected:
                    if (r,c) in valid:
                        pr,pc=selected
                        piece=board[pr][pc]

                        if board[r][c]!="":
                            update_castle_rights_on_capture(board,r,c)

                        if piece[1]=="p" and (r,c)==en_passant_target:
                            board[pr][c]=""

                        board[r][c]=piece
                        board[pr][pc]=""

                        # update castle rights
                        if piece=="wk":
                            castle_rights["w"]["K"]=False
                            castle_rights["w"]["Q"]=False
                        elif piece=="bk":
                            castle_rights["b"]["K"]=False
                            castle_rights["b"]["Q"]=False
                        elif piece=="wr":
                            if pr==7 and pc==0: castle_rights["w"]["Q"]=False
                            elif pr==7 and pc==7: castle_rights["w"]["K"]=False
                        elif piece=="br":
                            if pr==0 and pc==0: castle_rights["b"]["Q"]=False
                            elif pr==0 and pc==7: castle_rights["b"]["K"]=False

                        # castling rook move
                        if piece[1]=="k":
                            if c==6:
                                board[r][5]=board[r][7]
                                board[r][7]=""
                            elif c==2:
                                board[r][3]=board[r][0]
                                board[r][0]=""

                        # en passant
                        if piece[1]=="p" and abs(r-pr)==2:
                            en_passant_target=((r+pr)//2,c)
                        else:
                            en_passant_target=None

                        if check_promotion(board,r,c):
                            promotion=True
                            promotion_pos=(r,c)
                        else:
                            turn="b" if turn=="w" else "w"
                            game_over = check_game_over(board, turn)

                        selected=None
                        valid=[]
                    else:
                        selected=None
                        valid=[]
                else:
                    if board[r][c]!="" and board[r][c][0]==turn:
                        selected=(r,c)
                        valid=get_valid_moves(board,r,c)

    pygame.quit()

if __name__=="__main__":
    main()