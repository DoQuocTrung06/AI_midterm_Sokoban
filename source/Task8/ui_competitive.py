import pygame
import sys
import os
import time
import concurrent.futures

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from AI_midterm_Sokoban.source.Task7.agent_team1 import AgentTeam1
from AI_midterm_Sokoban.source.Task7.agent_team2 import AgentTeam2

TILE_SIZE = 48
PADDING_TILES = 1
COLOR_BG = (220, 210, 190)
COLOR_TEXT = (30, 30, 30)

class SokobanCompetitive:
    def __init__(self, map_path, max_turns):
        pygame.init()
        pygame.font.init()

        self._parse_map(map_path)
        
        self.screen_width = (self.board_cols + PADDING_TILES * 2) * TILE_SIZE
        self.screen_height = (self.board_rows + PADDING_TILES * 2) * TILE_SIZE + 80
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Sokoban - Cướp Thùng (Không Khóa)")
        
        self.font = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 28, bold=True)
        self.sprites = self._load_sprites()
        
        self.agent1 = AgentTeam1(player_id=1)
        self.agent2 = AgentTeam2(player_id=2)
        
        self.score_p1 = 0
        self.score_p2 = 0
        
        self.max_turns = max_turns
        self.current_turn = 0
        
        self.running = True
        self.is_paused = True
        self.clock = pygame.time.Clock()
        self.offset_x = PADDING_TILES * TILE_SIZE
        self.offset_y = PADDING_TILES * TILE_SIZE
        
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.ai_calculating = False
        self.future_p1 = None
        self.future_p2 = None

    def _parse_map(self, file_path):
        self.walls = set()
        self.goals = set()
        self.locked_boxes = set()
        
        self.p1_pos = None
        self.p2_pos = None
        self.boxes = {}

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.board_rows = len(lines)
        self.board_cols = max(len(line.rstrip('\n')) for line in lines)
        
        for r, line in enumerate(lines):
            for c, char in enumerate(list(line.rstrip('\n'))):
                if char == '%': self.walls.add((r, c))
                elif char == '1': self.p1_pos = (r, c)
                elif char == '2': self.p2_pos = (r, c)
                elif char == 'D': self.goals.add((r, c))
                elif char == 'B': self.boxes[(r, c)] = 0
                elif char == 'C': 
                    self.boxes[(r, c)] = 0
                    self.goals.add((r, c))

    def _load_sprites(self):
        base_dir = os.path.dirname(__file__)
        img_dir = os.path.join(base_dir, "..", "assets", "images")
        files = {
            'wall': "wall.png", 'floor': "floor.png", 'goal': "goal.png",
            'box': "box.png", 'box_on_goal': "box_on_goal.png", 'player': "player.png"
        }
        sprites = {}
        for key, filename in files.items():
            path = os.path.join(img_dir, filename)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                if key in ['wall', 'floor']:
                    img = img.subsurface(img.get_bounding_rect())
                sprites[key] = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        return sprites

    def tint_surface(self, surface, color):
        tinted = surface.copy()
        tinted.fill(color, special_flags=pygame.BLEND_MULT)
        return tinted

    def get_game_state(self):
        return {
            'p1': self.p1_pos, 'p2': self.p2_pos,
            'boxes': self.boxes.copy(),
            'goals': self.goals.copy(),
            'walls': self.walls.copy()
        }

    def is_board_deadlocked(self):
        if len(self.boxes) == 0: return False 
            
        for (r, c) in self.boxes.keys():
            up = (r-1, c) in self.walls
            down = (r+1, c) in self.walls
            left = (r, c-1) in self.walls
            right = (r, c+1) in self.walls

            is_corner = (up or down) and (left or right)
            is_wall_blocked = False

            if down or up:
                if (r, c-1) in self.boxes and ((down and (r+1, c-1) in self.walls) or (up and (r-1, c-1) in self.walls)): is_wall_blocked = True
                if (r, c+1) in self.boxes and ((down and (r+1, c+1) in self.walls) or (up and (r-1, c+1) in self.walls)): is_wall_blocked = True

            if left or right:
                if (r-1, c) in self.boxes and ((left and (r-1, c-1) in self.walls) or (right and (r-1, c+1) in self.walls)): is_wall_blocked = True
                if (r+1, c) in self.boxes and ((left and (r+1, c-1) in self.walls) or (right and (r+1, c+1) in self.walls)): is_wall_blocked = True

            if not is_corner and not is_wall_blocked:
                return False 
        return True

    def resolve_simultaneous_moves(self, a1, a2):
        n_p1 = (self.p1_pos[0] + a1[0], self.p1_pos[1] + a1[1])
        n_p2 = (self.p2_pos[0] + a2[0], self.p2_pos[1] + a2[1])
        
        n_box1, n_box2 = None, None
        pushing_box1, pushing_box2 = False, False

        def is_valid_basic(pos):
            return pos not in self.walls
            
        if not is_valid_basic(n_p1): n_p1 = self.p1_pos
        if not is_valid_basic(n_p2): n_p2 = self.p2_pos

        if n_p1 in self.boxes:
            pushing_box1 = True
            n_box1 = (n_p1[0] + a1[0], n_p1[1] + a1[1])
            if not is_valid_basic(n_box1) or n_box1 in self.boxes or n_box1 == self.p2_pos or n_box1 == n_p2:
                n_p1 = self.p1_pos
                pushing_box1 = False
                
        if n_p2 in self.boxes:
            pushing_box2 = True
            n_box2 = (n_p2[0] + a2[0], n_p2[1] + a2[1])
            if not is_valid_basic(n_box2) or n_box2 in self.boxes or n_box2 == self.p1_pos or n_box2 == n_p1:
                n_p2 = self.p2_pos
                pushing_box2 = False
        if n_p1 == self.p2_pos and n_p2 == self.p1_pos:
            n_p1, n_p2 = self.p1_pos, self.p2_pos
        if n_p1 == n_p2:
            n_p1, n_p2 = self.p1_pos, self.p2_pos
        if pushing_box1 and n_p2 == n_p1:
            n_p2 = self.p2_pos
        if pushing_box2 and n_p1 == n_p2:
            n_p1 = self.p1_pos

        new_boxes = {}
        for (r, c), owner in self.boxes.items():
            if pushing_box1 and (r, c) == n_p1:
                new_boxes[n_box1] = 1
            elif pushing_box2 and (r, c) == n_p2:
                new_boxes[n_box2] = 2
            else:
                new_boxes[(r, c)] = owner
                
        self.boxes = new_boxes
        self.p1_pos = n_p1
        self.p2_pos = n_p2

        self.score_p1 = sum(1 for (r, c), owner in self.boxes.items() if (r, c) in self.goals and owner == 1)
        self.score_p2 = sum(1 for (r, c), owner in self.boxes.items() if (r, c) in self.goals and owner == 2)
        
        self.current_turn += 1

    def update(self):
        if not self.is_paused:
            if not self.ai_calculating:
                state = self.get_game_state()
                self.future_p1 = self.executor.submit(self.agent1.get_action, state, 800)
                self.future_p2 = self.executor.submit(self.agent2.get_action, state, 800)
                self.ai_calculating = True
                
            else:
                if self.future_p1.done() and self.future_p2.done():
                    a1 = self.future_p1.result()
                    a2 = self.future_p2.result()
                    
                    self.resolve_simultaneous_moves(a1, a2)
                    self.ai_calculating = False
                    
                    is_max_turns = self.current_turn >= self.max_turns
                    is_deadlocked = self.is_board_deadlocked()
                    
                    if is_max_turns or is_deadlocked:
                        self.is_paused = True
                        print("\n" + "="*40)
                        if is_max_turns:
                            print(f"GAME OVER! ĐÃ HẾT GIỚI HẠN {self.max_turns} BƯỚC.")
                        elif is_deadlocked:
                            print("GAME OVER! BẾ TẮC TOÀN BỘ BÀN CỜ.")
                            
                        print(f"TỈ SỐ CHUNG CUỘC: P1 ({self.score_p1}) - P2 ({self.score_p2})")
                        if self.score_p1 > self.score_p2: print("🎉 NGƯỜI CHƠI 1 (BLUE) THẮNG! 🎉")
                        elif self.score_p2 > self.score_p1: print("🎉 NGƯỜI CHƠI 2 (RED) THẮNG! 🎉")
                        else: print("🤝 TRẬN ĐẤU HÒA! 🤝")
                        print("="*40 + "\n")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                self.running = False
                self.executor.shutdown(wait=False)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.is_paused = not self.is_paused

    def draw(self):
        self.screen.fill(COLOR_BG)
        
        COLOR_T1 = (100, 150, 255)
        COLOR_T2 = (255, 100, 100)

        for r in range(self.board_rows):
            for c in range(self.board_cols):
                x = self.offset_x + c * TILE_SIZE
                y = self.offset_y + r * TILE_SIZE
                if (r, c) in self.walls: self.screen.blit(self.sprites['wall'], (x, y))
                else: self.screen.blit(self.sprites['floor'], (x, y))
                if (r, c) in self.goals: self.screen.blit(self.sprites['goal'], (x, y))

        for (r, c), owner in self.boxes.items():
            x = self.offset_x + c * TILE_SIZE
            y = self.offset_y + r * TILE_SIZE
            box_img = self.sprites['box_on_goal'] if (r, c) in self.goals else self.sprites['box']
            if owner == 1: box_img = self.tint_surface(box_img, COLOR_T1)
            if owner == 2: box_img = self.tint_surface(box_img, COLOR_T2)
            self.screen.blit(box_img, (x, y))

        p1_x, p1_y = self.offset_x + self.p1_pos[1]*TILE_SIZE, self.offset_y + self.p1_pos[0]*TILE_SIZE
        p1_img = self.tint_surface(self.sprites['player'], COLOR_T1)
        self.screen.blit(p1_img, (p1_x, p1_y))
        
        p2_x, p2_y = self.offset_x + self.p2_pos[1]*TILE_SIZE, self.offset_y + self.p2_pos[0]*TILE_SIZE
        p2_img = self.tint_surface(self.sprites['player'], COLOR_T2)
        self.screen.blit(p2_img, (p2_x, p2_y))

        info_y = self.screen_height - 80
        pygame.draw.rect(self.screen, (200, 190, 170), (0, info_y, self.screen_width, 80))
        
        txt_p1 = self.font_large.render(f"P1 (Blue): {self.score_p1}", True, (0, 0, 150))
        txt_p2 = self.font_large.render(f"P2 (Red): {self.score_p2}", True, (150, 0, 0))
        
        txt_turn = self.font.render(f"Turn: {self.current_turn}/{self.max_turns}", True, (10, 10, 10))
        
        if self.ai_calculating:
            status_text = "THINKING..."
        elif self.is_paused:
            status_text = "PAUSED (Space to start)"
        else:
            status_text = "BATTLE ONGOING"
            
        txt_status = self.font.render(status_text, True, (100, 100, 100))
        
        self.screen.blit(txt_p1, (20, info_y + 20))
        self.screen.blit(txt_p2, (self.screen_width - 180, info_y + 20))
        self.screen.blit(txt_turn, (self.screen_width//2 - 40, info_y + 10))
        self.screen.blit(txt_status, (self.screen_width//2 - 90, info_y + 40))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    print("==================================================")
    print("      SOKOBAN COMPETITIVE - LUẬT CƯỚP THÙNG")
    print("==================================================")
    try:
        n_turns = int(input("Nhập số bước tối đa cho trận đấu (VD: 100): "))
    except ValueError:
        print("Đầu vào không hợp lệ, dùng mặc định 100 bước.")
        n_turns = 100
        
    map_file = os.path.join(os.path.dirname(__file__), "map_2p.txt")
    game = SokobanCompetitive(map_file, max_turns=n_turns)
    game.run()