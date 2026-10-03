def chebyshev_distance(pos1, pos2):
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

def is_deadlock(box, problem):
    if box in problem.targets:
        return False
        
    x, y = box
    blocked_horizontally = (x - 1, y) in problem.walls or (x + 1, y) in problem.walls
    blocked_vertically = (x, y - 1) in problem.walls or (x, y + 1) in problem.walls
    
    return blocked_horizontally and blocked_vertically

def calculate_heuristic(state, problem):
    _, boxes = state
    total_h = 0
    
    for box in boxes:
        if box in problem.targets:
            continue 
            
        if is_deadlock(box, problem):
            return float('inf')
            
        min_dist = float('inf')
        for target in problem.targets:
            dist = chebyshev_distance(box, target)
            if dist < min_dist:
                min_dist = dist
        total_h += min_dist
        
    return total_h