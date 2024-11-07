import os
import time
import tracemalloc# theo dõi bộ nhớ đang sử dụng 
import threading
import heapq




algorithm_mode="A*" #A* là mặt định
final_cost=[]

#Timeout flag
timeout_event = threading.Event() #để đánh dấu khi hết thời gian chờ. Event có hai trạng thái: "set" và "clear".
stop_timeout_event = threading.Event() #để ngừng ngay lập tức luồng kiểm tra thời gian khi cần.
timeout_duration = 15  # 15 seconds

def time_limit_check():#để thực hiện việc kiểm tra thời gian chờ.
    print('time thread start')
    for _ in range(timeout_duration):
        if stop_timeout_event.is_set():
            print('Timeout thread stopped immediately')
            return  # Thoát ngay khi cờ dừng được bật
        time.sleep(1)
    print('reach timeout')
    timeout_event.set()
    

class Node:
    def __init__(self, state, parent=None, action=None, cost=0, heuristic=0, depth=0):
        self.state = state
        self.parent = parent # Nút cha của nút hiện tại
        self.action = action #Hành động đã thực hiện để chuyển từ parent sang trạng thái hiện tại.
        self.cost = cost     #Chi phí để đạt đến nút hiện tại từ trạng thái bắt đầu (g(n)). mặc định 0                  
        self.heuristic = heuristic      #   Giá trị heuristic của nút hiện tại (h(n)).                     
        self.f = self.cost + self.heuristic     # f(n) = g(n) + h(n) #Đây là chi phí ước tính từ nút hiện tại đến trạng thái mục tiêu.
        self.depth = depth
        
    
    def __lt__(self, other):
        return self.f < other.f

    def __eq__(self, other):
        return isinstance(other, Node) and self.state == other.state

    # Allow the Node object to be used as a key in a dict
    def __hash__(self):
        return hash((
            tuple(self.state['player_pos']),
            frozenset(self.state['stones'].items())
        ))


def distance_two_point(pos1, pos2):#tính toán khoảng cách Manhattan giữa hai điểm pos1 và pos2 trong một không gian lưới hai chiều.
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

class ProblemAlgorithm:
    def __init__(self, initial_state, board, switches_position, way_action_and_nodes):
        self.initial_state = initial_state          
        self.board = board 
        self.switches_position = switches_position# vị trí mục tiêu
        self.way_action_and_nodes = way_action_and_nodes # những cái nút mà người chơi tại vị trí đó có thể đi

    
    def goal_checking(self, state):
        stones = state['stones']
        return all(stone in self.switches_position for stone in stones)


    def actions(self, state):#actions trả về danh sách các hành động hợp lệ từ trạng thái hiện tại
        player_position, stones = state['player_pos'], state['stones']
        actions = self.way_action_and_nodes[tuple(player_position)]

        valid_actions = [] # tạo mảng hành động hợp lệ 

       
        for action in actions:
            new_stone_positions = stones.copy()
            is_valid = True

            for stone_position in new_stone_positions:
                if tuple(action) == stone_position:    
                    new_stone_position = list(stone_position)

                    #đẩy cục đá theo các hướng
                    # Push up
                    if player_position[0] == stone_position[0] and player_position[1] > stone_position[1]:
                        new_stone_position[1] -= 1

                    # Push down
                    elif player_position[0] == stone_position[0] and player_position[1] < stone_position[1]:
                        new_stone_position[1] += 1

                    # Push left
                    elif player_position[0] > stone_position[0] and player_position[1] == stone_position[1]:
                        new_stone_position[0] -= 1

                    # Push right
                    elif player_position[0] < stone_position[0] and player_position[1] == stone_position[1]:
                        new_stone_position[0] += 1

                    #kiểm tra đẩy đá vào tường hay có hai cục đá 
                    if self.board[new_stone_position[1]][new_stone_position[0]] == '#' or (tuple(new_stone_position) in stones):
                        is_valid = False
                        break

            if is_valid:
                valid_actions.append(action)

        return valid_actions
    

    def heuristic_estimate_cost(self, state):#tính toán chi phí heuristic (ước lượng chi phí còn lại) từ trạng thái hiện tại state đến trạng thái mục tiêu:
        stones = list(state['stones'].keys())
        switches = self.switches_position 
        total_cost = 0

        for stone in stones:
            stone_weight = state['stones'][stone]
            
            min_cost = min(distance_two_point(stone, switch) * stone_weight for switch in switches)
            
            total_cost += min_cost

        return total_cost
