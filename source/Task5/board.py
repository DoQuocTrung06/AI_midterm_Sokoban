class Board:
    def __init__(self, file_path):
        self.grid = []          # Mảng 2 chiều lưu bản đồ
        self.agent_pos = None   # Tọa độ nhân vật (row, col)
        self.boxes = []         # Danh sách tọa độ các thùng [(r1, c1), (r2, c2),...]
        self.goals = []         # Danh sách tọa độ các đích đến
        
        self.load_map(file_path)

    def load_map(self, file_path):
        """Đọc file text và phân tích các thành phần."""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for row_idx, line in enumerate(lines):
            # Dùng rstrip('\n') để chỉ xóa dấu xuống dòng ở cuối, 
            # GIỮ NGUYÊN các khoảng trắng ở đầu dòng (rất quan trọng với dòng 1)
            row_data = list(line.rstrip('\n'))
            self.grid.append(row_data)

            # Duyệt qua từng ký tự trong dòng để tìm A, B, D, C
            for col_idx, char in enumerate(row_data):
                if char == 'A':
                    self.agent_pos = (row_idx, col_idx)
                elif char == 'B':
                    self.boxes.append((row_idx, col_idx))
                elif char == 'D':
                    self.goals.append((row_idx, col_idx))
                elif char == 'C':
                    # 'C' nghĩa là thùng đang nằm sẵn trên đích
                    self.boxes.append((row_idx, col_idx))
                    self.goals.append((row_idx, col_idx))

    def is_valid_move(self, row, col):
        """Kiểm tra ô (row, col) có hợp lệ để đi vào không (không phải tường)."""
        # Kiểm tra xem tọa độ có bị lọt ra ngoài mảng không (out of bounds)
        if 0 <= row < len(self.grid) and 0 <= col < len(self.grid[row]):
            # Hợp lệ nếu ký tự tại đó KHÔNG PHẢI là tường '%'
            return self.grid[row][col] != '%'
        return False

