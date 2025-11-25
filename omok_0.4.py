import pygame, os, sys, random

# --- 초기화 및 설정 ---
pygame.init()

# 화면 크기 설정 (1360x768)
screen_width = 1360
screen_height = 768
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("오목 - 난장판")

# 색깔 정의
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
GRAY = (128, 128, 128)
OBSTACLE_COLOR = (80, 80, 80)
WOOD_TEXT_COLOR = (245, 240, 220)

# --- [수정] UI 오프셋 제거 및 보드 위치 원상복구 ---
# ui_offset_y = 80 # 제거

# --- 게임판 격자 정밀 계산 ---
board_cell_count = 14
board_display_size = 700
board_offset_x = 50
# [수정] 오프셋 제거하여 원래 중앙 위치로
board_offset_y = (screen_height - board_display_size) // 2

grid_size = 46
board_internal_margin = (board_display_size - (board_cell_count * grid_size)) // 2

stone_size = int(grid_size * 0.9)
stone_radius = stone_size // 2

# --- 이미지 로드 ---
main_dir = os.path.split(os.path.abspath(__file__))[0]
image_dir = os.path.join(main_dir, "image")

def load_image(name, size=None):
    path = os.path.join(image_dir, name)
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    except pygame.error as e:
        return None

# 이미지 로드 및 크기 조정
title_screen_image = load_image("title_screen.png", (screen_width, screen_height))
board_image = load_image("board.png", (board_display_size, board_display_size))

# 돌 이미지
black_stone_image = load_image("black.png", (stone_size, stone_size))
white_stone_image = load_image("white.png", (stone_size, stone_size))
black_stone_latest_image = load_image("black_latest.png", (stone_size, stone_size))
white_stone_latest_image = load_image("white_latest.png", (stone_size, stone_size))

# 버튼 이미지
btn_w_large, btn_h_large = 250, 80
btn_w_small, btn_h_small = 200, 70

btn_start_img = load_image("btn_start.png", (btn_w_large, btn_h_large))
btn_quit_img = load_image("btn_quit.png", (btn_w_large, btn_h_large))
btn_quit_game_img = load_image("btn_quit.png", (btn_w_small, btn_h_small))

btn_mode_normal_img = load_image("btn_mode_normal.png", (btn_w_large, btn_h_large))
btn_mode_chaos_img = load_image("btn_mode_chaos.png", (btn_w_large, btn_h_large))

btn_undo_img = load_image("btn_undo.png", (btn_w_small, btn_h_small))
btn_undo_disabled_img = load_image("btn_undo_disabled.png", (btn_w_small, btn_h_small))
btn_replay_img = load_image("btn_replay.png", (btn_w_small, btn_h_small))
btn_main_img = load_image("btn_main.png", (btn_w_small, btn_h_small))

# 텍스트 보드 이미지 로드
text_board_w, text_board_h = 450, 250
board_text_img = load_image("board_text.png", (text_board_w, text_board_h))


# --- 전역 변수 ---
board = [[0] * 15 for _ in range(15)]
turn = 1
winner = 0
game_state = "START"
move_history = []
win_reason = ""
current_mode = "NORMAL"

chaos_move_counter = 0
chaos_trigger_limit = 0
last_event_message = ""
event_message_timer = 0

awaiting_forbidden_confirmation = False
forbidden_move_to_confirm = None

# --- 이벤트용 전역 변수 ---
is_double_turn_active = False
double_turn_count = 0

is_color_unified_active = False
color_unification_timer = 0

is_placing_obstacle_active = False

is_time_attack_active = False
TIME_LIMIT_SECONDS = 8
turn_time_limit = TIME_LIMIT_SECONDS * 60
current_turn_timer = 0


# 폰트 설정
def get_font(size, bold=False):
    try:
        font_path = pygame.font.match_font("malgungothic")
        if not font_path:
             font_path = pygame.font.match_font("arial")
        font = pygame.font.Font(font_path, size)
        font.set_bold(bold)
        return font
    except:
        return pygame.font.Font(None, size)

font_large = get_font(70, True)
font_medium = get_font(40)
font_small = get_font(25)
font_move_num = get_font(18, True)


# --- UI 레이아웃 설정 ---
mode_btn_margin_x = 50
mode_btn_margin_y = 50
mode_button_rect = btn_mode_normal_img.get_rect(topright=(screen_width - mode_btn_margin_x, mode_btn_margin_y))

