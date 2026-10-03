import time
import heapq
import random
from AI_midterm_Sokoban.source.Task7.base_agent import BaseAgent

class AgentTeam2(BaseAgent):
    def __init__(self, player_id=2):
        super().__init__(player_id)
        self.actions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        self.last_pos = None
        self.stuck_count = 0
        
    def get_action(self, state, time_limit):
        start_time = time.perf_counter()
        safe_time_limit = (time_limit - 100) / 1000.0

        current_pos = state['p1'] if self.player_id == 1 else state['p2']
        
        if self.last_pos == current_pos:
            self.stuck_count += 1
        else:
            self.stuck_count = 0
            self.last_pos = current_pos
            
        if self.stuck_count >= 2:
            self.stuck_count = 0 
            valid_moves = []
            for dx, dy in self.actions:
                nr, nc = current_pos[0] + dx, current_pos[1] + dy
                if (nr, nc) not in state['walls']:
                    valid_moves.append((dx, dy))
                    
            if valid_moves:
                fallback_action = random.choice(valid_moves)
                return fallback_action
        best_action = (0, 0)
        
        for max_depth in range(1, 50):
            action, timeout = self.greedy_search(state, max_depth, start_time, safe_time_limit)
            if action is not None:
                best_action = action
            if timeout:
                break
                
        return best_action

    def is_corner_deadlock(self, r, c, state):
        if (r, c) in state['goals']: 
            return False
        wall_v = (r-1, c) in state['walls'] or (r+1, c) in state['walls']
        wall_h = (r, c-1) in state['walls'] or (r, c+1) in state['walls']
        return wall_v and wall_h

    def greedy_search(self, start_state, max_depth, start_time, time_limit):
        frontier = []
        start_pos = start_state['p1'] if self.player_id == 1 else start_state['p2']
        boxes = start_state['boxes']
        
        start_h = self.heuristic(start_pos, boxes, start_state)
        boxes_tuple = tuple(sorted([(r, c, o) for (r, c), o in boxes.items()]))
        
        heapq.heappush(frontier, (start_h, 0, start_pos, boxes_tuple, None))
        visited = set()
        
        best_a = None
        min_h = float('inf')
        
        while frontier:
            if time.perf_counter() - start_time > time_limit:
                return best_a, True
                
            h_cost, depth, current_pos, current_boxes_tuple, first_action = heapq.heappop(frontier)
            
            state_hash = (current_pos, current_boxes_tuple)
            if state_hash in visited:
                continue
            visited.add(state_hash)
            
            current_boxes = {(r, c): o for r, c, o in current_boxes_tuple}
            
            if first_action is not None and h_cost < min_h:
                min_h = h_cost
                best_a = first_action
                
            if depth >= max_depth:
                continue
                
            for action in self.actions:
                dx, dy = action
                nr, nc = current_pos[0] + dx, current_pos[1] + dy
                enemy_pos = start_state['p1'] if self.player_id == 2 else start_state['p2']
                
                if (nr, nc) in start_state['walls'] or (nr, nc) == enemy_pos:
                    continue
                    
                new_boxes = current_boxes.copy()
                valid = True
                
                if (nr, nc) in new_boxes:
                    nnr, nnc = nr + dx, nc + dy
                    if (nnr, nnc) in start_state['walls'] or (nnr, nnc) in new_boxes or (nnr, nnc) == enemy_pos:
                        valid = False
                    else:
                        new_boxes.pop((nr, nc))
                        new_boxes[(nnr, nnc)] = self.player_id
                        if self.is_corner_deadlock(nnr, nnc, start_state):
                            valid = False
                
                if valid:
                    next_boxes_tuple = tuple(sorted([(r, c, o) for (r, c), o in new_boxes.items()]))
                    next_h = self.heuristic((nr, nc), new_boxes, start_state)
                    nxt_a = action if depth == 0 else first_action
                    heapq.heappush(frontier, (next_h, depth + 1, (nr, nc), next_boxes_tuple, nxt_a))
                    
        return best_a, False

    def heuristic(self, pos, boxes, state):
        h = 0
        my_boxes = 0
        enemy_boxes = 0
        
        target_goals = [g for g in state['goals'] if g not in boxes or boxes[g] != self.player_id]
        
        for (r, c), owner in boxes.items():
            if (r, c) in state['goals']:
                if owner == self.player_id:
                    h -= 2000
                    my_boxes += 1
                    continue
                elif owner != 0:
                    h += 2000
                    enemy_boxes += 1
                    
            min_dist_to_goal = min([abs(r - gr) + abs(c - gc) for gr, gc in target_goals], default=0)
            
            if owner == self.player_id:
                my_boxes += 1
                h += min_dist_to_goal * 2
            elif owner != 0:
                enemy_boxes += 1
                h -= min_dist_to_goal
            else:
                dist_bot_to_box = abs(pos[0] - r) + abs(pos[1] - c)
                h += dist_bot_to_box * 0.5
                
        h -= (my_boxes * 100)
        h += (enemy_boxes * 100)
        
        return h