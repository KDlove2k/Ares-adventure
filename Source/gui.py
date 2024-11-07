import os
import pygame
import time
import sys
import support_function
from UCS import *
from A_star import *
from BFS import *
from DFS import *


# khởi tạo giao diện 
pygame.init()

# set up màn hình
Screen_Width = 18 * 64
Screen_Height = 12 * 64
screen = pygame.display.set_mode((Screen_Width, Screen_Height))

# Font 
pygame.font.init()
font = pygame.font.SysFont(None, 33)


# Load hình ảnh từ thư mục Assets
wall_img = pygame.image.load(os.path.join("Assets", "wall.png")).convert_alpha()
floor_img = pygame.image.load(os.path.join("Assets", "floor.png")).convert_alpha()
switch_place_img = pygame.image.load(os.path.join("Assets", "point.png")).convert_alpha()
stone_img = pygame.image.load(os.path.join("Assets", "stone.png")).convert_alpha()
player_img = pygame.image.load(os.path.join("Assets", "player.png")).convert_alpha()

input_board_path = os.path.join(os.getcwd(), 'Source', 'input')



# nội dung ouput
output_content=[]

stop_timeout_event = threading.Event()

def time_limit_check(timeout_duration):
    print('time thread start')
    for _ in range(timeout_duration):
        if stop_timeout_event.is_set():
            print('Timeout thread stopped immediately')
            return  # Thoát ngay khi cờ dừng được bật
        time.sleep(1)
    print('reach timeout')
    support_function.timeout_event.set()

# đocj 1 input file
def get_board(path):
    global weights
    with open(path, 'r') as file:
        weight_line = file.readline().strip().split(' ')
        map_lines = file.readlines()[0:]
        weights = [int(weight) for weight in weight_line]
        board = [list(line.rstrip('\n')) for line in map_lines]
    return board

#trả về 1 danh sachs input
def get_boards():
    os.chdir(input_board_path)
    list_boards = []
    for file in os.listdir():
        if file.endswith(".txt"):
            file_path = os.path.join(input_board_path, file)
            board = get_board(file_path)
            list_boards.append(board)
    return list_boards


player_position = [0, 0]# vị trí ngưởi chơi
stones = {}# vị trí cục đá và cân nặng
weights = []# cân nặng của cục đá
graph_way_nodes = {} #đồ thị các node có thể đi của node hiện tại 
switches_pos = []# vị trí đích 

#tình trạng
is_running = False
is_paused = False
is_calculating = True


def get_indentX_indentY(board):
    # lấy chiều cao và chiều rộng của map input
    width = len(board[0])
    height = len(board)
    indent_x = (Screen_Width - width * 64) / 2.0
    indent_y = (Screen_Height - height * 64) / 2.0

    return indent_x, indent_y

# thêm kết nối giữa node và đồ thị 
def add_connection(board, graph, node, left_position, up_position, right_position, down_position):
    if node not in graph:
        graph[node] = []
    
    if (left_position[0] >= 0):
        if (board[left_position[1]][left_position[0]] != '#'):
            graph[node].append(left_position)

    if (up_position[1] >= 0):
        if (board[up_position[1]][up_position[0]] != '#'):
            graph[node].append(up_position)
    if (right_position[0] < len(board[0])):
        if (board[right_position[1]][right_position[0]] != '#'):
            graph[node].append(right_position)

    if (down_position[1] < len(board)):
        if (board[down_position[1]][down_position[0]] != '#'):
            graph[node].append(down_position)

# render map 
def render_map(board): 
    indent_x, indent_y = get_indentX_indentY(board)
    screen.fill((0, 0, 0)) 
    width = len(board[0])
    height = len(board)
    weight_index = 0

    for i in range(height):
        for j in range(width):
            #Sử dụng hàm add_connection để chỉ ra người chơi hành động nào có thể di chuyển ở một vị trí cụ thể
            if board[i][j] not in ['%', '#']:
                add_connection(board, graph_way_nodes, (j, i), (j-1, i), (j, i-1), (j+1, i), (j, i+1))
            # tường
            if board[i][j] == '#':
                screen.blit(wall_img, (j * 64 + indent_x, i * 64 + indent_y))

            # sàng
            if board[i][j] in [' ', '@', '$']:
                screen.blit(floor_img, (j * 64 + indent_x, i * 64 + indent_y))

            # đá
            if board[i][j] == '$':
                if weight_index < len(weights):
                    stones[(j, i)] = weights[weight_index]  
                    weight_index += 1  
                render_stones(board)

            # đích
            if board[i][j] in ['.', '+']:
                screen.blit(switch_place_img, (j * 64 + indent_x, i * 64 + indent_y))
                switches_pos.append((j, i))

            # người chơi 
            if board[i][j] in ['@', '+']:
                player_pos[0] = j
                player_pos[1] = i
                render_player(board)

