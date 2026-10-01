# algorithms/base_agent.py

class BaseAgent:
    def __init__(self, player_id):
        """
        player_id: 1 (Team 1) hoặc 2 (Team 2)
        """
        self.player_id = player_id

    def get_action(self, state, time_limit):
        """
        Nhận vào trạng thái hiện tại (state) và thời gian cho phép (time_limit tính bằng ms).
        Trả về một tuple hướng di chuyển: (dx, dy).
        Các hướng hợp lệ: (0, -1), (0, 1), (-1, 0), (1, 0), (0, 0) - đứng yên.
        """
        raise NotImplementedError("Phải override hàm get_action trong class kế thừa.")