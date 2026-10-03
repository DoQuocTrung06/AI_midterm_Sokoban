class SokobanProblem:
    def __init__(self, file_path):
        self.walls = set()
        self.targets = set()
        boxes = []
        self.start_agent = None

        with open(file_path, 'r') as f:
            for y, line in enumerate(f.readlines()):
                for x, char in enumerate(line.strip('\n')):
                    if char == '%':
                        self.walls.add((x, y))
                    elif char == 'D':
                        self.targets.add((x, y))
                    elif char == 'B':
                        boxes.append((x, y))
                    elif char == 'A':
                        self.start_agent = (x, y)
                    elif char == 'C':
                        boxes.append((x, y))
                        self.targets.add((x, y))

        self.start_state = (self.start_agent, tuple(sorted(boxes)))

    def is_goal(self, state):
        _, boxes = state
        return set(boxes) == self.targets

    def get_successors(self, state):
        agent_pos, boxes = state
        successors = []
        
        actions = {'North': (0, -1), 'South': (0, 1), 'East': (1, 0), 'West': (-1, 0)}

        for action, (dx, dy) in actions.items():
            new_agent = (agent_pos[0] + dx, agent_pos[1] + dy)

            if new_agent in self.walls:
                continue

            if new_agent in boxes:
                new_box = (new_agent[0] + dx, new_agent[1] + dy)

                if new_box in self.walls or new_box in boxes:
                    continue
                
                new_boxes = list(boxes)
                new_boxes[new_boxes.index(new_agent)] = new_box
                next_state = (new_agent, tuple(sorted(new_boxes)))
                successors.append((next_state, action, 1))
            
            else:
                next_state = (new_agent, boxes)
                successors.append((next_state, action, 1))

        return successors