# Render người chơi
def render_player(board):
    indent_x, indent_y = get_indentX_indentY(board)
    screen.blit(player_img, (player_pos[0] * 64 + indent_x, player_pos[1] * 64 + indent_y))



def render_stones(board):
    indent_x, indent_y = get_indentX_indentY(board)
    for stone in stones:
        stone_x = stone[0] * 64 + indent_x
        stone_y = stone[1] * 64 + indent_y

        # Sử dụng hình ảnh đá duy nhất
        screen.blit(stone_img, (stone_x, stone_y))

        # Vẽ vòng tròn tại trung tâm để hiển thị trọng lượng
        stone_rect = pygame.Rect(stone_x, stone_y, 64, 64)
        pygame.draw.circle(screen, (0, 0, 0), stone_rect.center, 25)  # Vòng tròn ngoài màu đen
        pygame.draw.circle(screen, (255, 255, 255), stone_rect.center, 23)  # Vòng tròn trong màu trắng

        # Hiển thị trọng lượng của viên đá
        weight = stones[stone]
        text = font.render(str(weight), True, (0, 0, 0))  # Chữ màu đen
        text_rect = text.get_rect(center=stone_rect.center)
        screen.blit(text, text_rect)




# Render đích
def render_switches(board,old_pos_player):
    indent_x, indent_y = get_indentX_indentY(board)
    if(tuple(old_pos_player) in switches_pos):
        screen.blit(switch_place_img, (old_pos_player[0] * 64 + indent_x, old_pos_player[1] * 64 + indent_y))
        
# Button size
Button_Witdh = 100
Button_Height = 50

# vị trí buton
 # Căn thẳng hàng phía bên trái màn hình
Start_Button_Position = (50, 50)  
Pause_Button_Position = (50, 120)  
Reset_Button_Position = (50, 190)
Exit_Button_Position = (50, 260)  

def render_buttons():
    #nút start
    pygame.draw.rect(screen, (255, 255, 255), (Start_Button_Position[0], Start_Button_Position[1], Button_Witdh, Button_Height))
    start_text = font.render("Start", True, (0, 0, 0))
    screen.blit(start_text, (Start_Button_Position[0] + 10, Start_Button_Position[1] + 10))
    #nút Pause
    pygame.draw.rect(screen, (255, 255, 255), (Pause_Button_Position[0], Pause_Button_Position[1], Button_Witdh, Button_Height))
    pause_text = font.render("Pause", True, (0, 0, 0))
    screen.blit(pause_text, (Pause_Button_Position[0] + 10, Pause_Button_Position[1] + 10))
    #nút reset
    pygame.draw.rect(screen, (255, 255, 255), (Reset_Button_Position[0], Reset_Button_Position[1], Button_Witdh, Button_Height))
    reset_text = font.render("Reset", True, (0, 0, 0))
    screen.blit(reset_text, (Reset_Button_Position[0] + 10, Reset_Button_Position[1] + 10))

    # Nút Exit
    pygame.draw.rect(screen, (255, 255, 255), (Exit_Button_Position[0], Exit_Button_Position[1], Button_Witdh, Button_Height))
    exit_text = font.render("Exit", True, (0, 0, 0))
    screen.blit(exit_text, (Exit_Button_Position[0] + 10, Exit_Button_Position[1] + 10))



    
def render_status_text(text):
    pygame.draw.rect(screen, (0, 0, 0), (Screen_Width - 150, 20, 145, 30))

    status_text = font.render(text, True, (255, 255, 255))
    screen.blit(status_text, (Screen_Width - 150, 20))

def render_algorithm_name(name):
    
    pygame.draw.rect(screen, (0, 0, 0), (550, 50, 200, 30))  
    algorithm_text = font.render(name, True, (255, 255, 255))  
    screen.blit(algorithm_text, (550, 70))
    

