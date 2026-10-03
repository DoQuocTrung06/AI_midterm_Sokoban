import heapq

def ucs(problem):
    frontier = []
    counter = 0 
    heapq.heappush(frontier, (0, counter, problem.start_state, []))
    
    visited = set()

    while frontier:
        cost, _, current_state, path = heapq.heappop(frontier)

        if problem.is_goal(current_state):
            return path, cost 
        if current_state not in visited:
            visited.add(current_state)

            for next_state, action, step_cost in problem.get_successors(current_state):
                if next_state not in visited:
                    counter += 1
                    new_cost = cost + step_cost
                    new_path = path + [action]
                    heapq.heappush(frontier, (new_cost, counter, next_state, new_path))
                    
    return None, 0 

def a_star(problem, heuristic_func):
    frontier = []
    counter = 0
    
    start_state = problem.start_state
    start_h = heuristic_func(start_state, problem)
    
    heapq.heappush(frontier, (start_h, 0, counter, start_state, []))
    
    visited = set()

    while frontier:
        f_cost, g_cost, _, current_state, path = heapq.heappop(frontier)

        if problem.is_goal(current_state):
            return path, g_cost 

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