bottom_btn_margin_y = 80
btn_spacing_x = 50
total_bottom_btn_width = btn_w_large * 2 + btn_spacing_x
start_btn_x = (screen_width - total_bottom_btn_width) // 2
bottom_btn_y = screen_height - btn_h_large - bottom_btn_margin_y

start_button_rect = btn_start_img.get_rect(topleft=(start_btn_x, bottom_btn_y))
quit_button_start_rect = btn_quit_img.get_rect(topleft=(start_btn_x + btn_w_large + btn_spacing_x, bottom_btn_y))

ui_panel_x = board_offset_x + board_display_size + 50
ui_center_x = ui_panel_x + (screen_width - ui_panel_x) // 2
ui_start_y = 100

# [수정] 텍스트 보드 및 버튼 위치 원상복구 (오프셋 제거)
text_board_rect = board_text_img.get_rect(center=(ui_center_x, ui_start_y + 120))
undo_button_rect = btn_undo_img.get_rect(center=(ui_center_x, text_board_rect.bottom + 60))
quit_button_game_rect = btn_quit_game_img.get_rect(center=(ui_center_x, text_board_rect.bottom + 140))

# 게임 종료 화면 버튼들
replay_button_rect = btn_replay_img.get_rect(center=(ui_center_x, screen_height - 240))
main_button_rect = btn_main_img.get_rect(center=(ui_center_x, screen_height - 150))
quit_button_over_rect = btn_quit_game_img.get_rect(center=(ui_center_x, screen_height - 60))


# --- 함수 정의 ---

def get_board_coords(r, c):
    x = board_offset_x + board_internal_margin + c * grid_size
    y = board_offset_y + board_internal_margin + r * grid_size
    return x, y

def get_grid_pos(x, y):
    c = round((x - board_offset_x - board_internal_margin) / grid_size)
    r = round((y - board_offset_y - board_internal_margin) / grid_size)
    return r, c

def draw_game_screen():
    screen.fill((240, 230, 210))
    screen.blit(board_image, (board_offset_x, board_offset_y))

def draw_stones():
    for r in range(15):
        for c in range(15):
            cx, cy = get_board_coords(r, c)
            blit_x = cx - stone_radius
            blit_y = cy - stone_radius
            
            stone_value = board[r][c]

            if is_color_unified_active and stone_value in (1, 2):
                stone_value = turn

            if stone_value == 1:
                img = black_stone_latest_image if move_history and move_history[-1][:2] == (r, c) else black_stone_image
                screen.blit(img, (blit_x, blit_y))
            elif stone_value == 2:
                img = white_stone_latest_image if move_history and move_history[-1][:2] == (r, c) else white_stone_image
                screen.blit(img, (blit_x, blit_y))
            elif stone_value == 3: # 장애물
                pygame.draw.circle(screen, OBSTACLE_COLOR, (cx, cy), stone_radius)
                pygame.draw.line(screen, BLACK, (cx - 10, cy - 10), (cx + 10, cy + 10), 4)
                pygame.draw.line(screen, BLACK, (cx + 10, cy - 10), (cx - 10, cy + 10), 4)
            elif stone_value == 4: # 공용돌
                pygame.draw.circle(screen, GRAY, (cx, cy), stone_radius)
                pygame.draw.circle(screen, BLACK, (cx, cy), stone_radius, 2)

def draw_move_numbers():
    black_count = 0
    white_count = 0
    for (r, c, player) in move_history:
        if board[r][c] != player: continue
        
        if player == 1:
            black_count += 1
            num_str = str(black_count)
            text_color = WHITE
        else:
            white_count += 1
            num_str = str(white_count)
            text_color = BLACK
            
        text_surf = font_move_num.render(num_str, True, text_color)
        cx, cy = get_board_coords(r, c)
        text_rect = text_surf.get_rect(center=(cx, cy))
        screen.blit(text_surf, text_rect)

def check_bounds(r, c):
    return 0 <= r < 15 and 0 <= c < 15

