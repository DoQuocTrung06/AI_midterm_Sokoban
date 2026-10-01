import time
import heapq
import random
from base_agent import BaseAgent

class AgentTeam1(BaseAgent):
    def __init__(self, player_id=1):
        super().__init__(player_id)
        self.actions = [(0, -1), (0, 1), (-1, 0), (1, 0)] # Lên, Xuống, Trái, Phải

        # THÊM TRÍ NHỚ CHO BOT
        self.last_pos = None
        self.stuck_count = 0
        
    def get_action(self, state, time_limit):
        start_time = time.perf_counter()
        safe_time_limit = (time_limit - 100) / 1000.0 # Dừng ở 900ms để đảm bảo không bị time out

        # ==========================================================
        # LOGIC CHỐNG KẸT (ANTI-STUCK / DEADLOCK BREAKER)
        # ==========================================================
        current_pos = state['p1'] if self.player_id == 1 else state['p2']
        
        if self.last_pos == current_pos:
            self.stuck_count += 1
        else:
            self.stuck_count = 0
            self.last_pos = current_pos
            
        # Nếu đứng im 2 turn liên tiếp -> Đang bị đâm nhau -> Đi lách ra chỗ khác
        if self.stuck_count >= 2:
            self.stuck_count = 0 # Reset lại bộ đếm
            valid_moves = []
            for dx, dy in self.actions:
                nr, nc = current_pos[0] + dx, current_pos[1] + dy
                # Bỏ check 'locked', giờ chỉ cần né tường cứng
                if (nr, nc) not in state['walls']:
                    valid_moves.append((dx, dy))
                    
            if valid_moves:
                fallback_action = random.choice(valid_moves)
                print(f"[P1-Blue] BỊ KẸT! Tự động lách sang: {fallback_action}")
                return fallback_action
        # ==========================================================
        
        best_first_action = (0, 0)
        max_depth_reached = 0
        
        # Iterative Deepening Search (IDS)
        for max_depth in range(1, 50):
            # A* Search với giới hạn độ sâu
            action, timeout = self.a_star_search(state, max_depth, start_time, safe_time_limit)
            
            if action is not None:
                best_first_action = action
                
            if timeout:
                # Nếu hết giờ trong quá trình tìm, break và lấy best_first_action của depth trước đó
                break

            max_depth_reached = max_depth
                
        return best_first_action

    def is_corner_deadlock(self, r, c, state):
        if (r, c) in state['goals']: 
            return False # Bị kẹt nhưng kẹt trên đích thì lại là lợi thế (An toàn tuyệt đối)
        wall_v = (r-1, c) in state['walls'] or (r+1, c) in state['walls']
        wall_h = (r, c-1) in state['walls'] or (r, c+1) in state['walls']
        return wall_v and wall_h

    def a_star_search(self, start_state, max_depth, start_time, time_limit):
        # Hàng đợi ưu tiên: (f_cost, g_cost, depth, agent_pos, boxes_dict, first_action)
        frontier = []
        start_pos = start_state['p1'] if self.player_id == 1 else start_state['p2']
        boxes = start_state['boxes']
        
        start_h = self.calculate_heuristic(start_pos, boxes, start_state)
        # Lưu boxes dưới dạng tuple (r, c, owner) để băm (hash) cho set
        boxes_tuple = tuple(sorted([(r, c, o) for (r, c), o in boxes.items()]))
        
        heapq.heappush(frontier, (start_h, 0, 0, start_pos, boxes_tuple, None))
        visited = set()
        
        best_action = None
        best_h = float('inf')
        
        while frontier:
            # Kiểm tra thời gian ngắt (IDS break)
            if time.perf_counter() - start_time > time_limit:
                return best_action, True
                
            f_cost, g_cost, depth, current_pos, current_boxes_tuple, first_action = heapq.heappop(frontier)
            
            # Trạng thái hiện tại
            state_hash = (current_pos, current_boxes_tuple)
            if state_hash in visited:
                continue
            visited.add(state_hash)
            
            # Chuyển boxes tuple về dict để tính toán
            current_boxes = {(r, c): o for r, c, o in current_boxes_tuple}
            current_h = self.calculate_heuristic(current_pos, current_boxes, start_state)
            
            # Lưu lại trạng thái tốt nhất phòng trường hợp time_out hoặc chạm max_depth
            if first_action is not None and current_h < best_h:
                best_h = current_h
                best_action = first_action
                
            if depth >= max_depth:
                continue
                
            # Tạo các trạng thái kế tiếp
            for action in self.actions:
                dx, dy = action
                nr, nc = current_pos[0] + dx, current_pos[1] + dy
                
                # Tránh tường và Bot đối phương (Bỏ check locked)
                enemy_pos = start_state['p2'] if self.player_id == 1 else start_state['p1']
                if (nr, nc) in start_state['walls'] or (nr, nc) == enemy_pos:
                    continue
                    
                new_boxes = current_boxes.copy()
                valid_move = True
                
                # Xử lý đẩy thùng
                if (nr, nc) in new_boxes:
                    nnr, nnc = nr + dx, nc + dy
                    # Kiểm tra sau lưng thùng có trống không
                    if (nnr, nnc) in start_state['walls'] or (nnr, nnc) in new_boxes or (nnr, nnc) == enemy_pos:
                        valid_move = False
                    else:
                        # Đẩy thùng
                        owner = new_boxes.pop((nr, nc))
                        new_boxes[(nnr, nnc)] = self.player_id # Đổi màu thùng
                        if self.is_corner_deadlock(nnr, nnc, start_state):
                            valid_move = False
                
                if valid_move:
                    next_boxes_tuple = tuple(sorted([(r, c, o) for (r, c), o in new_boxes.items()]))
                    next_h = self.calculate_heuristic((nr, nc), new_boxes, start_state)
                    
                    next_first_action = action if depth == 0 else first_action
                    
                    heapq.heappush(frontier, (g_cost + 1 + next_h, g_cost + 1, depth + 1, (nr, nc), next_boxes_tuple, next_first_action))
                    
        return best_action, False

    def calculate_heuristic(self, pos, boxes, state):
        """
        Đánh giá trạng thái: Càng nhỏ càng tốt.
        - Thưởng lớn nếu sở hữu nhiều thùng.
        - Phạt khoảng cách từ các thùng của mình đến đích gần nhất.
        - Phạt khoảng cách từ bot đến thùng trung lập.
        """
        score = 0
        my_boxes = 0
        enemy_boxes = 0
        
        # Chỉ tập trung vào những đích CHƯA bị quân ta chiếm (Bao gồm đích trống và đích địch đang chiếm)
        target_goals = [g for g in state['goals'] if g not in boxes or boxes[g] != self.player_id]
        
        for (r, c), owner in boxes.items():
            # NẾU ĐẨY VÀO ĐÍCH -> THƯỞNG CỰC LỚN ĐỂ ƯU TIÊN DỨT ĐIỂM!
            if (r, c) in state['goals']:
                if owner == self.player_id:
                    score -= 2000  # Thưởng 2000 điểm
                    my_boxes += 1
                    continue # Của mình rồi thì khỏi đẩy nữa, mặc kệ khoảng cách
                elif owner != 0:
                    score += 2000  # Phạt nếu địch đẩy vào đích
                    enemy_boxes += 1
                    # Cố tình KHÔNG dùng continue ở đây, để hàm bên dưới tính khoảng cách từ Bot ra để cướp
            
            min_dist_to_goal = min([abs(r - gr) + abs(c - gc) for gr, gc in target_goals], default=0)
            
            if owner == self.player_id:
                my_boxes += 1
                score += min_dist_to_goal * 2 # Thùng của mình thì muốn kéo lại gần đích
            elif owner != 0:
                enemy_boxes += 1
                score -= min_dist_to_goal # Thùng của địch thì muốn nó xa đích
            else:
                # Thùng trung lập: bot cố gắng tiếp cận
                dist_bot_to_box = abs(pos[0] - r) + abs(pos[1] - c)
                score += dist_bot_to_box * 0.5
                
        # Trừ đi số thùng sở hữu (càng nhiều càng âm -> càng tốt)
        score -= (my_boxes * 100)
        score += (enemy_boxes * 100)
        return score