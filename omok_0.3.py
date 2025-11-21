import pygame, os, sys
import random 

pygame.init()

# 윈도우 설정
screen_width = 900
screen_height = 700
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("오목 - 익스트림 난장판 모드")

# 색깔 정의
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 215, 0)
OBSTACLE_COLOR = (100, 100, 100) # 방해물 색 (진한 회색)

# 게임판 설정
board_size = 14
grid_size = 40
start_pos = 40

# --- 이미지 로드 ---
main_dir = os.path.split(os.path.abspath(__file__))[0]

def load_image(name):
    path = os.path.join(main_dir, "image", name)
    return pygame.image.load(path).convert_alpha()

try:
    board_image = load_image("board.png")
    board_image = pygame.transform.scale(board_image, (screen_width, screen_height))

    stone_size = 36
    black_stone_image = load_image("black.png")
    black_stone_image = pygame.transform.scale(black_stone_image, (stone_size, stone_size))
    
    white_stone_image = load_image("white.png")
    white_stone_image = pygame.transform.scale(white_stone_image, (stone_size, stone_size))

    black_stone_latest_image = load_image("black_latest.png")
    black_stone_latest_image = pygame.transform.scale(black_stone_latest_image, (stone_size, stone_size))

    white_stone_latest_image = load_image("white_latest.png")
    white_stone_latest_image = pygame.transform.scale(white_stone_latest_image, (stone_size, stone_size))
    
except pygame.error as e:
    print(f"이미지 로드 오류: {e}")
    sys.exit() # 이미지가 없으면 게임을 진행할 수 없으므로 종료

stone_radius = stone_size // 2

# --- 전역 변수 ---
board = [[0] * 15 for _ in range(15)]
turn = 1
winner = 0
game_state = "START"
move_history = []
win_reason = ""
current_mode = "NORMAL"

# 난장판 모드 관련 변수
chaos_move_counter = 0     # 현재 몇 수 두었는지 카운트 (양쪽 합산)
chaos_trigger_limit = 0    # 이번 이벤트가 발동하기 위한 목표 횟수
last_event_message = ""    # 화면에 띄울 이벤트 메시지
event_message_timer = 0    # 메시지를 띄울 시간 타이머

awaiting_forbidden_confirmation = False
forbidden_move_to_confirm = None

# 폰트 설정
try:
    font = pygame.font.SysFont("malgungothic", 35)
    large_font = pygame.font.SysFont("malgungothic", 60)
    move_num_font = pygame.font.SysFont("malgungothic", 18)
    small_font = pygame.font.SysFont("malgungothic", 25) # 이벤트 메시지용
except:
    font = pygame.font.Font(None, 35)
    large_font = pygame.font.Font(None, 60)
    move_num_font = pygame.font.Font(None, 18)
    small_font = pygame.font.Font(None, 25)

# 버튼 설정
mode_button_rect = pygame.Rect(300, 230, 300, 60)
start_button_rect = pygame.Rect(300, 310, 300, 90)
quit_button_start_rect = pygame.Rect(300, 420, 300, 80)

undo_button_rect = pygame.Rect(670, 200, 180, 60)
replay_button_rect = pygame.Rect(670, 300, 180, 60)
quit_button_rect = pygame.Rect(670, 400, 180, 60)


# --- 함수 정의 ---

def draw_board():
    screen.blit(board_image, (0, 0))

def draw_stones():
    for r in range(15):
        for c in range(15):
            center_x = start_pos + c * grid_size
            center_y = start_pos + r * grid_size
            blit_x = center_x - stone_radius
            blit_y = center_y - stone_radius

            if board[r][c] == 1: # 흑돌
                if move_history and move_history[-1][:2] == (r, c):
                    screen.blit(black_stone_latest_image, (blit_x, blit_y))
                else:
                    screen.blit(black_stone_image, (blit_x, blit_y))
            elif board[r][c] == 2: # 백돌
                if move_history and move_history[-1][:2] == (r, c):
                    screen.blit(white_stone_latest_image, (blit_x, blit_y))
                else:
                    screen.blit(white_stone_image, (blit_x, blit_y))
            elif board[r][c] == 3: # [New] 방해물 (돌을 둘 수 없음)
                # 방해물은 이미지가 없으므로 직접 그리기 (회색 원 + X)
                pygame.draw.circle(screen, OBSTACLE_COLOR, (center_x, center_y), stone_radius)
                pygame.draw.line(screen, BLACK, (center_x - 10, center_y - 10), (center_x + 10, center_y + 10), 3)
                pygame.draw.line(screen, BLACK, (center_x + 10, center_y - 10), (center_x - 10, center_y + 10), 3)

