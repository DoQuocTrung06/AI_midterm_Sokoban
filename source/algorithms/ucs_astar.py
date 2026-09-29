import heapq
# 1. CLASS MÔ HÌNH HÓA DÀNH RIÊNG CHO AI (Tối ưu bằng Set và Tuple)
class SokobanProblem:
    def __init__(self, file_path):
        self.walls = set()
        self.targets = set()
        boxes = []
        self.start_agent = None

        # Đọc file map
        with open(file_path, 'r') as f:
            for y, line in enumerate(f.readlines()):
                for x, char in enumerate(line.strip('\n')):
                    if char == '%':
                        self.walls.add((x, y))
                    elif char == 'D':
                        self.targets.add((x, y))
                    elif char == 'B':
                        boxes.append((x, y))
                    elif char == 'A':
                        self.start_agent = (x, y)
                    elif char == 'C':
                        boxes.append((x, y))
                        self.targets.add((x, y))

        # Trạng thái ban đầu: (vị trí nhân vật, tuple các vị trí hộp)
        self.start_state = (self.start_agent, tuple(sorted(boxes)))

    def is_goal(self, state):
        _, boxes = state
        # Trạng thái đích khi tập hợp hộp khớp hoàn toàn với tập hợp đích
        return set(boxes) == self.targets

    def get_successors(self, state):
        agent_pos, boxes = state
        successors = []
        
        # 4 hành động hợp lệ theo yêu cầu
        actions = {'North': (0, -1), 'South': (0, 1), 'East': (1, 0), 'West': (-1, 0)}

        for action, (dx, dy) in actions.items():
            new_agent = (agent_pos[0] + dx, agent_pos[1] + dy)

            # Trường hợp đụng tường
            if new_agent in self.walls:
                continue

            # Trường hợp đụng hộp
            if new_agent in boxes:
                new_box = (new_agent[0] + dx, new_agent[1] + dy)
                
                # Kiểm tra xem hộp có bị đẩy vào tường hoặc hộp khác không
                if new_box in self.walls or new_box in boxes:
                    continue
                
                # Cập nhật danh sách hộp mới
                new_boxes = list(boxes)
                new_boxes[new_boxes.index(new_agent)] = new_box
                next_state = (new_agent, tuple(sorted(new_boxes)))
                successors.append((next_state, action, 1)) # 1 là cost cho mỗi bước đi
            
            # Trường hợp đường trống
            else:
                next_state = (new_agent, boxes)
                successors.append((next_state, action, 1))

        return successors
# 2. HÀM HEURISTIC VÀ KIỂM TRA BẾ TẮC
def chebyshev_distance(pos1, pos2):
    # Tính khoảng cách Chebyshev giữa 2 điểm
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

def is_deadlock(box, problem):
    # Nếu hộp đã vào đúng ô đích thì dù ở góc tường cũng không bị tính là bế tắc
    if box in problem.targets:
        return False
        
    x, y = box
    # Kiểm tra xem hộp có bị kẹt bởi tường theo trục ngang (bên trái hoặc bên phải) không
    blocked_horizontally = (x - 1, y) in problem.walls or (x + 1, y) in problem.walls
    # Kiểm tra xem hộp có bị kẹt bởi tường theo trục dọc (phía trên hoặc phía dưới) không
    blocked_vertically = (x, y - 1) in problem.walls or (x, y + 1) in problem.walls
    
    # Nếu bị kẹt CẢ ngang VÀ dọc (tạo thành góc vuông 90 độ) -> Chắc chắn Deadlock
    return blocked_horizontally and blocked_vertically

def calculate_heuristic(state, problem):
    _, boxes = state
    total_h = 0
    
    for box in boxes:
        if box in problem.targets:
            continue # Hộp đã vào đích, không cộng thêm cost
            
        # TÍCH HỢP DEADLOCK: Nếu phát hiện bất kỳ hộp nào bị kẹt góc, trả về vô cực
        if is_deadlock(box, problem):
            return float('inf')
            
        min_dist = float('inf')
        for target in problem.targets:
            dist = chebyshev_distance(box, target)
            if dist < min_dist:
                min_dist = dist
        total_h += min_dist
        
    return total_h
# 3. THUẬT TOÁN TÌM KIẾM
def ucs(problem):
    # Queue lưu: (chi_phí_tổng, biến_đếm, trạng_thái_hiện_tại, danh_sách_hành_động)
    frontier = []
    counter = 0 
    heapq.heappush(frontier, (0, counter, problem.start_state, []))
    
    visited = set()

    while frontier:
        cost, _, current_state, path = heapq.heappop(frontier)

        if problem.is_goal(current_state):
            return path, cost # Trả về list of actions và total cost

        if current_state not in visited:
            visited.add(current_state)

            for next_state, action, step_cost in problem.get_successors(current_state):
                if next_state not in visited:
                    counter += 1
                    new_cost = cost + step_cost
                    new_path = path + [action]
                    heapq.heappush(frontier, (new_cost, counter, next_state, new_path))
                    
    return None, 0 # Không tìm thấy đường

def a_star(problem, heuristic_func):
    frontier = []
    counter = 0
    
    start_state = problem.start_state
    start_h = heuristic_func(start_state, problem)
    
    # Queue lưu: (f_cost, g_cost, biến_đếm, trạng_thái, danh_sách_hành_động)
    heapq.heappush(frontier, (start_h, 0, counter, start_state, []))
    
    visited = set()

    while frontier:
        f_cost, g_cost, _, current_state, path = heapq.heappop(frontier)

        if problem.is_goal(current_state):
            return path, g_cost # Trả về list of actions và total cost[cite: 1]

        if current_state not in visited:
            visited.add(current_state)

            for next_state, action, step_cost in problem.get_successors(current_state):
                if next_state not in visited:
                    counter += 1
                    new_g = g_cost + step_cost
                    new_h = heuristic_func(next_state, problem)
                    new_f = new_g + new_h
                    new_path = path + [action]
                    
                    heapq.heappush(frontier, (new_f, new_g, counter, next_state, new_path))

    return None, 0
