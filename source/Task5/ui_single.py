import pygame
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.abspath(os.path.join(current_dir, '..'))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

from Task5.board import Board
from Task1.sokoban_problem import SokobanProblem
from Task2.search_algorithms import ucs, a_star, SearchStats
from Task2.heuristics import calculate_heuristic

TILE_SIZE = 48
PADDING_TILES = 1

COLOR_BG = (220, 210, 190)
COLOR_INFO_BG = (200, 190, 170)
COLOR_LINE = (150, 140, 120)
COLOR_TEXT = (30, 30, 30)
COLOR_PAUSED = (180, 0, 0)
COLOR_PLAYING = (0, 120, 0)


class SokobanGUI:

    def __init__(self, map_path):
        pygame.init()
        pygame.font.init()

        self.map_path = map_path
        self.board = Board(map_path)
        self.board_rows = len(self.board.grid)
        self.board_cols = max(len(row) for row in self.board.grid)

        self.total_cols = self.board_cols + PADDING_TILES * 2
        self.total_rows = self.board_rows + PADDING_TILES * 2

        self.screen_width = self.total_cols * TILE_SIZE
        self.screen_height = self.total_rows * TILE_SIZE + 80

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Sokoban - Task 5 (Single Player)")

        self.font = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 40, bold=True)

        self.sprites = self._load_sprites()
        self.outside_spaces = self._find_outside_spaces()

        self.selected_algo = "None"
        self.current_step = 0
        self.is_paused = True

        self.auto_play_speed = 300
        self.last_auto_move_time = pygame.time.get_ticks()

        self.running = True
        self.clock = pygame.time.Clock()

        self.offset_x = PADDING_TILES * TILE_SIZE
        self.offset_y = PADDING_TILES * TILE_SIZE

        self.solution_path = [(self.board.agent_pos, list(self.board.boxes))]

    def _load_sprites(self):
        base_dir = os.path.dirname(__file__)
        img_dir = os.path.join(base_dir, "..", "assets", "images")

        files = {
            'wall': "wall.png",
            'floor': "floor.png",
            'goal': "goal.png",
            'box': "box.png",
            'box_on_goal': "box_on_goal.png",
            'player': "player.png"
        }

        sprites = {}
        for key, filename in files.items():
            path = os.path.join(img_dir, filename)
            if os.path.exists(path):
                raw_img = pygame.image.load(path).convert_alpha()

                if key in ['wall', 'floor']:
                    crop_rect = raw_img.get_bounding_rect()
                    raw_img = raw_img.subsurface(crop_rect)
                    sprites[key] = pygame.transform.scale(raw_img, (TILE_SIZE, TILE_SIZE))
                else:
                    sprites[key] = pygame.transform.smoothscale(raw_img, (TILE_SIZE, TILE_SIZE))
            else:
                print(f"Error: Sprite file not found at {path}")
                sys.exit(1)

        return sprites

    def _find_outside_spaces(self):
        outside = set()
        queue = []

        for r in range(self.board_rows):
            for c in range(len(self.board.grid[r])):
                if self.board.grid[r][c] == ' ':
                    if r == 0 or r == self.board_rows - 1 or c == 0 or c == len(self.board.grid[r]) - 1:
                        outside.add((r, c))
                        queue.append((r, c))

        while queue:
            curr_r, curr_c = queue.pop(0)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = curr_r + dr, curr_c + dc
                if 0 <= nr < self.board_rows and 0 <= nc < len(self.board.grid[nr]):
                    if self.board.grid[nr][nc] == ' ' and (nr, nc) not in outside:
                        outside.add((nr, nc))
                        queue.append((nr, nc))
        return outside

    def _convert_actions_to_states(self, initial_board, actions):
        direction_offsets = {
            'NORTH': (-1, 0), 'N': (-1, 0), 'UP': (-1, 0),
            'SOUTH': (1, 0),  'S': (1, 0),  'DOWN': (1, 0),
            'WEST':  (0, -1), 'W': (0, -1), 'LEFT': (0, -1),
            'EAST':  (0, 1),  'E': (0, 1),  'RIGHT': (0, 1)
        }

        states = [(initial_board.agent_pos, list(initial_board.boxes))]
        curr_agent = initial_board.agent_pos
        curr_boxes = set(initial_board.boxes)

        for act in actions:
            act_upper = str(act).upper()
            if act_upper not in direction_offsets:
                continue

            dr, dc = direction_offsets[act_upper]
            next_agent = (curr_agent[0] + dr, curr_agent[1] + dc)

            if next_agent in curr_boxes:
                next_box = (next_agent[0] + dr, next_agent[1] + dc)
                curr_boxes.remove(next_agent)
                curr_boxes.add(next_box)

            curr_agent = next_agent
            states.append((curr_agent, list(curr_boxes)))

        return states

    def _solve_and_load(self, algo_name):
        self.board = Board(self.map_path)
        self.selected_algo = algo_name
        self.current_step = 0
        self.is_paused = True

        initial_state = (self.board.agent_pos, list(self.board.boxes))
        print(f"Solving puzzle using algorithm: {algo_name}...")

        self.screen.fill(COLOR_BG)
        txt_solving = self.font_large.render(f"SOLVING WITH {algo_name}...", True, COLOR_PAUSED)
        self.screen.blit(txt_solving, (self.screen_width//2 - txt_solving.get_width()//2, self.screen_height//2 - txt_solving.get_height()//2))
        pygame.display.flip()

        try:
            problem = SokobanProblem(self.map_path)
            raw_result = None
            stats = SearchStats()
            self.solve_stats = stats

            if algo_name == "UCS":
                path, cost = ucs(problem, stats=stats)
                raw_result = path
            elif algo_name == "A*":
                path, cost = a_star(problem, calculate_heuristic, stats=stats)
                raw_result = path

            if raw_result is None:
                self.solution_path = [initial_state]
            elif isinstance(raw_result, list) and len(raw_result) > 0:
                if isinstance(raw_result[0], str):
                    self.solution_path = self._convert_actions_to_states(self.board, raw_result)
                else:
                    self.solution_path = raw_result
            else:
                self.solution_path = [initial_state]

            print(f"Search completed! Total steps: {len(self.solution_path) - 1}")

        except Exception as err:
            print(f"Error executing algorithm {algo_name}: {err}")
            self.solution_path = [initial_state]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.selected_algo != "None":
                        self.is_paused = not self.is_paused

                elif event.key in (pygame.K_1, pygame.K_KP1):
                    self._solve_and_load("UCS")
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self._solve_and_load("A*")

                elif event.key == pygame.K_RIGHT:
                    if self.is_paused and self.current_step < len(self.solution_path) - 1:
                        self.current_step += 1
                        self.board.agent_pos, boxes = self.solution_path[self.current_step]
                        self.board.boxes = list(boxes)

                elif event.key == pygame.K_LEFT:
                    if self.is_paused and self.current_step > 0:
                        self.current_step -= 1
                        self.board.agent_pos, boxes = self.solution_path[self.current_step]
                        self.board.boxes = list(boxes)

    def update(self):
        if self.selected_algo == "None":
            return

        if not self.is_paused:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_auto_move_time > self.auto_play_speed:
                if self.current_step < len(self.solution_path) - 1:
                    self.current_step += 1
                    self.board.agent_pos, boxes = self.solution_path[self.current_step]
                    self.board.boxes = list(boxes)
                    self.last_auto_move_time = current_time
                else:
                    self.is_paused = True

    def draw(self):
        self.screen.fill(COLOR_BG)

        for r in range(self.board_rows):
            for c in range(len(self.board.grid[r])):
                char = self.board.grid[r][c]
                x = self.offset_x + c * TILE_SIZE
                y = self.offset_y + r * TILE_SIZE

                if char == '%':
                    self.screen.blit(self.sprites['wall'], (x, y))
                else:
                    if (r, c) not in self.outside_spaces:
                        self.screen.blit(self.sprites['floor'], (x, y))

                if (r, c) in self.board.goals:
                    self.screen.blit(self.sprites['goal'], (x, y))

        for (r, c) in self.board.boxes:
            x = self.offset_x + c * TILE_SIZE
            y = self.offset_y + r * TILE_SIZE
            if (r, c) in self.board.goals:
                self.screen.blit(self.sprites['box_on_goal'], (x, y))
            else:
                self.screen.blit(self.sprites['box'], (x, y))

        if self.board.agent_pos:
            ar, ac = self.board.agent_pos
            ax = self.offset_x + ac * TILE_SIZE
            ay = self.offset_y + ar * TILE_SIZE
            self.screen.blit(self.sprites['player'], (ax, ay))

        info_y = self.total_rows * TILE_SIZE
        info_rect = pygame.Rect(0, info_y, self.screen_width, 80)
        pygame.draw.rect(self.screen, COLOR_INFO_BG, info_rect)
        pygame.draw.line(self.screen, COLOR_LINE, (0, info_y), (self.screen_width, info_y), 2)

        total_actions = max(0, len(self.solution_path) - 1)

        if self.selected_algo == "None":
            txt_algo = self.font.render("Waiting for selection... (1: UCS, 2: A*)", True, COLOR_TEXT)
        else:
            txt_algo = self.font.render(f"Algo: {self.selected_algo} (Key 1: UCS | Key 2: A*)", True, COLOR_TEXT)

        txt_steps = self.font.render(f"Actions: {self.current_step} / {total_actions}", True, COLOR_TEXT)

        stats_info = ""
        if hasattr(self, 'solve_stats'):
            stats_info = f"Nodes: {self.solve_stats.expanded} | Time: {self.solve_stats.time_s:.3f}s"
        txt_stats = self.font.render(stats_info, True, (0, 100, 200))

        if self.selected_algo == "None":
            status_text = "WAITING"
            status_color = (150, 150, 150)
        elif total_actions > 0 and self.current_step == total_actions:
            status_text = "GOAL REACHED!"
            status_color = (0, 0, 255)
        else:
            status_text = "PAUSED" if self.is_paused else "AUTO-PLAY"
            status_color = COLOR_PAUSED if self.is_paused else COLOR_PLAYING

        txt_status = self.font.render(status_text, True, status_color)

        self.screen.blit(txt_algo, (15, info_y + 10))
        self.screen.blit(txt_steps, (15, info_y + 35))
        self.screen.blit(txt_stats, (15, info_y + 60))
        self.screen.blit(txt_status, (self.screen_width - 130, info_y + 30))

        if self.selected_algo == "None":
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

            prompt_txt1 = self.font_large.render("SELECT ALGORITHM", True, (255, 255, 255))
            prompt_txt2 = self.font.render("Press 1 for UCS   |   Press 2 for A*", True, (200, 255, 200))
            self.screen.blit(prompt_txt1, (self.screen_width//2 - prompt_txt1.get_width()//2, self.screen_height//2 - 40))
            self.screen.blit(prompt_txt2, (self.screen_width//2 - prompt_txt2.get_width()//2, self.screen_height//2 + 10))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(30)
        pygame.quit()


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    map_file = os.path.join(base_dir, "..", "maps", "example_map.txt")
    game = SokobanGUI(map_file)
    game.run()


if __name__ == "__main__":
    main()
