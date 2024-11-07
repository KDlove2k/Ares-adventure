from support_function import *

# Thuật toán Tìm kiếm Chi phí Thống nhất (Uniform Cost Search - UCS)
def uniform_cost_search(problem, output_content):
    if timeout_event.is_set():  # Kiểm tra nếu hết thời gian
        print("Timeout in UCS")
        return None
    
    # Tạo luồng kiểm tra thời gian
    timeout_thread = threading.Thread(target=time_limit_check)
    timeout_thread.start()
    
    print('Calculating UCS...')
    start_node = Node(problem.initial_state)
    algorithm_name = 'UCS'

    tracemalloc.start()  # Bắt đầu theo dõi bộ nhớ
    start_time = time.time()
    
    priority_queue = [(0, start_node)]  # Hàng đợi ưu tiên cho các nút theo chi phí
    visited_nodes = {start_node: (0, None)}  # Các nút đã được khám phá, với chi phí nhỏ nhất và nút trước đó

    generated_node_count = 0  # Đếm số lượng nút được tạo ra

    while priority_queue:
        if timeout_event.is_set():  # Kiểm tra nếu hết thời gian
            stop_timeout_event.set()
            timeout_thread.join()
            stop_timeout_event.clear()
            timeout_event.clear()
            output_content.append(algorithm_name)
            output_content.append("Timeout")
            print("Timeout in UCS")
            return None
        
        current_cost, current_node = heapq.heappop(priority_queue)

        # Kiểm tra nếu trạng thái của nút hiện tại là mục tiêu
        if problem.goal_checking(current_node.state):
            stop_timeout_event.set()
            timeout_thread.join()
            stop_timeout_event.clear()
            timeout_event.clear()
            return process_solution(current_node, start_time, start_node, algorithm_name, generated_node_count, problem, output_content)

        # Duyệt qua các hành động có thể thực hiện từ trạng thái hiện tại
        for action in problem.actions(current_node.state):
            new_node = child_node_create(problem, current_node, action)
            generated_node_count += 1

            # Kiểm tra nếu nút mới chưa được khám phá hoặc có chi phí thấp hơn
            if new_node not in visited_nodes or new_node.f < visited_nodes[new_node][0]:
                visited_nodes[new_node] = (new_node.f, current_node)
                heapq.heappush(priority_queue, (new_node.f, new_node))
    
    return None
