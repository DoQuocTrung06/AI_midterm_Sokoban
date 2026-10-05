import heapq
import time

class SearchStats:
    def __init__(self):
        self.nodes_expanded = 0    
        self.nodes_generated = 0   
        self.execution_time = 0.0  
        self.max_memory = 0

def ucs(problem, stats=None):
    frontier = []
    counter = 0 
    heapq.heappush(frontier, (0, counter, problem.start_state, []))
    
    visited = set()

    if stats:
        start_time = time.time()
        stats.nodes_generated += 1

    while frontier:
        if stats and len(frontier) > stats.max_memory:
            stats.max_memory = len(frontier)

        cost, _, current_state, path = heapq.heappop(frontier)

        if problem.is_goal(current_state):
            if stats:
                stats.execution_time = time.time() - start_time
            return path, cost

        if current_state not in visited:
            visited.add(current_state)
            
            if stats:
                stats.nodes_expanded += 1

            for next_state, action, step_cost in problem.get_successors(current_state):
                if next_state not in visited:
                    counter += 1
                    new_cost = cost + step_cost
                    new_path = path + [action]
                    heapq.heappush(frontier, (new_cost, counter, next_state, new_path))
                    
                    if stats:
                        stats.nodes_generated += 1

    if stats:
        stats.execution_time = time.time() - start_time
    return None, 0 

def a_star(problem, heuristic_func, stats=None):
    frontier = []
    counter = 0
    
    start_state = problem.start_state
    start_h = heuristic_func(start_state, problem)
    
    heapq.heappush(frontier, (start_h, 0, counter, start_state, []))
    
    visited = set()
    if stats:
        start_time = time.time()
        stats.nodes_generated += 1

    while frontier:
        if stats and len(frontier) > stats.max_memory:
            stats.max_memory = len(frontier)

        f_cost, g_cost, _, current_state, path = heapq.heappop(frontier)

        if problem.is_goal(current_state):
            if stats:
                stats.execution_time = time.time() - start_time
            return path, g_cost

        if current_state not in visited:
            visited.add(current_state)
            
            if stats:
                stats.nodes_expanded += 1

            for next_state, action, step_cost in problem.get_successors(current_state):
                if next_state not in visited:
                    counter += 1
                    new_g = g_cost + step_cost
                    new_h = heuristic_func(next_state, problem)
                    new_f = new_g + new_h
                    new_path = path + [action]
                    
                    heapq.heappush(frontier, (new_f, new_g, counter, next_state, new_path))
                    
                    if stats:
                        stats.nodes_generated += 1

    if stats:
        stats.execution_time = time.time() - start_time
    return None, 0