def draw_move_numbers():
    black_count = 0
    white_count = 0
    
    # 난장판 이벤트로 사라진 돌들이 move_history에는 남아있을 수 있음.
    # 따라서 보드에 실제 돌이 있는 경우에만 번호를 그림.
    for (r, c, player) in move_history:
        if board[r][c] != player: continue # 돌이 사라졌거나 바뀌었으면 패스

        move_num = ""
        if player == 1:
            black_count += 1
            move_num = str(black_count)
            text_color = WHITE
        else:
            white_count += 1
            move_num = str(white_count)
            text_color = BLACK
            
        text_surf = move_num_font.render(move_num, True, text_color)
        text_rect = text_surf.get_rect(center=(start_pos + c * grid_size, start_pos + r * grid_size))
        screen.blit(text_surf, text_rect)

def check_bounds(r, c):
    return 0 <= r < 15 and 0 <= c < 15

def check_win(r, c, player):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        for i in range(1, 5):
            nr, nc = r + dr * i, c + dc * i
            if check_bounds(nr, nc) and board[nr][nc] == player:
                count += 1
            else: break
        for i in range(1, 5):
            nr, nc = r - dr * i, c - dc * i
            if check_bounds(nr, nc) and board[nr][nc] == player:
                count += 1
            else: break
            
        if count >= 5:
            if current_mode == "NORMAL" and player == 1 and count > 5:
                return False
            return True # 난장판 모드는 6목 이상도 승리
    return False

def get_empty_positions():
    empty_pos = []
    for r in range(15):
        for c in range(15):
            if board[r][c] == 0:
                empty_pos.append((r, c))
    return empty_pos

def trigger_chaos_event(): # [New] 난장판 이벤트 발생 함수
    global last_event_message, event_message_timer, board, move_history
    
    event_type = random.randint(1, 3)
    last_event_message = ""
    event_message_timer = 120 # 약 2초간 메시지 표시
    
    if event_type == 1: # 1. 돌 소멸 (1~3개)
        stones_pos = []
        for r in range(15):
            for c in range(15):
                if board[r][c] == 1 or board[r][c] == 2: # 흑/백돌만 대상
                    stones_pos.append((r, c))
        
        if stones_pos:
            num_to_remove = random.randint(1, min(3, len(stones_pos)))
            targets = random.sample(stones_pos, num_to_remove)
            for r, c in targets:
                board[r][c] = 0 # 돌 제거
            last_event_message = f"이벤트: 돌 {num_to_remove}개가 증발했습니다!"
        else:
            last_event_message = "이벤트: 사라질 돌이 없습니다..."

    elif event_type == 2: # 2. 방해물 생성 (제3의 돌)
        empty_pos = get_empty_positions()
        if empty_pos:
            r, c = random.choice(empty_pos)
            board[r][c] = 3 # 3번은 방해물
            last_event_message = "이벤트: 방해물이 떨어졌습니다!"
        else:
            last_event_message = "이벤트: 방해물을 놓을 자리가 없습니다."

    elif event_type == 3: # 3. 흑/백 2개씩 랜덤 생성
        empty_pos = get_empty_positions()
        if len(empty_pos) >= 4:
            targets = random.sample(empty_pos, 4)
            # 흑 2개
            board[targets[0][0]][targets[0][1]] = 1
            board[targets[1][0]][targets[1][1]] = 1
            # 백 2개
            board[targets[2][0]][targets[2][1]] = 2
            board[targets[3][0]][targets[3][1]] = 2
            last_event_message = "이벤트: 흑돌과 백돌이 2개씩 솟아납니다!"
        else:
            last_event_message = "이벤트: 돌이 솟아날 공간이 부족합니다."

def reset_game():
    global board, turn, winner, game_state, move_history, win_reason
    global awaiting_forbidden_confirmation, forbidden_move_to_confirm
    global chaos_move_counter, chaos_trigger_limit, last_event_message
    
    board = [[0] * 15 for _ in range(15)]
    turn = 1
    winner = 0
    move_history.clear()
    win_reason = ""
    awaiting_forbidden_confirmation = False
    forbidden_move_to_confirm = None
    
    # 난장판 모드 초기화
    if current_mode == "CHAOS":
        chaos_move_counter = 0
        # 양쪽이 N번 두어야 하므로, 총 턴수는 2*N ~ 2*M
        # 여기서는 '각자' 2~4번 둔 후로 설정 (즉, 총 4~8수 후 이벤트)
        chaos_trigger_limit = random.randint(4, 8) 
        last_event_message = "난장판 모드 시작! 곧 이벤트가 발생합니다..."
        event_message_timer = 120
    
    game_state = "PLAY"