#để truy ngược lại đường đi từ trạng thái mục tiêu đến trạng thái ban đầu, tạo thành một danh sách các hành động dẫn đến giải pháp.
def solution_reverse_way(node):
    path = [] #anh sách rỗng path để lưu trữ các hành động.
    while node.parent is not None:
        path.append(node.action)
        node = node.parent
    path.reverse()# đảo ngược lại để tìm từ đầu đến mục tiêu 
    return path

# Tạo ra chuỗi kí tự in vào outpuy
def generate_action_string(path, problem):
    action_string = []
    state = problem.initial_state

    for action in path:
        player_position, stones = state['player_pos'], state['stones']

        # nếu là một hành động đẩy
        if tuple(action) in stones:
            stone_position = action
            if player_position[0] == stone_position[0] and player_position[1] > stone_position[1]:
                action_string.append('U')
            elif player_position[0] == stone_position[0] and player_position[1] < stone_position[1]:
                action_string.append('D')
            elif player_position[0] > stone_position[0] and player_position[1] == stone_position[1]:
                action_string.append('L')
            elif player_position[0] < stone_position[0] and player_position[1] == stone_position[1]:
                action_string.append('R')
        else:
            if player_position[0] == action[0] and player_position[1] > action[1]:
                action_string.append('u')
            elif player_position[0] == action[0] and player_position[1] < action[1]:
                action_string.append('d')
            elif player_position[0] > action[0] and player_position[1] == action[1]:
                action_string.append('l')
            elif player_position[0] < action[0] and player_position[1] == action[1]:
                action_string.append('r')

        # Cập nhật state cho hành động tiếp theo
        state = child_node_create(problem, Node(state), action).state

    return action_string

# Calculate total weight in final step
def calculate_total_weight(solution_path, problem):
    total_weight = 0
    state = problem.initial_state

    for action in solution_path:
        player_position, stones = state.get('player_pos'), state.get('stones')

        # Kiểm tra xem action có liên quan đến việc đẩy đá
        stone_weight = stones.get(tuple(action))
        if stone_weight:
            total_weight += stone_weight

        # Cập nhật trạng thái mới sau hành động
        state = child_node_create(problem, Node(state), action).state

    return total_weight

def save_output_to_file(input_file_name, output_content):
    #  Trích xuất hậu tố từ tên tệp đầu vào ví dụ file input-01.txt thì sẽ in vào file output-01.txt
    file_suffix = os.path.splitext(os.path.basename(input_file_name))[0].replace("input-", "")
    output_file_name = f"output-{file_suffix}.txt"
    
      # Đảm bảo thư mục đầu ra tồn tại
    os.makedirs("output", exist_ok=True)
    
    # dường dẫn dầy đủ cho tệp đầu ra
    output_file_path = os.path.join("output", output_file_name)
    
    # Viết kết quả vào file output
    with open(output_file_path, 'w') as file:
        for string in output_content:
            file.write(string+'\n')



