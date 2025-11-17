import pygame

pygame.init()

# 윈도우 설정 ---
screen_width = 900
screen_height = 700
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("오목")

# 색깔
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BROWN = (139, 69, 19) # (이제 배경 이미지에 가려져 거의 쓰이지 않음)
GRAY = (150, 150, 150) # 버튼 색
RED = (255, 0, 0) # 승자 텍스트 색

# 게임판 설정
board_size = 14  # 15x15 
grid_size = 40   # 한 칸 크기
start_pos = 40   # 여백

# --- [신규] 이미지 로드 ---
try:
    # 1. 배경 이미지 로드 및 크기 조절
    board_image = pygame.image.load("C:/Users/user/OneDrive/바탕 화면/board.png")
    board_image = pygame.transform.scale(board_image, (screen_width, screen_height))

    # 2. 바둑돌 이미지 로드 (돌 크기는 36x36으로 가정)
    stone_size = 36 
    black_stone_image = pygame.image.load("C:/Users/user/OneDrive/바탕 화면/black.jpg")
    black_stone_image = pygame.transform.scale(black_stone_image, (stone_size, stone_size))
    
    white_stone_image = pygame.image.load("C:/Users/user/OneDrive/바탕 화면/white.jpg")
    white_stone_image = pygame.transform.scale(white_stone_image, (stone_size, stone_size))
    
except pygame.error as e:
    print(f"이미지 로드 오류: {e}")
    running = False # 이미지가 없으면 실행 중단
    
# 돌을 그릴 때 중심 좌표를 기준으로 top-left를 계산하기 위한 값
stone_radius = stone_size // 2


# 게임 데이터
board = [[0] * 15 for _ in range(15)] 
turn = 1 
winner = 0 

# 게임 상태 관리
game_state = "START" # "START", "PLAY", "OVER"
move_history = [] # (r, c, player)를 순서대로 저장
win_reason = "" # 승리 사유 저장

# 금수 확인 상태
awaiting_forbidden_confirmation = False
forbidden_move_to_confirm = None

# 폰트 설정
try:
    # 윈도우 기본 폰트 '맑은 고딕' 사용
    font = pygame.font.SysFont("malgungothic", 35) 
    large_font = pygame.font.SysFont("malgungothic", 60)
    move_num_font = pygame.font.SysFont("malgungothic", 18) 
except Exception as e:
    print(f"폰트 로드 실패: {e}. 기본 폰트를 사용합니다 (한글이 깨질 수 있습니다).")
    font = pygame.font.Font(None, 35)
    large_font = pygame.font.Font(None, 60)
    move_num_font = pygame.font.Font(None, 18)

# 버튼 설정
start_button_rect = pygame.Rect(300, 300, 300, 100) 
quit_button_start_rect = pygame.Rect(300, 420, 300, 80) 

undo_button_rect = pygame.Rect(670, 200, 180, 60) 
replay_button_rect = pygame.Rect(670, 300, 180, 60) 
quit_button_rect = pygame.Rect(670, 400, 180, 60) 


# --- 2. 함수 정의 ---

# --- [수정] draw_board 함수 ---
def draw_board(): # 바둑판 그리기
    # screen.fill(BROWN) # [수정] 갈색으로 채우는 대신 이미지 blit
    screen.blit(board_image, (0, 0)) # 배경 이미지를 (0, 0) 위치에 그림
    
    # 격자 그리기 (배경 이미지에 격자가 없다면 이 코드가 필요함)
    for i in range(board_size + 1): 
        pygame.draw.line(screen, BLACK, (start_pos, start_pos + i * grid_size), (start_pos + board_size * grid_size, start_pos + i * grid_size), 1)
        pygame.draw.line(screen, BLACK, (start_pos + i * grid_size, start_pos), (start_pos + i * grid_size, start_pos + board_size * grid_size), 1)

    # 화점 그리기
    dot_positions = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)]
    for (r, c) in dot_positions:
        pos_x = start_pos + c * grid_size
        pos_y = start_pos + r * grid_size
        pygame.draw.circle(screen, BLACK, (pos_x, pos_y), 5)