def draw_start_screen():
    screen.blit(board_image, (0, 0))
    
    title_text = large_font.render("오목 게임", True, BLACK)
    title_rect = title_text.get_rect(center=(screen_width / 2, 120))
    screen.blit(title_text, title_rect)

    # 모드 버튼
    pygame.draw.rect(screen, YELLOW if current_mode == "CHAOS" else GRAY, mode_button_rect)
    if current_mode == "NORMAL":
        mode_str = "모드: 일반"
        mode_color = BLACK
    else:
        mode_str = "모드: 난장판"
        mode_color = RED
    mode_text = font.render(mode_str, True, mode_color)
    screen.blit(mode_text, mode_text.get_rect(center=mode_button_rect.center))

    # 시작/종료 버튼
    pygame.draw.rect(screen, GRAY, start_button_rect)
    start_text = font.render("게임 시작", True, BLACK)
    screen.blit(start_text, start_text.get_rect(center=start_button_rect.center))

    pygame.draw.rect(screen, GRAY, quit_button_start_rect)
    quit_text = font.render("게임 종료", True, BLACK)
    screen.blit(quit_text, quit_text.get_rect(center=quit_button_start_rect.center))

def draw_game_ui():
    global event_message_timer
    
    if game_state == "PLAY":
        # 수 되돌리기 (난장판 모드에서는 비활성화 추천하지만 일단 둠)
        if current_mode == "NORMAL":
            pygame.draw.rect(screen, GRAY, undo_button_rect)
            undo_text = font.render("수 되돌리기", True, BLACK)
            screen.blit(undo_text, undo_text.get_rect(center=undo_button_rect.center))
        else:
            # 난장판 모드일 때는 '수 되돌리기' 대신 '이벤트 대기' 정보나 공백 처리
            # (랜덤 이벤트 때문에 되돌리기가 매우 복잡해지므로 막는 것이 좋음)
            pygame.draw.rect(screen, (200, 200, 200), undo_button_rect) # 비활성 색
            undo_text = font.render("되돌리기 불가", True, (100, 100, 100))
            screen.blit(undo_text, undo_text.get_rect(center=undo_button_rect.center))

        pygame.draw.rect(screen, GRAY, quit_button_rect)
        quit_text = font.render("게임 종료", True, BLACK)
        screen.blit(quit_text, quit_text.get_rect(center=quit_button_rect.center))
        
        mode_text = font.render(f"[{'난장판' if current_mode == 'CHAOS' else '일반'}]", True, BLUE)
        screen.blit(mode_text, (670, 150))
        
        # [New] 이벤트 메시지 출력
        if current_mode == "CHAOS" and event_message_timer > 0:
            msg_surf = small_font.render(last_event_message, True, RED)
            # 화면 상단 중앙 혹은 우측 패널에 표시
            screen.blit(msg_surf, (650, 50)) 
            event_message_timer -= 1

    elif game_state == "OVER":
        winner_text_str = "흑돌 승리!" if winner == 1 else "백돌 승리!"
        text_surface = large_font.render(winner_text_str, True, RED)
        text_rect = text_surface.get_rect(center=(785, 130))
        pygame.draw.rect(screen, GRAY, text_rect.inflate(20, 20))
        screen.blit(text_surface, text_rect)
        
        reason_surf = font.render(f"({win_reason})", True, BLACK)
        screen.blit(reason_surf, reason_surf.get_rect(center=(785, 190)))

        pygame.draw.rect(screen, GRAY, replay_button_rect)
        replay_text = font.render("다시하기", True, BLACK)
        screen.blit(replay_text, replay_text.get_rect(center=replay_button_rect.center))

        pygame.draw.rect(screen, GRAY, quit_button_rect)
        quit_text = font.render("게임 종료", True, BLACK)
        screen.blit(quit_text, quit_text.get_rect(center=quit_button_rect.center))

def draw_confirmation_warning():
    if awaiting_forbidden_confirmation and forbidden_move_to_confirm:
        text_surf = font.render("금수! 다시 클릭 시 패배.", True, RED)
        text_rect = text_surf.get_rect(center=((start_pos + board_size * grid_size + start_pos) / 2, screen_height / 2))
        pygame.draw.rect(screen, GRAY, text_rect.inflate(20, 20))
        screen.blit(text_surf, text_rect)
        
        r, c = forbidden_move_to_confirm
        pos_x = start_pos + c * grid_size
        pos_y = start_pos + r * grid_size
        pygame.draw.circle(screen, RED, (pos_x, pos_y), 20, 3)

