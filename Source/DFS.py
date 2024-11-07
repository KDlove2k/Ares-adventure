from support_function import *

def dfs_search(problem, output_content):
    if timeout_event.is_set():  # Kiểm tra nếu hết thời gian
        print("Timeout in DFS")
        return None
    
    # Tạo luồng kiểm tra thời gian
    timeout_thread = threading.Thread(target=time_limit_check)
    timeout_thread.start()
    
    print('Calculating DFS...')
    start_node = Node(problem.initial_state)
    algorithm_name = 'DFS'

    stack = []  # Sử dụng ngăn xếp để lưu trữ các nút theo thứ tự DFS
    visited_nodes = set()  # Tập hợp các nút đã được khám phá

    tracemalloc.start()  # Bắt đầu theo dõi bộ nhớ
    start_time = time.time()
    
    stack.append(start_node)
    
    generated_node_count = 0  # Đếm số lượng nút được tạo ra

    while stack:
        if timeout_event.is_set():  # Kiểm tra nếu hết thời gian
            stop_timeout_event.set()
            timeout_thread.join()
            stop_timeout_event.clear()
            timeout_event.clear()
            output_content.append(algorithm_name)
            output_content.append("Timeout")
            print("Timeout in DFS")
            return None
        
        current_node = stack.pop()  # Lấy nút cuối cùng từ ngăn xếp (LIFO)

        # Kiểm tra nếu trạng thái của nút hiện tại là mục tiêu
        if problem.goal_checking(current_node.state):
            stop_timeout_event.set()
            timeout_thread.join()
            stop_timeout_event.clear()
            timeout_event.clear()
            return process_solution(current_node, start_time, start_node, algorithm_name, generated_node_count, problem, output_content)
        
        visited_nodes.add(current_node)

        # Duyệt qua các hành động có thể thực hiện từ trạng thái hiện tại
        for action in problem.actions(current_node.state):
            new_node = child_node_create(problem, current_node, action)
            generated_node_count += 1

            # Kiểm tra nếu nút mới chưa được khám phá và chưa có trong ngăn xếp
            if new_node not in visited_nodes and new_node not in stack:
                # Kiểm tra nếu trạng thái của nút con là mục tiêu
                if problem.goal_checking(new_node.state):
                    stop_timeout_event.set()
                    timeout_thread.join()
                    stop_timeout_event.clear()
                    timeout_event.clear()
                    return process_solution(new_node, start_time, start_node, algorithm_name, generated_node_count, problem, output_content)
                stack.append(new_node)
    
    return None