def check_win(r, c, player):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        for i in range(1, 5):
            nr, nc = r + dr * i, c + dc * i
            if check_bounds(nr, nc) and (board[nr][nc] == player or board[nr][nc] == 4): count += 1
            else: break
        for i in range(1, 5):
            nr, nc = r - dr * i, c - dc * i
            if check_bounds(nr, nc) and (board[nr][nc] == player or board[nr][nc] == 4): count += 1
            else: break
            
        if count >= 5:
            if current_mode == "NORMAL" and player == 1 and count > 5: return False
            return True
    return False

def get_empty_positions():
    return [(r, c) for r in range(15) for c in range(15) if board[r][c] == 0]

def trigger_chaos_event():
    global last_event_message, event_message_timer, board, move_history
    global is_double_turn_active, double_turn_count
    global is_color_unified_active, color_unification_timer
    global is_placing_obstacle_active
    global is_time_attack_active, current_turn_timer

    is_time_attack_active = False 

    event_type = random.randint(1, 8)
    event_message_timer = 180

    if event_type == 1: # 돌 증발
        stones_pos = [(r, c) for r in range(15) for c in range(15) if board[r][c] in (1, 2)]
        if stones_pos:
            num_to_remove = random.randint(1, min(3, len(stones_pos)))
            for r, c in random.sample(stones_pos, num_to_remove):
                board[r][c] = 0
            last_event_message = f"돌 {num_to_remove}개가 증발했습니다!"
        else: last_event_message = "증발할 돌이 없습니다."

    elif event_type == 2: # 방해물
        empty_pos = get_empty_positions()
        if empty_pos:
            r, c = random.choice(empty_pos)
            board[r][c] = 3
            last_event_message = "하늘에서 방해물이 떨어졌습니다!"
        else: last_event_message = "방해물을 놓을 곳이 없습니다."

    elif event_type == 3: # 돌 솟아남
        empty_pos = get_empty_positions()
        if len(empty_pos) >= 4:
            targets = random.sample(empty_pos, 4)
            board[targets[0][0]][targets[0][1]] = 1
            board[targets[1][0]][targets[1][1]] = 1
            board[targets[2][0]][targets[2][1]] = 2
            board[targets[3][0]][targets[3][1]] = 2
            last_event_message = "흑돌과 백돌이 2개씩 솟아납니다!"
        else: last_event_message = "돌이 솟아날 공간이 부족합니다."

    elif event_type == 4: # 돌 2배로 두기
        is_double_turn_active = True
        double_turn_count = 4
        last_event_message = "양쪽 플레이어 모두 돌을 2번씩 둡니다!"

    elif event_type == 5: # 일시적으로 돌 색 통일
        is_color_unified_active = True
        color_unification_timer = 180
        last_event_message = "잠시 동안 모든 돌 색이 통일됩니다!"

    elif event_type == 6: # 플레이어 선택 장애물
        is_placing_obstacle_active = True
        last_event_message = "원하는 위치에 장애물을 하나 두세요."

    elif event_type == 7: # 시간 제한 (8초)
        is_time_attack_active = True
        current_turn_timer = turn_time_limit
        last_event_message = f"타임 어택! {TIME_LIMIT_SECONDS}초 안에 두세요."

    elif event_type == 8: # 공용돌 배치
        empty_pos = get_empty_positions()
        if empty_pos:
            r, c = random.choice(empty_pos)
            board[r][c] = 4
            last_event_message = "'공용돌'(회색)이 나타났습니다!"
        else: last_event_message = "공용돌을 놓을 곳이 없습니다."


def reset_game():
    global board, turn, winner, game_state, move_history, win_reason
    global awaiting_forbidden_confirmation, forbidden_move_to_confirm
    global chaos_move_counter, chaos_trigger_limit, last_event_message, event_message_timer
    global is_double_turn_active, double_turn_count, is_color_unified_active, color_unification_timer
    global is_placing_obstacle_active, is_time_attack_active, current_turn_timer
    
    board = [[0] * 15 for _ in range(15)]
    turn = 1
    winner = 0
    move_history.clear()
    win_reason = ""
    awaiting_forbidden_confirmation = False
    forbidden_move_to_confirm = None
    event_message_timer = 0
    
    is_double_turn_active = False
    double_turn_count = 0
    is_color_unified_active = False
    color_unification_timer = 0
    is_placing_obstacle_active = False
    is_time_attack_active = False
    current_turn_timer = 0

    if current_mode == "CHAOS":
        chaos_move_counter = 0
        chaos_trigger_limit = random.randint(4, 8)
        last_event_message = "난장판 모드 시작! 이벤트를 조심하세요."
        event_message_timer = 180
    
    game_state = "PLAY"