def get_line_count(r, c, player, dr, dc):
    count = 1
    for i in range(1, 6):
        nr, nc = r + dr * i, c + dc * i
        if check_bounds(nr, nc) and board[nr][nc] == player: count += 1
        else: break
    for i in range(1, 6):
        nr, nc = r - dr * i, c - dc * i
        if check_bounds(nr, nc) and board[nr][nc] == player: count += 1
        else: break
    return count

def is_forbidden(r, c, player):
    if current_mode == "CHAOS": return False # 난장판은 금수 없음
    if player == 2: return False

    board[r][c] = player
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    line_counts = []
    for dr, dc in directions:
        line_counts.append(get_line_count(r, c, player, dr, dc))
    board[r][c] = 0
    
    if 5 in line_counts:
        if not any(count >= 6 for count in line_counts): return False
    if any(count >= 6 for count in line_counts): return True
    if (line_counts.count(4) + line_counts.count(3)) >= 2: return True
    return False

# --- 메인 루프 ---
running = True
clock = pygame.time.Clock()

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            
            if game_state == "START":
                awaiting_forbidden_confirmation = False
                if start_button_rect.collidepoint(x, y):
                    reset_game()
                elif mode_button_rect.collidepoint(x, y):
                    current_mode = "CHAOS" if current_mode == "NORMAL" else "NORMAL"
                elif quit_button_start_rect.collidepoint(x, y):
                    running = False
            
            elif game_state == "PLAY":
                row = round((y - start_pos) / grid_size)
                col = round((x - start_pos) / grid_size)
                
                # 금수 확인 중 처리
                if awaiting_forbidden_confirmation:
                    if (row, col) == forbidden_move_to_confirm: # 금수 강행 -> 패배
                        board[row][col] = turn
                        move_history.append((row, col, turn))
                        winner = 2
                        win_reason = "흑돌 금수패"
                        game_state = "OVER"
                    else:
                        awaiting_forbidden_confirmation = False
                        forbidden_move_to_confirm = None
                        
                        if quit_button_rect.collidepoint(x, y): running = False
                        elif undo_button_rect.collidepoint(x, y) and current_mode == "NORMAL":
                             if move_history:
                                last_r, last_c, _ = move_history.pop()
                                board[last_r][last_c] = 0
                                turn = 3 - turn
                        # 다른 곳 클릭 시 일반 착수 처리 로직으로 넘어감 (아래 else와 연결됨)
                
                else: # 금수 확인 중이 아닐 때
                    if quit_button_rect.collidepoint(x, y):
                        running = False
                    elif undo_button_rect.collidepoint(x, y):
                        if current_mode == "NORMAL" and move_history:
                            last_r, last_c, _ = move_history.pop()
                            board[last_r][last_c] = 0
                            turn = 3 - turn
                    
                    elif 0 <= row < 15 and 0 <= col < 15 and board[row][col] == 0:
                        # [금수 체크]
                        if current_mode == "NORMAL" and turn == 1 and is_forbidden(row, col, turn):
                            awaiting_forbidden_confirmation = True
                            forbidden_move_to_confirm = (row, col)
                        else:
                            # 착수
                            board[row][col] = turn
                            move_history.append((row, col, turn))
                            
                            # 승리 체크
                            if check_win(row, col, turn):
                                winner = turn
                                win_reason = "5목 완성"
                                game_state = "OVER"
                            else:
                                turn = 3 - turn
                                
                                # [New] 난장판 모드 이벤트 트리거 체크
                                if current_mode == "CHAOS" and game_state == "PLAY":
                                    chaos_move_counter += 1
                                    if chaos_move_counter >= chaos_trigger_limit:
                                        trigger_chaos_event()
                                        chaos_move_counter = 0
                                        chaos_trigger_limit = random.randint(4, 6) # 다음 이벤트까지 4~6수 (각자 2~3수)
                                        
                                        # 이벤트로 인해 승패가 갈릴 수도 있으므로 체크 (옵션)
                                        # 돌이 생겨서 5목이 완성될 수도 있으므로 턴 넘기기 전에 확인하면 좋지만
                                        # 규칙상 '착수 시' 승리이므로 다음 사람이 두면서 확인하게 둠.
            
            elif game_state == "OVER":
                if replay_button_rect.collidepoint(x, y):
                    reset_game()
                elif quit_button_rect.collidepoint(x, y):
                    running = False

    if game_state == "START":
        draw_start_screen()
    elif game_state == "PLAY":
        draw_board()
        draw_stones()
        draw_game_ui()
        draw_confirmation_warning()
    elif game_state == "OVER":
        draw_board()
        draw_stones()
        draw_move_numbers()
        draw_game_ui()
    
    pygame.display.flip()

pygame.quit()