# --- [수정] draw_stones 함수 ---
def draw_stones(): # 바둑돌 그리기
    for r in range(15):
        for c in range(15):
            # 중심 좌표 계산
            center_x = start_pos + c * grid_size
            center_y = start_pos + r * grid_size
            
            # blit는 top-left 좌표를 사용하므로, 중심 좌표에서 반지름만큼 빼줌
            blit_x = center_x - stone_radius
            blit_y = center_y - stone_radius
            
            if board[r][c] == 1: # 흑돌
                # [수정] 원을 그리는 대신 이미지 blit
                screen.blit(black_stone_image, (blit_x, blit_y))
            elif board[r][c] == 2: # 백돌
                # [수정] 원을 그리는 대신 이미지 blit
                screen.blit(white_stone_image, (blit_x, blit_y))

def draw_move_numbers():    # 게임 종료 시 돌 위에 순서 표기. (흑/백 따로)
    black_count = 0
    white_count = 0
    
    for (r, c, player) in move_history:
        move_num = ""
        if player == 1:
            black_count += 1
            move_num = str(black_count)
            text_color = WHITE
        else: # player == 2
            white_count += 1
            move_num = str(white_count)
            text_color = BLACK
            
        text_surf = move_num_font.render(move_num, True, text_color)
        text_rect = text_surf.get_rect(center=(start_pos + c * grid_size, start_pos + r * grid_size))
        screen.blit(text_surf, text_rect)

def check_bounds(r, c): # (r, c)가 바둑판 범위 내에 있는지 확인
    return 0 <= r < 15 and 0 <= c < 15

def check_win(r, c, player): # (r, c)에 놓인 player의 돌을 기준으로 5목을 완성했는지 확인
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)] 
    
    for dr, dc in directions:
        count = 1 
        for i in range(1, 5):
            nr, nc = r + dr * i, c + dc * i
            if check_bounds(nr, nc) and board[nr][nc] == player:
                count += 1
            else:
                break
        for i in range(1, 5):
            nr, nc = r - dr * i, c - dc * i
            if check_bounds(nr, nc) and board[nr][nc] == player:
                count += 1
            else:
                break
        if count >= 5:
            # 흑돌 장목 금수
            if player == 1 and count > 5:
                return False
            return True
            
    return False

def reset_game(): # 게임 상태 초기화
    global board, turn, winner, game_state, move_history, win_reason
    global awaiting_forbidden_confirmation, forbidden_move_to_confirm
    
    board = [[0] * 15 for _ in range(15)]
    turn = 1
    winner = 0
    move_history.clear() # 바둑돌 순서 기록 초기화
    win_reason = "" # 승리 사유 초기화

    # 금수 확인 상태 초기화
    awaiting_forbidden_confirmation = False
    forbidden_move_to_confirm = None
    
    game_state = "PLAY"  # 게임 상태를 "PLAY"로 변경

def draw_start_screen():   # 시작 화면 그리기
    # screen.fill(BROWN) # [수정]
    screen.blit(board_image, (0, 0)) # 시작 화면에도 배경 이미지 적용
    
    title_text = large_font.render("오목 게임", True, BLACK) # 타이틀
    title_rect = title_text.get_rect(center=(screen_width / 2, 150))
    screen.blit(title_text, title_rect)

    pygame.draw.rect(screen, GRAY, start_button_rect) # 시작 버튼
    start_text = font.render("게임 시작", True, BLACK)
    start_text_rect = start_text.get_rect(center=start_button_rect.center)
    screen.blit(start_text, start_text_rect)

    pygame.draw.rect(screen, GRAY, quit_button_start_rect) # 종료 버튼
    quit_text = font.render("게임 종료", True, BLACK)
    quit_text_rect = quit_text.get_rect(center=quit_button_start_rect.center)
    screen.blit(quit_text, quit_text_rect)

