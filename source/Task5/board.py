class Board:
    def __init__(self, file_path):
        self.grid = []
        self.agent_pos = None
        self.boxes = []
        self.goals = []
        
        self.load_map(file_path)

    def load_map(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for row_idx, line in enumerate(lines):
            row_data = list(line.rstrip('\n'))
            self.grid.append(row_data)

            for col_idx, char in enumerate(row_data):
                if char == 'A':
                    self.agent_pos = (row_idx, col_idx)
                elif char == 'B':
                    self.boxes.append((row_idx, col_idx))
                elif char == 'D':
                    self.goals.append((row_idx, col_idx))
                elif char == 'C':
                    self.boxes.append((row_idx, col_idx))
                    self.goals.append((row_idx, col_idx))

    def is_valid_move(self, row, col):
        if 0 <= row < len(self.grid) and 0 <= col < len(self.grid[row]):
            return self.grid[row][col] != '%'
        return False