def draw_ui_panel():
    if game_state == "PLAY":
        # 현재 턴 표시
        turn_text = "흑돌 차례" if turn == 1 else "백돌 차례"
        turn_color = BLACK if turn == 1 else WHITE
        turn_bg = WHITE if turn == 1 else BLACK
        
        turn_surf = font_medium.render(turn_text, True, turn_color)
        # [수정] UI 위치를 보드 위로 올림 (y 좌표를 50으로 설정)
        turn_rect = turn_surf.get_rect(center=(ui_center_x, 50))
        pygame.draw.rect(screen, turn_bg, turn_rect.inflate(20, 10))
        screen.blit(turn_surf, turn_rect)

        # 타임 어택 시간 표시 (턴 표시 바로 아래)
        if is_time_attack_active:
            time_left = max(0, int(current_turn_timer / 60))
            time_surf = font_large.render(str(time_left), True, RED)
            time_rect = time_surf.get_rect(center=(ui_center_x, 120))
            screen.blit(time_surf, time_rect)

    # 텍스트 보드 그리기 및 정보 표시 (난장판 모드)
    if current_mode == "CHAOS":
        screen.blit(board_text_img, text_board_rect)
        
        # 1. 이벤트 메시지 표시
        if event_message_timer > 0:
            msg_surf = font_small.render(last_event_message, True, WOOD_TEXT_COLOR)
            msg_rect = msg_surf.get_rect(center=(text_board_rect.centerx, text_board_rect.top + 70))
            screen.blit(msg_surf, msg_rect)

        # 2. 남은 턴 표시
        turns_left = chaos_trigger_limit - chaos_move_counter
        turns_surf = font_medium.render(f"다음 이벤트까지: {turns_left}턴", True, WOOD_TEXT_COLOR)
        turns_rect = turns_surf.get_rect(center=(text_board_rect.centerx, text_board_rect.bottom - 70))
        screen.blit(turns_surf, turns_rect)

    # 버튼 그리기
    if game_state == "PLAY":
        if current_mode == "NORMAL":
            screen.blit(btn_undo_img, undo_button_rect)
        else:
            screen.blit(btn_undo_disabled_img, undo_button_rect)
        screen.blit(btn_quit_game_img, quit_button_game_rect)
        
    elif game_state == "OVER":
        screen.blit(btn_replay_img, replay_button_rect)
        screen.blit(btn_main_img, main_button_rect)
        screen.blit(btn_quit_game_img, quit_button_over_rect)

