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