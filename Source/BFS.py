from support_function import *

def bfs_search(problem, output_content):
    if timeout_event.is_set():  # Kiểm tra nếu hết thời gian
        print("Timeout in BFS")
        return None
    
    # Tạo luồng kiểm tra thời gian
    timeout_thread = threading.Thread(target=time_limit_check)
    timeout_thread.start()
    
    print('Calculating BFS...')
    start_node = Node(problem.initial_state)
    algorithm_name = 'BFS'

    queue = []  # Hàng đợi để duyệt các nút theo thứ tự BFS
    visited_nodes = set()  # Tập các nút đã được khám phá

    tracemalloc.start()  # Bắt đầu theo dõi bộ nhớ
    start_time = time.time()
    
    queue.append(start_node)
    
    generated_node_count = 0  # Đếm số lượng nút được tạo ra

    while queue:
        if timeout_event.is_set():  # Kiểm tra nếu hết thời gian
            stop_timeout_event.set()
            timeout_thread.join()
            stop_timeout_event.clear()
            timeout_event.clear()
            output_content.append(algorithm_name)
            output_content.append("Timeout")
            print("Timeout in BFS")
            return None
        
        current_node = queue.pop(0)  # Lấy nút đầu tiên từ hàng đợi

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

            # Kiểm tra nếu nút mới chưa được khám phá và chưa có trong hàng đợi
            if new_node not in visited_nodes and new_node not in queue:
                # Kiểm tra nếu trạng thái của nút con là mục tiêu
                if problem.goal_checking(new_node.state):
                    stop_timeout_event.set()
                    timeout_thread.join()
                    stop_timeout_event.clear()
                    timeout_event.clear()
                    return process_solution(new_node, start_time, start_node, algorithm_name, generated_node_count, problem, output_content)
                queue.append(new_node)
    
    return None