def draw_game_over_overlay():
    if game_state == "OVER":
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        if winner == 1: winner_text = "흑돌 승리!"
        elif winner == 2: winner_text = "백돌 승리!"
        else: winner_text = "무승부/패배"

        win_surf = font_large.render(winner_text, True, RED)
        reason_surf = font_small.render(f"({win_reason})", True, WHITE)
        
        box_rect = pygame.Rect(0, 0, 500, 250)
        box_rect.center = (screen_width // 2, screen_height // 2 - 50)
        pygame.draw.rect(screen, BLACK, box_rect, border_radius=20)
        pygame.draw.rect(screen, RED, box_rect, 5, border_radius=20)
        
        win_rect = win_surf.get_rect(center=(box_rect.centerx, box_rect.centery - 30))
        reason_rect = reason_surf.get_rect(center=(box_rect.centerx, box_rect.centery + 40))
        
        screen.blit(win_surf, win_rect)
        screen.blit(reason_surf, reason_rect)

def draw_confirmation_warning():
    if awaiting_forbidden_confirmation and forbidden_move_to_confirm:
        warn_surf = font_small.render("금수입니다! 클릭 시 패배.", True, WHITE)
        box_rect = warn_surf.get_rect(center=(screen_width // 2, screen_height // 2)).inflate(40, 40)
        pygame.draw.rect(screen, RED, box_rect, border_radius=15)
        screen.blit(warn_surf, warn_surf.get_rect(center=box_rect.center))
        
        r, c = forbidden_move_to_confirm
        cx, cy = get_board_coords(r, c)
        pygame.draw.circle(screen, RED, (cx, cy), stone_radius + 5, 4)

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
    if current_mode == "CHAOS" or player == 2: return False
    board[r][c] = player
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    line_counts = [get_line_count(r, c, player, dr, dc) for dr, dc in directions]
    board[r][c] = 0
    
    if 5 in line_counts:
        if not any(count > 5 for count in line_counts): return False
    if any(count > 5 for count in line_counts): return True # 장목
    if (line_counts.count(4) + line_counts.count(3)) >= 2: return True # 33, 44, 34
    return False


# --- 메인 루프 ---
running = True
clock = pygame.time.Clock()

while running:
    clock.tick(60)
    if event_message_timer > 0: event_message_timer -= 1
    
    if is_color_unified_active:
        color_unification_timer -= 1
        if color_unification_timer <= 0:
            is_color_unified_active = False

    if game_state == "PLAY" and is_time_attack_active:
        current_turn_timer -= 1
        if current_turn_timer <= 0:
            winner = 3 - turn
            win_reason = "시간 초과 패배"
            game_state = "OVER"

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            
            if game_state == "START":
                if start_button_rect.collidepoint(x, y): reset_game()
                elif mode_button_rect.collidepoint(x, y):
                    current_mode = "CHAOS" if current_mode == "NORMAL" else "NORMAL"
                elif quit_button_start_rect.collidepoint(x, y): running = False
            
            elif game_state == "PLAY":
                if board_offset_x <= x < board_offset_x + board_display_size and \
                   board_offset_y <= y < board_offset_y + board_display_size:
                    r, c = get_grid_pos(x, y)
                    
                    if check_bounds(r, c):
                        if awaiting_forbidden_confirmation:
                            if (r, c) == forbidden_move_to_confirm:
                                board[r][c] = turn
                                move_history.append((r, c, turn))
                                winner = 2
                                win_reason = "흑돌 금수패"
                                game_state = "OVER"
                            else:
                                awaiting_forbidden_confirmation = False
                                forbidden_move_to_confirm = None
                        
                        elif board[r][c] == 0:
                            if is_placing_obstacle_active:
                                board[r][c] = 3
                                is_placing_obstacle_active = False
                            else:
                                if current_mode == "NORMAL" and turn == 1 and is_forbidden(r, c, turn):
                                    awaiting_forbidden_confirmation = True
                                    forbidden_move_to_confirm = (r, c)
                                else:
                                    board[r][c] = turn
                                    move_history.append((r, c, turn))
                                    
                                    if check_win(r, c, turn):
                                        winner = turn
                                        win_reason = "5목 완성"
                                        game_state = "OVER"
                                    else:
                                        turn_ended = True
                                        if is_double_turn_active:
                                            double_turn_count -= 1
                                            if double_turn_count % 2 != 0:
                                                turn_ended = False
                                            if double_turn_count <= 0:
                                                is_double_turn_active = False

                                        if turn_ended:
                                            turn = 3 - turn
                                            if is_time_attack_active:
                                                current_turn_timer = turn_time_limit

                                            if current_mode == "CHAOS":
                                                chaos_move_counter += 1
                                                if chaos_move_counter >= chaos_trigger_limit:
                                                    trigger_chaos_event()
                                                    chaos_move_counter = 0
                                                    chaos_trigger_limit = random.randint(4, 8)

                if quit_button_game_rect.collidepoint(x, y): running = False
                elif undo_button_rect.collidepoint(x, y) and current_mode == "NORMAL" and not awaiting_forbidden_confirmation:
                    if move_history:
                        last_r, last_c, _ = move_history.pop()
                        board[last_r][last_c] = 0
                        turn = 3 - turn

            elif game_state == "OVER":
                if replay_button_rect.collidepoint(x, y): reset_game()
                elif main_button_rect.collidepoint(x, y): game_state = "START"
                elif quit_button_over_rect.collidepoint(x, y): running = False

    if game_state == "START":
        screen.blit(title_screen_image, (0, 0))
        img = btn_mode_chaos_img if current_mode == "CHAOS" else btn_mode_normal_img
        screen.blit(img, mode_button_rect)
        screen.blit(btn_start_img, start_button_rect)
        screen.blit(btn_quit_img, quit_button_start_rect)
    else:
        draw_game_screen()
        draw_stones()
        if game_state == "OVER": draw_move_numbers()
        draw_ui_panel()
        draw_confirmation_warning()
        draw_game_over_overlay()
    
    pygame.display.flip()

pygame.quit()