def child_node_create(problem, node, action, use_heuristic=False):
    #Đặt cost mặc định là 1. Đây là chi phí để di chuyển một bước.
    cost = 1

    player_position, stones = node.state['player_pos'], node.state['stones']
    new_stone_positions = stones.copy()
    
    if not use_heuristic:
        heuristic = 0
    else:
        heuristic = problem.heuristic_estimate_cost(node.state)

    for stone in stones:
        if tuple(action) == stone:
            cost = stones[stone] 
            new_stone_position = list(stone)

            # Push up
            if player_position[0] == stone[0] and player_position[1] > stone[1]:
                new_stone_position[1] -= 1

            # Push down
            elif player_position[0] == stone[0] and player_position[1] < stone[1]:
                new_stone_position[1] += 1

            # Push left
            elif player_position[0] > stone[0] and player_position[1] == stone[1]:
                new_stone_position[0] -= 1

            # Push right
            elif player_position[0] < stone[0] and player_position[1] == stone[1]:
                new_stone_position[0] += 1
            
            # Cập nhật vị trí viên đá trong trạng thái mới
            del new_stone_positions[stone]                    # xóa vị trí cũ
            new_stone_positions[tuple(new_stone_position)] = cost  # thêm vị trí mới
    

    child_state = {
        'player_pos': action,
        'stones': new_stone_positions
    }

    return Node(child_state, node, action, cost + node.cost, heuristic)


        
cost_list = [0]

#tính toán tổng trọng lượng của các viên đá mà người chơi đã đẩy trong quá trình thực hiện đường đi 
def caculating_total_weight_pushed(solution_path, start_node, cost_list=None):
    if cost_list is None:
        cost_list = [0]
        
    total_weight_pushed = 0
    total_weight_save = 0
    
    state = start_node.state.copy()
    stone_positions = state['stones'].copy()

    for action in solution_path:
        player_position = state['player_pos']

        # Kiểm tra xem hành động hiện tại có phải là đẩy viên đá không
        stone_weight = stone_positions.get(tuple(action))
        if stone_weight:
            total_weight_pushed += stone_weight
            total_weight_save += stone_weight + 1
            cost_list.append(total_weight_save)
            
            # Tính toán vị trí mới của viên đá sau khi đẩy
            new_stone_position = list(action)
            if player_position[0] == new_stone_position[0] and player_position[1] > new_stone_position[1]:
                new_stone_position[1] -= 1
            elif player_position[0] == new_stone_position[0] and player_position[1] < new_stone_position[1]:
                new_stone_position[1] += 1
            elif player_position[0] > new_stone_position[0] and player_position[1] == new_stone_position[1]:
                new_stone_position[0] -= 1
            elif player_position[0] < new_stone_position[0] and player_position[1] == new_stone_position[1]:
                new_stone_position[0] += 1

            # Cập nhật vị trí viên đá
            stone_positions[tuple(new_stone_position)] = stone_positions.pop(tuple(action))
        else:
            # Nếu chỉ là di chuyển, cộng chi phí di chuyển vào tổng
            total_weight_save += 1
            cost_list.append(total_weight_save)

        # Cập nhật vị trí của người chơi
        state['player_pos'] = tuple(action)

    return total_weight_pushed, cost_list



def process_solution(node, start_time, start_node, algorithm_name, nodes_generated, problem, output_content):
    global final_cost, cost_list
    
    solution_path = solution_reverse_way(node)
    
    # Kết thúc và ghi nhận thời gian, bộ nhớ
    end_time = time.time()
    current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    num_steps = len(solution_path)
    total_time_ms = (end_time - start_time) * 1000  # Thời gian thực thi bằng ms
    peak_memory_mb = peak_memory / (1024 * 1024)  # Bộ nhớ tối đa sử dụng tính bằng MB
    
    # Tính tổng trọng lượng các viên đá bị đẩy trong quá trình giải
    total_weight_pushed = caculating_total_weight_pushed(solution_path, start_node)
    
    # Lưu chi phí cuối cùng để dùng cho các mục đích khác nếu cần
    final_cost = cost_list.copy()
    
    # Thêm thông tin vào output_content
    output_content.append(algorithm_name)
    output_content.append(f"Steps: {num_steps}, Weight: {total_weight_pushed[0]}, Node: {nodes_generated}, Time (ms): {total_time_ms:.2f}, Memory (MB): {peak_memory_mb:.2f}")
    output_content.append(''.join(generate_action_string(solution_path, problem)))
    
    # Reset cost_list để chuẩn bị cho lần gọi hàm tiếp theo
    cost_list = [0]
    
    return solution_path