def calculation_animation():
    global is_calculating
    dot_count = 0
    max_dots = 3 

    while is_calculating:
      
        loading_text = "Calculating" + "." * dot_count
        render_status_text(loading_text)  # render text trên màn hình
        pygame.display.update()
        
        dot_count = (dot_count + 1) % (max_dots + 1)
        
        time.sleep(0.5) 



def render_cost_step(current_step, final_cost):
    pygame.draw.rect(screen, (0, 0, 0), (Screen_Width - 150, 60, 140, 60))  

        # Hiển thị bước hiện tại
    step_text = font.render(f"Step: {current_step}", True, (255, 255, 255))
    screen.blit(step_text, (Screen_Width - 150, 60))  

        # Hiển thị tổng chi phí dựa vào giá trị tại current_step
    if current_step < len(final_cost):
        current_cost = final_cost[current_step]
    else:
        current_cost = 0
        
    cost_text = font.render(f"Cost: {current_cost}", True, (255, 255, 255))
    screen.blit(cost_text, (Screen_Width - 150, 100))

def movement(board, node):
    global final_cost, cost_list
    x = 0
    y = 1
    player_move = 0  # move left: 1, move up: 2, move right: 3, move down: 4
    indent_x, indent_y = get_indentX_indentY(board)
    delay_time = 500  # Delay time between each move

    old_pos_player = player_pos.copy()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            return

    pygame.time.delay(delay_time)

    if (player_pos[x] - node[x] == 1):
        player_pos[x] -= 1
        player_move = 1
    elif (player_pos[y] - node[y] == 1):
        player_pos[y] -= 1
        player_move = 2
    elif (player_pos[x] - node[x] == -1):
        player_pos[x] += 1
        player_move = 3
    elif (player_pos[y] - node[y] == -1):
        player_pos[y] += 1
        player_move = 4

    if node in stones:
        old_pos_stone = node
        if player_move == 1:
            new_pos_stone = (node[x] - 1, node[y]) 
        elif player_move == 2:
            new_pos_stone = (node[x], node[y] - 1)  
        elif player_move == 3:
            new_pos_stone = (node[x] + 1, node[y])  
        elif player_move == 4:
            new_pos_stone = (node[x], node[y] + 1) 

        # Cập nhật vị trí của viên đá và chi phí
        stone_weight = stones[old_pos_stone]
        stones[new_pos_stone] = stones.pop(old_pos_stone)
        cost_list.append(cost_list[-1] + stone_weight)  # Tăng chi phí bằng trọng lượng của viên đá được đẩy
        cost_list.append(cost_list[-1] + stone_weight) 
        screen.blit(floor_img, (old_pos_stone[0] * 64 + indent_x, old_pos_stone[1] * 64 + indent_y))  
        render_stones(board)  

    else:
        # Nếu chỉ di chuyển mà không đẩy đá
        cost_list.append(cost_list[-1] + 1)  # Tăng chi phí chỉ đơn giản là +1

    screen.blit(floor_img, (old_pos_player[0] * 64 + indent_x, old_pos_player[1] * 64 + indent_y))  
    render_switches(board, old_pos_player) 
    render_player(board)  
    pygame.display.update()  

def is_win():
    for stone in stones:
        if stone not in switches_pos:
            return False
    
    return True

