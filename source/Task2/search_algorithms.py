import heapq
import time

class SearchStats:
    def __init__(self):
        self.expanded = 0
        self.generated = 0
        self.max_frontier = 0
        self.max_explored = 0
        self.time_s = 0.0
        self.timed_out = False

def ucs(problem, stats=None, time_limit=None):
    start_time = time.perf_counter()
    frontier = []
    counter = 0 
    heapq.heappush(frontier, (0, counter, problem.start_state, []))
    if stats:
        stats.generated = 1
        stats.max_frontier = 1
    
    visited = set()

    while frontier:
        if time_limit is not None and time.perf_counter() - start_time > time_limit:
            if stats:
                stats.timed_out = True
            break

        cost, _, current_state, path = heapq.heappop(frontier)

        if problem.is_goal(current_state):
            if stats:
                stats.time_s = time.perf_counter() - start_time
            return path, cost 
        if current_state not in visited:
            visited.add(current_state)
            if stats:
                stats.expanded += 1
                stats.max_explored = max(stats.max_explored, len(visited))

            for next_state, action, step_cost in problem.get_successors(current_state):
                if next_state not in visited:
                    counter += 1
                    new_cost = cost + step_cost
                    new_path = path + [action]
                    heapq.heappush(frontier, (new_cost, counter, next_state, new_path))
                    if stats:
                        stats.generated += 1
            if stats:
                stats.max_frontier = max(stats.max_frontier, len(frontier))
                    
    if stats:
        stats.time_s = time.perf_counter() - start_time
    return None, 0 

def a_star(problem, heuristic_func, stats=None, time_limit=None):
    start_time = time.perf_counter()
    frontier = []
    counter = 0
    
    start_state = problem.start_state
    start_h = heuristic_func(start_state, problem)
    
    heapq.heappush(frontier, (start_h, 0, counter, start_state, []))
    if stats:
        stats.generated = 1
        stats.max_frontier = 1
    
    visited = set()

    while frontier:
        if time_limit is not None and time.perf_counter() - start_time > time_limit:
            if stats:
                stats.timed_out = True
            break

        f_cost, g_cost, _, current_state, path = heapq.heappop(frontier)

        if problem.is_goal(current_state):
            if stats:
                stats.time_s = time.perf_counter() - start_time
            return path, g_cost 

        if current_state not in visited:
            visited.add(current_state)
            if stats:
                stats.expanded += 1
                stats.max_explored = max(stats.max_explored, len(visited))

            for next_state, action, step_cost in problem.get_successors(current_state):
                if next_state not in visited:
                    counter += 1
                    new_g = g_cost + step_cost
                    new_h = heuristic_func(next_state, problem)
                    new_f = new_g + new_h
                    new_path = path + [action]
                    
                    heapq.heappush(frontier, (new_f, new_g, counter, next_state, new_path))
                    if stats:
                        stats.generated += 1
            if stats:
                stats.max_frontier = max(stats.max_frontier, len(frontier))

    if stats:
        stats.time_s = time.perf_counter() - start_time
    return None, 0