def draw_game_ui():  # 게임 중 및 종료 UI 그리기
    # UI 버튼들은 배경 이미지 위에 그려져야 하므로 수정할 필요 없음
    if game_state == "PLAY":
        # "수 되돌리기" 버튼
        pygame.draw.rect(screen, GRAY, undo_button_rect)
        undo_text = font.render("수 되돌리기", True, BLACK)
        undo_text_rect = undo_text.get_rect(center=undo_button_rect.center)
        screen.blit(undo_text, undo_text_rect)
        
        # "게임 종료" 버튼
        pygame.draw.rect(screen, GRAY, quit_button_rect)
        quit_text = font.render("게임 종료", True, BLACK)
        quit_text_rect = quit_text.get_rect(center=quit_button_rect.center)
        screen.blit(quit_text, quit_text_rect)

    elif game_state == "OVER":
        # 승자 텍스트
        winner_text_str = "흑돌 승리!" if winner == 1 else "백돌 승리!"
        text_surface = large_font.render(winner_text_str, True, RED)
        
        text_rect = text_surface.get_rect(center=(785, 130)) 
        pygame.draw.rect(screen, GRAY, text_rect.inflate(20, 20))
        screen.blit(text_surface, text_rect)
        
        # 승리 사유 텍스트
        reason_surf = font.render(f"({win_reason})", True, BLACK)
        reason_rect = reason_surf.get_rect(center=(785, 190)) 
        screen.blit(reason_surf, reason_rect)

        # "다시하기" 버튼
        pygame.draw.rect(screen, GRAY, replay_button_rect)
        replay_text = font.render("다시하기", True, BLACK)
        replay_text_rect = replay_text.get_rect(center=replay_button_rect.center)
        screen.blit(replay_text, replay_text_rect)

        # "게임 종료" 버튼
        pygame.draw.rect(screen, GRAY, quit_button_rect)
        quit_text = font.render("게임 종료", True, BLACK)
        quit_text_rect = quit_text.get_rect(center=quit_button_rect.center)
        screen.blit(quit_text, quit_text_rect)

def draw_confirmation_warning(): # 금수 경고
    if awaiting_forbidden_confirmation and forbidden_move_to_confirm:
        text_surf = font.render("금수입니다! 다시 클릭하면 패배합니다.", True, RED)  # 1. 경고
        text_rect = text_surf.get_rect(center=((start_pos + board_size * grid_size + start_pos) / 2, screen_height / 2))
        pygame.draw.rect(screen, GRAY, text_rect.inflate(20, 20))
        screen.blit(text_surf, text_rect)
        
        r, c = forbidden_move_to_confirm    # 2. 금수 위치 빨간 원 표시
        pos_x = start_pos + c * grid_size
        pos_y = start_pos + r * grid_size
        pygame.draw.circle(screen, RED, (pos_x, pos_y), 20, 3) # 테두리 굵기 3

def get_line_count(r, c, player, dr, dc):  # (r,c)돌 가정해, (dr, dc) 방향의 연속된 돌 개수 측정
    count = 1 
    
    for i in range(1, 6): 
        nr, nc = r + dr * i, c + dc * i
        if check_bounds(nr, nc) and board[nr][nc] == player:
            count += 1
        else:
            break
    for i in range(1, 6):
        nr, nc = r - dr * i, c - dc * i
        if check_bounds(nr, nc) and board[nr][nc] == player:
            count += 1
        else:
            break
    return count

