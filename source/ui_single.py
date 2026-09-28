import pygame
import sys
import os

from models.board import Board

# Kích thước mỗi ô vuông trên màn hình
TILE_SIZE = 48
PADDING_TILES = 1  # Độ rộng lề viền bao quanh bản đồ

COLOR_BG = (220, 210, 190)  # Màu nền viền ngoài
COLOR_TEXT = (30, 30, 30)


class SokobanGUI:
    def __init__(self, map_path):
        pygame.init()
        pygame.font.init()

        self.board = Board(map_path)
        self.board_rows = len(self.board.grid)
        self.board_cols = max(len(row) for row in self.board.grid)
        
        self.total_cols = self.board_cols + PADDING_TILES * 2
        self.total_rows = self.board_rows + PADDING_TILES * 2
        
        self.screen_width = self.total_cols * TILE_SIZE
        self.screen_height = self.total_rows * TILE_SIZE + 60 # Tăng nhẹ chiều cao để vẽ thêm text
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Sokoban - Task 5 (Single Player)")
        
        self.font = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 40, bold=True)
        
        self.sprites = self._load_sprites()
        self.outside = self._find_outside_spaces()
        
        # --- GIẢ LẬP KẾT QUẢ TỪ AI (MOCK DATA) ---
        # Khi Anh Tuấn làm xong Task 2, bạn sẽ gán self.solution_path = a_star_search(self.board)
        initial_state = (self.board.agent_pos, list(self.board.boxes))
        self.solution_path = [initial_state]
        
        self.selected_algo = "A*"
        self.current_step = 0
        self.is_paused = True
        
        # Cài đặt tốc độ Auto-play (thời gian giữa các bước)
        self.auto_play_speed = 300 # ms
        self.last_auto_move = pygame.time.get_ticks()
        
        self.running = True
        self.clock = pygame.time.Clock()
        
        self.offset_x = PADDING_TILES * TILE_SIZE
        self.offset_y = PADDING_TILES * TILE_SIZE

    def _load_sprites(self):
        """Nạp và tự động co dãn ảnh, xử lý lỗi hở viền tường và sàn."""
        base_dir = os.path.dirname(__file__)
        img_dir = os.path.join(base_dir, "assets", "images")
        
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
                
                # SỬA LỖI HỞ VIỀN CHO TƯỜNG VÀ SÀN
                if key in ['wall', 'floor']:
                    crop_rect = raw_img.get_bounding_rect()
                    raw_img = raw_img.subsurface(crop_rect)
                    sprites[key] = pygame.transform.scale(raw_img, (TILE_SIZE, TILE_SIZE))
                else:
                    sprites[key] = pygame.transform.smoothscale(raw_img, (TILE_SIZE, TILE_SIZE))
            else:
                print(f"Lỗi: Không tìm thấy file {path}")
                sys.exit(1)
                
        return sprites

    def _find_outside_spaces(self):
        """Tìm các khoảng trắng bên ngoài bức tường (void) bằng BFS."""
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

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                # Phím Space: Chuyển đổi trạng thái Auto-play / Pause
                if event.key == pygame.K_SPACE:
                    self.is_paused = not self.is_paused
                
                # Phím 1, 2: Chọn thuật toán
                elif event.key == pygame.K_1:
                    self.selected_algo = "UCS"
                    self.current_step = 0
                    self.is_paused = True
                    # TODO: self.solution_path = ucs_search(self.board)
                elif event.key == pygame.K_2:
                    self.selected_algo = "A*"
                    self.current_step = 0
                    self.is_paused = True
                    # TODO: self.solution_path = a_star_search(self.board)

                # Phím mũi tên (Chỉ thao tác tay khi đang Pause)
                if self.is_paused:
                    if event.key == pygame.K_RIGHT:
                        if self.current_step < len(self.solution_path) - 1:
                            self.current_step += 1
                            self.board.agent_pos, boxes = self.solution_path[self.current_step]
                            self.board.boxes = list(boxes)
                            
                    elif event.key == pygame.K_LEFT:
                        if self.current_step > 0:
                            self.current_step -= 1
                            self.board.agent_pos, boxes = self.solution_path[self.current_step]
                            self.board.boxes = list(boxes)

    def update(self):
        """Cập nhật logic game (Auto-play)."""
        if not self.is_paused:
            now = pygame.time.get_ticks()
            if now - self.last_auto_move > self.auto_play_speed:
                if self.current_step < len(self.solution_path) - 1:
                    self.current_step += 1
                    self.board.agent_pos, boxes = self.solution_path[self.current_step]
                    self.board.boxes = list(boxes)
                    self.last_auto_move = now
                else:
                    self.is_paused = True # Hết đường thì tự động Pause

    def draw(self):
        """Vẽ toàn bộ lên màn hình."""
        self.screen.fill(COLOR_BG)

        for r in range(self.board_rows):
            for c in range(len(self.board.grid[r])):
                char = self.board.grid[r][c]
                x = self.offset_x + c * TILE_SIZE
                y = self.offset_y + r * TILE_SIZE
                
                if char == '%':
                    self.screen.blit(self.sprites['wall'], (x, y))
                else:
                    if (r, c) not in self.outside:
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

        # --- THANH THÔNG TIN BÊN DƯỚI ---
        info_y = self.total_rows * TILE_SIZE
        info_rect = pygame.Rect(0, info_y, self.screen_width, 60)
        pygame.draw.rect(self.screen, (200, 190, 170), info_rect)
        pygame.draw.line(self.screen, (150, 140, 120), (0, info_y), (self.screen_width, info_y), 2)
        
        # Hiển thị Thuật toán đang chọn và trạng thái
        txt_algo = self.font.render(f"Algo: {self.selected_algo} (Press 1/2)", True, COLOR_TEXT)
        txt_steps = self.font.render(f"Steps: {self.current_step}", True, COLOR_TEXT)
        status_color = (180, 0, 0) if self.is_paused else (0, 120, 0)
        txt_status = self.font.render("PAUSED" if self.is_paused else "AUTO-PLAY", True, status_color)

        self.screen.blit(txt_algo, (15, info_y + 10))
        self.screen.blit(txt_steps, (15, info_y + 35))
        self.screen.blit(txt_status, (self.screen_width - 120, info_y + 20))

        pygame.display.flip()

    def run(self):
        """Vòng lặp game."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(30)
        pygame.quit()


if __name__ == "__main__":
    map_file = os.path.join(os.path.dirname(__file__), "maps", "example_map.txt")
    game = SokobanGUI(map_file)
    game.run()