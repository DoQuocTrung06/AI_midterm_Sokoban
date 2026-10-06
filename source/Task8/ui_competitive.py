import pygame
import sys
import os
import time
import concurrent.futures

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from Task7.agent_team1 import AgentTeam1
from Task7.agent_team2 import AgentTeam2

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
        pygame.display.set_caption("Sokoban - Box Stealing (No Lock)")
        
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

        self.history = []
        self.view_index = 0
        self._save_state()

        self.game_over = False
        self.game_over_reason = ""
        self.blurred_background = None

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
    
    def _save_state(self):
        state = {
            'p1_pos': self.p1_pos,
            'p2_pos': self.p2_pos,
            'boxes': self.boxes.copy(),
            'score_p1': self.score_p1,
            'score_p2': self.score_p2,
            'current_turn': self.current_turn
        }
        self.history.append(state)
        self.view_index = len(self.history) - 1

    def _load_state(self, index):
        state = self.history[index]
        self.p1_pos = state['p1_pos']
        self.p2_pos = state['p2_pos']
        self.boxes = state['boxes'].copy()
        self.score_p1 = state['score_p1']
        self.score_p2 = state['score_p2']
        self.current_turn = state['current_turn']

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
                
        if pushing_box1 and pushing_box2 and n_box1 == n_box2:
            pushing_box1 = False
            pushing_box2 = False
            n_p1 = self.p1_pos
            n_p2 = self.p2_pos

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

        self._save_state()

    def update(self):
        if not self.is_paused and not self.game_over:
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
                        self.game_over = True
                        self.game_over_reason = "MAX TURNS REACHED" if is_max_turns else "BOARD DEADLOCKED"

                        print("\n" + "="*40)
                        print(f"GAME OVER! {self.game_over_reason}")
                        print(f"FINAL SCORE: P1 ({self.score_p1}) - P2 ({self.score_p2})")
                        if self.score_p1 > self.score_p2: print("PLAYER 1 (BLUE) WINS")
                        elif self.score_p2 > self.score_p1: print("PLAYER 2 (RED) WINS")
                        else: print("DRAW")
                        print("="*40 + "\n")

    def handle_events(self):
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    self.running = False
                    self.executor.shutdown(wait=False)
                elif event.type == pygame.KEYDOWN:
                    if not self.game_over:
                        if event.key == pygame.K_SPACE:
                            self.is_paused = not self.is_paused
                            if not self.is_paused and self.view_index < len(self.history) - 1:
                                self.history = self.history[:self.view_index + 1]
                        elif event.key == pygame.K_LEFT:
                            self.is_paused = True
                            if self.view_index > 0:
                                self.view_index -= 1
                                self._load_state(self.view_index)
                        elif event.key == pygame.K_RIGHT:
                            self.is_paused = True
                            if self.view_index < len(self.history) - 1:
                                self.view_index += 1
                                self._load_state(self.view_index)
                            
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
        
        if self.game_over:
            status_text = "GAME OVER"
        elif self.ai_calculating:
            status_text = "THINKING..."
        elif self.is_paused:
            if self.view_index < len(self.history) - 1:
                status_text = f"REVIEWING: TURN {self.current_turn} (Space to overwrite & resume)"
            else:
                status_text = "PAUSED (Space to start)"
        else:
            status_text = "BATTLE ONGOING"            
        txt_status = self.font.render(status_text, True, (100, 100, 100))
        
        self.screen.blit(txt_p1, (20, info_y + 20))
        self.screen.blit(txt_p2, (self.screen_width - 180, info_y + 20))
        self.screen.blit(txt_turn, (self.screen_width//2 - 40, info_y + 10))
        self.screen.blit(txt_status, (self.screen_width//2 - 130 if self.is_paused else self.screen_width//2 - 90, info_y + 40))

        if self.game_over:
            if self.blurred_background is None:
                small = pygame.transform.smoothscale(self.screen, (self.screen_width // 4, self.screen_height // 4))
                self.blurred_background = pygame.transform.smoothscale(small, (self.screen_width, self.screen_height))
                
                overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                self.blurred_background.blit(overlay, (0, 0))

            self.screen.blit(self.blurred_background, (0, 0))

            if self.score_p1 > self.score_p2:
                winner_txt = "PLAYER 1 (BLUE) WINS!"
                color_win = (100, 150, 255)
            elif self.score_p2 > self.score_p1:
                winner_txt = "PLAYER 2 (RED) WINS!"
                color_win = (255, 100, 100)
            else:
                winner_txt = "DRAW!"
                color_win = (200, 200, 200)

            font_title = pygame.font.SysFont("Arial", 40, bold=True)
            font_score = pygame.font.SysFont("Arial", 30, bold=True)
            
            title_surf = font_title.render("GAME OVER", True, (255, 255, 255))
            reason_surf = self.font.render(self.game_over_reason, True, (200, 200, 200))
            score_surf = font_score.render(f"P1: {self.score_p1}   -   P2: {self.score_p2}", True, (255, 255, 255))
            win_surf = font_title.render(winner_txt, True, color_win)
            
            cx, cy = self.screen_width // 2, self.screen_height // 2
            self.screen.blit(title_surf, (cx - title_surf.get_width()//2, cy - 80))
            self.screen.blit(reason_surf, (cx - reason_surf.get_width()//2, cy - 30))
            self.screen.blit(score_surf, (cx - score_surf.get_width()//2, cy + 10))
            self.screen.blit(win_surf, (cx - win_surf.get_width()//2, cy + 60))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

def main():
    print("SOKOBAN COMPETITIVE - BOX STEALING GAME")
    try:
        n_turns = int(input("Enter the maximum number of turns for the match (e.g., 100): "))
    except ValueError:
        print("Invalid input, using default 100 turns.")
        n_turns = 100
        
    map_file = os.path.join(os.path.dirname(__file__), "map_2p.txt")
    game = SokobanCompetitive(map_file, max_turns=n_turns)
    game.run()

if __name__ == "__main__":
    main()