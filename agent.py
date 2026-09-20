# agent.py
class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        # If standing directly on food, or just wander / move towards coordinates
        pos = percept['agent_pos']
        # Simple heuristic or fallback random sweep
        return random.choice(self.actions_pool)

from collections import deque
import heapq


class SearchAgent:
    # Direction -> (dx, dy). Matches the environment: "Up" increases y.
    MOVES = {
        "Up": (0, 1),
        "Down": (0, -1),
        "Left": (-1, 0),
        "Right": (1, 0),
    }

    LEFT_TURNS = {"Up": "Left", "Left": "Down", "Down": "Right", "Right": "Up"}
    RIGHT_TURNS = {"Up": "Right", "Right": "Down", "Down": "Left", "Left": "Up"}

    def __init__(self):
        self.plan = []
        self.active_algo = 'UCS'

        # The percept does not include the agent's position or heading,
        # so the agent tracks them itself (same as ModelBasedAgent).
        self.current_position = (4, 2)
        self.direction = "Down"
        self.visited_cells = {(4, 2)}
        self.last_action = None
        self.last_wall_ahead = False

    def update_internal_state(self, percept):
        """Update the estimated position / heading using the previous action."""
        if self.last_action == "MoveForward" and not self.last_wall_ahead:
            x, y = self.current_position
            dx, dy = self.MOVES[self.direction]
            self.current_position = (x + dx, y + dy)
            self.visited_cells.add(self.current_position)

        elif self.last_action == "TurnLeft":
            self.direction = self.LEFT_TURNS[self.direction]

        elif self.last_action == "TurnRight":
            self.direction = self.RIGHT_TURNS[self.direction]

        self.last_wall_ahead = percept["wall_ahead"]

    def directions_to_actions(self, directions):
        """
        Convert a list of movement directions (Up/Down/Left/Right) into the
        environment's primitive actions (TurnLeft/TurnRight/MoveForward).
        """
        actions = []
        facing = self.direction

        for target in directions:
            if facing == target:
                pass
            elif self.LEFT_TURNS[facing] == target:
                actions.append("TurnLeft")
            elif self.RIGHT_TURNS[facing] == target:
                actions.append("TurnRight")
            else:  # opposite direction
                actions.extend(["TurnLeft", "TurnLeft"])

            facing = target
            actions.append("MoveForward")

        return actions

    def sense_and_act(self, percept: dict) -> str:
        self.update_internal_state(percept)

        if not self.plan:
            all_food = [tuple(f) for f in percept["all_food"]]

            if not all_food:
                # Nothing left to plan for
                self.last_action = "TurnLeft"
                return self.last_action

            # Closest food pellet by Manhattan distance
            x, y = self.current_position
            goal = min(all_food, key=lambda f: abs(f[0] - x) + abs(f[1] - y))

            search = {
                'BFS': self.bfs_search,
                'DFS': self.dfs_search,
                'UCS': self.ucs_search,
            }[self.active_algo]

            directions = search(
                self.current_position,
                goal,
                percept["walls"],
                percept["grid_size"],
            )

            # The plan ends with "Suck" to collect the pellet on arrival
            self.plan = self.directions_to_actions(directions) + ["Suck"]

            print(
                f"[{self.active_algo}] New plan from {self.current_position} "
                f"to {goal}: {len(directions)} moves, {len(self.plan)} actions -> {self.plan}"
            )

        self.last_action = self.plan.pop(0)
        return self.last_action

    def get_successors(self, state, walls, grid_size):
        """Return a list of (action, next_state) pairs for a given state."""
        x, y = state
        width, height = grid_size
        successors = []

        for action, (dx, dy) in self.MOVES.items():
            nx, ny = x + dx, y + dy

            inside_grid = 0 <= nx < width and 0 <= ny < height
            if inside_grid and (nx, ny) not in walls:
                successors.append((action, (nx, ny)))

        return successors

    def reconstruct_path(self, parents, goal):
        """
        Walk backwards from the goal using the parents map
        {state: (parent_state, action)} to build the action sequence.
        """
        path = []
        current = goal

        while parents[current] is not None:
            parent, action = parents[current]
            path.append(action)
            current = parent

        path.reverse()
        return path

    def bfs_search(self, start, goal, walls, grid_size):
        """Breadth-First Search: FIFO queue, explores shallowest nodes first."""
        walls = set(walls)
        start = tuple(start)
        goal = tuple(goal)

        if start == goal:
            return []

        frontier = deque([start])
        reached = {start}
        parents = {start: None}

        while frontier:
            state = frontier.popleft()

            for action, next_state in self.get_successors(state, walls, grid_size):
                if next_state not in reached:
                    reached.add(next_state)
                    parents[next_state] = (state, action)

                    if next_state == goal:
                        return self.reconstruct_path(parents, goal)

                    frontier.append(next_state)

        return []

    def dfs_search(self, start, goal, walls, grid_size):
        """Depth-First Search: LIFO stack, explores deepest nodes first."""
        walls = set(walls)
        start = tuple(start)
        goal = tuple(goal)

        if start == goal:
            return []

        frontier = [start]
        reached = {start}
        parents = {start: None}

        while frontier:
            state = frontier.pop()

            if state == goal:
                return self.reconstruct_path(parents, goal)

            for action, next_state in self.get_successors(state, walls, grid_size):
                if next_state not in reached:
                    reached.add(next_state)
                    parents[next_state] = (state, action)
                    frontier.append(next_state)

        return []

    def ucs_search(self, start, goal, walls, grid_size):
        """Uniform-Cost Search: priority queue ordered by path cost g(n)."""
        walls = set(walls)
        start = tuple(start)
        goal = tuple(goal)

        if start == goal:
            return []

        # Each entry is (g(n), state). Every move costs 1.
        frontier = [(0, start)]
        cost_so_far = {start: 0}
        reached = set()
        parents = {start: None}

        while frontier:
            g, state = heapq.heappop(frontier)

            if state in reached:
                continue
            reached.add(state)

            if state == goal:
                return self.reconstruct_path(parents, goal)

            for action, next_state in self.get_successors(state, walls, grid_size):
                new_cost = g + 1

                if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
                    cost_so_far[next_state] = new_cost
                    parents[next_state] = (state, action)
                    heapq.heappush(frontier, (new_cost, next_state))

        return []