def flash_rect(text, size, color1, color2, duration=0.5):
    current_time = time.time()
    # Cứ mỗi nửa giây đổi màu giữa color1 và color2
    if int(current_time * 2) % 2 == 0:
        TEXT=get_font(size).render(text,True,color1)
        RECT=TEXT.get_rect(center=(Screen_Width // 2, Screen_Height // 2))
    else:
        TEXT=get_font(size).render(text,True,color2)
        RECT=TEXT.get_rect(center=(Screen_Width // 2, Screen_Height // 2))
    screen.blit(TEXT,RECT)

def game_loop(board):
    global is_running, is_paused, is_calculating, player_pos, stones, algorithm_mode, output_content, cost_list, final_cost, timeout_reached
    screen.fill("black")
    
    def notify_win():
        global is_running, is_paused, is_calculating, player_pos, stones
        nonlocal move_index
        state=True
        while state:
            WIN_MOUSE_POS=pygame.mouse.get_pos()
           
            MENU_BUTTON=Button(image=None,pos=(Screen_Width//2+120,Screen_Height//2+70)
                            ,text_input="MENU",font=get_font(30),base_color="White",hovering_color="Green")
            for button in [MENU_BUTTON]:
                button.changeColor(WIN_MOUSE_POS)
                button.update(screen)
        
            flash_rect('YOU WIN!',60,'White','Yellow')
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type==pygame.MOUSEBUTTONDOWN:
                    if MENU_BUTTON.checkForInput(WIN_MOUSE_POS):
                        main_menu()
            pygame.display.update()
    
    def notify_timeout():
        global is_running, is_paused, is_calculating, player_pos, stones
        nonlocal move_index
        state=True
        while state:
            WIN_MOUSE_POS=pygame.mouse.get_pos()
            MENU_BUTTON=Button(image=None,pos=(Screen_Width//2+120,Screen_Height//2+70)
                            ,text_input="MENU",font=get_font(30),base_color="White",hovering_color="Green")
            
            MENU_BUTTON.changeColor(WIN_MOUSE_POS)
            MENU_BUTTON.update(screen)
        
            flash_rect('TIMEOUT!',60,'White','Yellow')
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type==pygame.MOUSEBUTTONDOWN:
                    if MENU_BUTTON.checkForInput(WIN_MOUSE_POS):
                        main_menu()
            pygame.display.update()
            
    # Reset để chạy map
    player_pos=[0,0]
    stones.clear()
    switches_pos.clear()
    cost_list = [0]
    graph_way_nodes.clear()
    
    render_map(board) 
    render_buttons()
    render_algorithm_name(support_function.algorithm_mode)
    pygame.display.update()

    # Show "Calculating" while starting calculations
    is_calculating = True 
    calculation_thread = threading.Thread(target=calculation_animation)
    calculation_thread.start()
    
    #Set timeout thread
    support_function.timeout_reached = False
    timeout_duration = 20  # 1 minutes
    timeout_thread = threading.Thread(target=time_limit_check, args=(timeout_duration,))
    timeout_thread.start()

    # Initialize state
    initial_state = {
        'player_pos': player_pos.copy(),
        'stones': stones.copy()
    }
    
    # Run algorithm
    problem = support_function.ProblemAlgorithm(initial_state, board, switches_pos, graph_way_nodes)

    output_content.clear()
    ucs_go=uniform_cost_search(problem, output_content)
    bfs_go=bfs_search(problem, output_content)
    dfs_go=dfs_search(problem, output_content)
    a_star_go=a_star_search(problem, output_content)
    print("finish")
    
    for i in [ucs_go, bfs_go, dfs_go, a_star_go]:
        if i is None and support_function.timeout_event.is_set():
            timeout_thread.join()
            is_calculating = False  
            support_function.timeout_event.clear()
            calculation_thread.join()
            notify_timeout()
    
    stop_timeout_event.set()
    timeout_thread.join()
    stop_timeout_event.clear()
    save_output_to_file(current_map_path, output_content)
    
    if support_function.algorithm_mode=='UCS':
        way_player_go=ucs_go
    elif support_function.algorithm_mode=='BFS':
        way_player_go=bfs_go
    elif support_function.algorithm_mode=='DFS':
        way_player_go=dfs_go
    elif support_function.algorithm_mode=='A*':
        way_player_go=a_star_go

    is_calculating = False  
    calculation_thread.join() 
    
    if way_player_go == None:
        notify_timeout()
        
    
    # Delete calculating
    pygame.draw.rect(screen, (0, 0, 0), (Screen_Width - 150, 20, 145, 30))  

    # Update text to "Finish"
    render_status_text("Finish")
    pygame.display.update()

    # Game control variables
    move_index = 0
    is_running = True
    is_paused = True

    # Main game loop
    while is_running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if Start_Button_Position[0] <= mouse_pos[0] <= Start_Button_Position[0] + Button_Witdh and \
                    Start_Button_Position[1] <= mouse_pos[1] <= Start_Button_Position[1] + Button_Height:
                    is_paused = False
                elif Pause_Button_Position[0] <= mouse_pos[0] <= Pause_Button_Position[0] + Button_Witdh and \
                    Pause_Button_Position[1] <= mouse_pos[1] <= Pause_Button_Position[1] + Button_Height:
                    is_paused = True
                elif Reset_Button_Position[0] <= mouse_pos[0] <= Reset_Button_Position[0] + Button_Witdh and \
                    Reset_Button_Position[1] <= mouse_pos[1] <= Reset_Button_Position[1] + Button_Height:
                    move_index = 0
                    player_pos = initial_state['player_pos'].copy()
                    stones = initial_state['stones'].copy()
                    is_paused = True
                    render_map(board)
                    render_buttons()
                    render_algorithm_name(support_function.algorithm_mode)
                    pygame.display.update()
                elif Exit_Button_Position[0] <= mouse_pos[0] <= Exit_Button_Position[0] + Button_Witdh and \
                    Exit_Button_Position[1] <= mouse_pos[1] <= Exit_Button_Position[1] + Button_Height:
                    main_menu()  # Quay lại menu chính
                    return

        if is_win():
            notify_win()
        if not is_paused and move_index < len(way_player_go):
            movement(board, way_player_go[move_index])
            
            move_index += 1

        if not way_player_go:
            text = font.render("THERE IS NO WAY TO WIN!", True, (255, 255, 255))
            text_rect = text.get_rect(center=(Screen_Width // 2, Screen_Height // 2))
            screen.blit(text, text_rect)

        if is_calculating:
            render_status_text("Calculating")
        else:
            render_status_text("Finish")

        render_buttons()
        render_cost_step(move_index, cost_list)  # Cập nhật chi phí
        pygame.display.update()

    pygame.quit()

current_map_directory=input_board_path#default is standard
current_map_path='input-01.txt' #input01 is default input
map=get_board(os.path.join(current_map_directory,current_map_path))
#Create MENU
class Button():
    def __init__(self, image, pos, text_input, font, base_color, hovering_color):
        self.image = image
        self.x_pos = pos[0]
        self.y_pos = pos[1]
        self.font = font
        self.base_color, self.hovering_color = base_color, hovering_color
        self.text_input = text_input
        self.text = self.font.render(self.text_input, True, self.base_color)
        if self.image is None:
            self.image = self.text
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

    def update(self, screen):
        if self.image is not None:
            screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

    def checkForInput(self, position):
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            return True
        return False

    def changeColor(self, position):
        # Thay đổi màu thành đen khi rê chuột qua
        if self.checkForInput(position):
            self.text = self.font.render(self.text_input, True, (0, 0, 0))  # Màu đen khi rê chuột
        else:
            self.text = self.font.render(self.text_input, True, self.base_color)

BG = pygame.image.load("Assets/Background.png")
def get_font(size): # Returns Press-Start-2P in the desired size
    return pygame.font.Font("Assets/font.ttf", size)

def getFilesName(mapDirectory):
    mapArr=[]
    for file_name in os.listdir(mapDirectory):
        if file_name.endswith('.txt'):
            mapArr.append(file_name)
    return mapArr

def map_choose():
    global map, current_map_path
    while True:
        screen.fill("black")
        screen.blit(BG, (0, 0))
        MAP_MOUSE_POS = pygame.mouse.get_pos()
        
        MAP_TEXT = get_font(40).render("Please Choose Map", True, "Black")
        MAP_RECT = MAP_TEXT.get_rect(center=(Screen_Width // 2, 100))
        screen.blit(MAP_TEXT, MAP_RECT)

        # Lấy danh sách các map
        mapArr = getFilesName(current_map_directory)

        # Tính toán vị trí y bắt đầu và khoảng cách giữa các nút
        y_position = 200  # Vị trí bắt đầu theo trục Y
        y_gap = 40  # Khoảng cách giữa các nút theo trục Y

        map_button_list = []

        # Tạo các nút map và căn giữa theo chiều ngang
        for index, mapName in enumerate(mapArr):
            mapText = f"MAP{index + 1:02d}"
            MAP_NAME_BUTTON = Button(
                image=None,
                pos=(Screen_Width // 2, y_position),  # Căn giữa theo trục X
                text_input=mapText,
                font=get_font(20),
                base_color="White",
                hovering_color="Green"
            )
            map_button_list.append(MAP_NAME_BUTTON)
            y_position += y_gap  # Cập nhật vị trí y cho nút tiếp theo

        # Hiển thị các nút map
        for button in map_button_list:
            button.changeColor(MAP_MOUSE_POS)
            button.update(screen)

        # Xử lý sự kiện
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for index, button in enumerate(map_button_list):
                    if button.checkForInput(MAP_MOUSE_POS):
                        current_map_path = mapArr[index]
                        map = get_board(os.path.join(current_map_directory, current_map_path))
                        algorithm_choose()  # Sau khi chọn map, tự động chuyển tới chọn thuật toán

        pygame.display.update()


def algorithm_choose():
    global algorithm_mode
    while True:
        screen.fill("black")
        screen.blit(BG, (0, 0))
        ALGORITHM_MOUSE_POS = pygame.mouse.get_pos()

        ALGORITHM_TEXT = get_font(40).render("Please Choose Algorithm", True, "Black")
        ALGORITHM_RECT = ALGORITHM_TEXT.get_rect(center=(Screen_Width // 2, 100))
        screen.blit(ALGORITHM_TEXT, ALGORITHM_RECT)

        UCS_BUTTON = Button(image=pygame.image.load("Assets/Rect.png"), pos=(Screen_Width // 2, 225), 
                            text_input="UCS", font=get_font(50), base_color="White", hovering_color="Green")
        BFS_BUTTON = Button(image=pygame.image.load("Assets/Rect.png"), pos=(Screen_Width // 2, 350), 
                            text_input="BFS", font=get_font(50), base_color="White", hovering_color="Green")
        DFS_BUTTON = Button(image=pygame.image.load("Assets/Rect.png"), pos=(Screen_Width // 2, 475), 
                            text_input="DFS", font=get_font(50), base_color="White", hovering_color="Green")
        A_STAR_BUTTON = Button(image=pygame.image.load("Assets/Rect.png"), pos=(Screen_Width // 2, 600), 
                               text_input="A*", font=get_font(50), base_color="White", hovering_color="Green")
        
        for button in [UCS_BUTTON, BFS_BUTTON, DFS_BUTTON, A_STAR_BUTTON]:
            button.changeColor(ALGORITHM_MOUSE_POS)
            button.update(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if UCS_BUTTON.checkForInput(ALGORITHM_MOUSE_POS):
                    support_function.algorithm_mode = "UCS"
                    game_loop(map)  # Tự động vào chơi sau khi chọn thuật toán
                if BFS_BUTTON.checkForInput(ALGORITHM_MOUSE_POS):
                    support_function.algorithm_mode = "BFS"
                    game_loop(map)  # Tự động vào chơi sau khi chọn thuật toán
                if DFS_BUTTON.checkForInput(ALGORITHM_MOUSE_POS):
                    support_function.algorithm_mode = "DFS"
                    game_loop(map)  # Tự động vào chơi sau khi chọn thuật toán
                if A_STAR_BUTTON.checkForInput(ALGORITHM_MOUSE_POS):
                    support_function.algorithm_mode = "A*"
                    game_loop(map)  # Tự động vào chơi sau khi chọn thuật toán

        pygame.display.update()

def main_menu():
    global map, current_map_path
    while True:
        screen.blit(BG, (0, 0))
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        
        # Hiển thị tiêu đề với màu đen
        MENU_TEXT = get_font(40).render("Ares's Adventure", True, (0, 0, 0))
        MENU_RECT = MENU_TEXT.get_rect(center=(Screen_Width // 2, 100))
        screen.blit(MENU_TEXT, MENU_RECT)
        MAP_BUTTON = Button(image=pygame.image.load("Assets/Rect.png"), pos=(Screen_Width // 2, 320), 
                            text_input="MAP", font=get_font(30), base_color="White", hovering_color="Green")
        QUIT_BUTTON = Button(image=pygame.image.load("Assets/Rect.png"), pos=(Screen_Width // 2, 420), 
                             text_input="QUIT", font=get_font(30), base_color="White", hovering_color="Green")
        
        # Hiển thị các nút
        for button in [MAP_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(screen)

        # Xử lý sự kiện nhấp chuột
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
              
                if MAP_BUTTON.checkForInput(MENU_MOUSE_POS):
                    map_choose()
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()
        
        pygame.display.update()