def is_forbidden(r, c, player): # (r, c)에 player 돌을 놓았을 때 금수인지 판정
    if player == 2: 
        return False

    board[r][c] = player # 1. 임시 돌
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)] 
    line_counts = [] 
    
    for dr, dc in directions:
        line_counts.append(get_line_count(r, c, player, dr, dc))

    board[r][c] = 0 # 2. 임시 돌 제거
    
    if 5 in line_counts:
        is_6_mok = any(count >= 6 for count in line_counts)
        if not is_6_mok:
             return False # 5목은 승리이므로 금수가 아님

    if any(count >= 6 for count in line_counts): #장목 판정
        return True # 장목은 금수.

    fours = line_counts.count(4)    # 4x4, 3x3, 3-4 판정
    threes = line_counts.count(3)
    
    if (threes + fours) >= 2:     # 3줄 또는 4줄의 합이 2개 이상일 시 금수 판정
        return True
    return False # 금수 아님


# --- 3. 메인 게임 루프 [수정] ---
running = True
clock = pygame.time.Clock()

while running:
    # FPS 설정
    clock.tick(60)

    # --- 3-1. 이벤트 처리 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # 마우스 클릭 처리
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            
            # --- 시작 화면에서의 클릭 ---
            if game_state == "START":
                awaiting_forbidden_confirmation = False
                
                if start_button_rect.collidepoint(x, y):
                    reset_game() 
                elif quit_button_start_rect.collidepoint(x, y):
                    running = False
            
            # --- 게임 중일 때의 클릭 [수정됨] ---
            elif game_state == "PLAY":
                
                row = round((y - start_pos) / grid_size)
                col = round((x - start_pos) / grid_size)
                
                if awaiting_forbidden_confirmation:
                    if (row, col) == forbidden_move_to_confirm:
                        board[row][col] = turn
                        move_history.append((row, col, turn))
                        winner = 2 # 백돌 승리
                        win_reason = "흑돌 금수패"
                        game_state = "OVER"
                    
                    else:
                        awaiting_forbidden_confirmation = False
                        forbidden_move_to_confirm = None
                        
                        if undo_button_rect.collidepoint(x, y):
                            if move_history:
                                last_r, last_c, _ = move_history.pop()
                                board[last_r][last_c] = 0 
                                turn = 3 - turn 
                        elif quit_button_rect.collidepoint(x, y):
                            running = False
                        elif 0 <= row < 15 and 0 <= col < 15 and board[row][col] == 0:
                            board[row][col] = turn
                            move_history.append((row, col, turn))
                            if check_win(row, col, turn):
                                winner = turn
                                win_reason = "5목 완성"
                                game_state = "OVER" 
                            else:
                                turn = 3 - turn
                
                else:
                    if undo_button_rect.collidepoint(x, y):
                        if move_history:
                            last_r, last_c, _ = move_history.pop()
                            board[last_r][last_c] = 0 
                            turn = 3 - turn 
                    elif quit_button_rect.collidepoint(x, y):
                        running = False
                        
                    elif 0 <= row < 15 and 0 <= col < 15 and board[row][col] == 0:
                        
                        if turn == 1 and is_forbidden(row, col, turn):
                            awaiting_forbidden_confirmation = True
                            forbidden_move_to_confirm = (row, col)
                        else:
                            board[row][col] = turn
                            move_history.append((row, col, turn))
                            
                            if check_win(row, col, turn):
                                winner = turn
                                win_reason = "5목 완성"
                                game_state = "OVER" 
                            else:
                                turn = 3 - turn 
            
            elif game_state == "OVER":
                awaiting_forbidden_confirmation = False
                
                if replay_button_rect.collidepoint(x, y):
                    reset_game() 
                elif quit_button_rect.collidepoint(x, y):
                    running = False

    # --- 4. 화면 그리기 ---
    
    if game_state == "START":
        draw_start_screen()
        
    elif game_state == "PLAY":
        draw_board()
        draw_stones()
        draw_game_ui()
        
    elif game_state == "OVER":
        draw_board()
        draw_stones()
        draw_move_numbers() # 수순 그리기
        draw_game_ui()
    
    if game_state == "PLAY":
        draw_confirmation_warning()
    
    pygame.display.flip()

# --- 5. 게임 종료 ---
pygame.quit()