import random
import tkinter as tk


class VisualGridHuntGame:
    """
    A grid environment where an agent collects food, avoids walls,
    opponents, and toxic traps.
    """

    def __init__(
        self,
        width=10,
        height=10,
        num_food=10,
        num_opponents=2,
        num_traps=3,
        custom_walls=None,
    ):
        self.width = width
        self.height = height
        self.agent_pos = [4, 2]
        self.agent_direction = "Down"
        
        # Create walls
        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            self.walls = {
                (2, 2),
                (2, 3),
                (5, 5),
                (6, 5),
                (3, 7),
            }

        # Create food positions
        self.food_positions = set()

        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            food_pos = (fx, fy)

            if food_pos != (0, 0) and food_pos not in self.walls:
                self.food_positions.add(food_pos)

        # Create opponent positions
        self.opponents = []

        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            opponent_pos = [ox, oy]

            if (
                tuple(opponent_pos) != (0, 0)
                and tuple(opponent_pos) not in self.walls
                and tuple(opponent_pos) not in self.food_positions
                and opponent_pos not in self.opponents
            ):
                self.opponents.append(opponent_pos)

        # Create toxic traps
        self.toxic_traps = set()

        while len(self.toxic_traps) < num_traps:
            tx = random.randint(0, self.width - 1)
            ty = random.randint(0, self.height - 1)
            trap_pos = (tx, ty)

            opponent_positions = {
                tuple(opponent) for opponent in self.opponents
            }

            if (
                trap_pos != (0, 0)
                and trap_pos not in self.walls
                and trap_pos not in self.food_positions
                and trap_pos not in opponent_positions
            ):
                self.toxic_traps.add(trap_pos)

        self.score = 0
        self.steps = 0
        self.collision = False

    def get_percept(self) -> dict:
        x, y = self.agent_pos

        # Find the adjacent cell in the current facing direction
        if self.agent_direction == "Up":
            ahead = (x, y + 1)
        elif self.agent_direction == "Down":
            ahead = (x, y - 1)
        elif self.agent_direction == "Left":
            ahead = (x - 1, y)
        else:  # Right
            ahead = (x + 1, y)

        ahead_x, ahead_y = ahead

        # A boundary is also treated as a wall
        outside_grid = (
            ahead_x < 0
            or ahead_x >= self.width
            or ahead_y < 0
            or ahead_y >= self.height
        )

        wall_ahead = outside_grid or ahead in self.walls
        food_here = tuple(self.agent_pos) in self.food_positions

        return {
            "wall_ahead": wall_ahead,
            "food_here": food_here,
        }

    def turn_left(self):
        left_turns = {
            "Up": "Left",
            "Left": "Down",
            "Down": "Right",
            "Right": "Up"
        }
        self.agent_direction = left_turns[self.agent_direction]

    def turn_right(self):
        right_turns = {
            "Up": "Right",
            "Right": "Down",
            "Down": "Left",
            "Left": "Up",
        }
        self.agent_direction = right_turns[self.agent_direction]

    def get_forward_position(self):
        x, y = self.agent_pos
        if self.agent_direction == "Up":
            return [x, y + 1]
        elif self.agent_direction == "Down":
            return [x, y - 1]
        elif self.agent_direction == "Left":
            return [x - 1, y]
        else:
            return [x + 1, y]

    def execute_action(self, action: str):
        self.steps += 1
        self.collision = False

        if action == "Suck":
            current_pos = tuple(self.agent_pos)
            if current_pos in self.food_positions:
                self.food_positions.remove(current_pos)
                self.score += 20
            return

        elif action == "TurnLeft":
            self.turn_left()
            return
        elif action == "TurnRight":
            self.turn_right()
            return
        elif action == "MoveForward":
            new_pos = self.get_forward_position()
        else:
            print(f"Unknown action: {action}")
            return

        new_x, new_y = new_pos
        outside_grid = (
            new_x < 0 or new_x >= self.width or
            new_y < 0 or new_y >= self.height
        )

        if outside_grid or tuple(new_pos) in self.walls:
            print("Wall ahead. Cannot move.")
        else:
            self.agent_pos = new_pos

    def move_opponent(self, opponent):
        """
        Move an opponent randomly while keeping it inside the grid
        and preventing it from entering walls.
        """
        possible_moves = ["Up", "Down", "Left", "Right", "Stay"]
        move = random.choice(possible_moves)
        new_pos = list(opponent)

        if move == "Up":
            new_pos[1] = min(self.height - 1, new_pos[1] + 1)
        elif move == "Down":
            new_pos[1] = max(0, new_pos[1] - 1)
        elif move == "Left":
            new_pos[0] = max(0, new_pos[0] - 1)
        elif move == "Right":
            new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        if tuple(new_pos) not in self.walls:
            opponent[0] = new_pos[0]
            opponent[1] = new_pos[1]

    def is_done(self) -> bool:
        """
        End the game when all food is collected, the maximum
        number of steps is reached, or a collision occurs.
        """
        return self.steps >= 60 or self.collision

class SimpleReflexAgent:
    """
    A simple reflex agent that uses only the current percept.
    It does not store any history.
    """

    def sense_and_act(self, percept):
        if percept["food_here"]:
            return "Suck"
        elif percept["wall_ahead"]:
            return "TurnLeft"
        else:
            return "MoveForward"


class ModelBasedAgent:

    def __init__(self):
        self.current_position = (4, 2)
        self.direction = "Down"

        self.visited_cells = {(4, 2)}
        self.last_action = None
        self.previous_percepts = []
        self.repeated_states = {}

    def update_internal_state(self, percept):
        # Record the current percept
        self.previous_percepts.append(percept.copy())

        # Update estimated position or direction
        # using the previous action
        if self.last_action == "MoveForward":
            x, y = self.current_position

            if self.direction == "Up":
                self.current_position = (x, y + 1)

            elif self.direction == "Down":
                self.current_position = (x, y - 1)

            elif self.direction == "Left":
                self.current_position = (x - 1, y)

            elif self.direction == "Right":
                self.current_position = (x + 1, y)

            self.visited_cells.add(self.current_position)

        elif self.last_action == "TurnLeft":
            left_turns = {
                "Up": "Left",
                "Left": "Down",
                "Down": "Right",
                "Right": "Up"
            }

            self.direction = left_turns[self.direction]

        elif self.last_action == "TurnRight":
            right_turns = {
                "Up": "Right",
                "Right": "Down",
                "Down": "Left",
                "Left": "Up"
            }

            self.direction = right_turns[self.direction]

    def get_cell_ahead(self):
        x, y = self.current_position

        if self.direction == "Up":
            return (x, y + 1)

        elif self.direction == "Down":
            return (x, y - 1)

        elif self.direction == "Left":
            return (x - 1, y)

        else:
            return (x + 1, y)

    def get_left_cell(self):
        left_turns = {
            "Up": "Left",
            "Left": "Down",
            "Down": "Right",
            "Right": "Up"
        }

        left_direction = left_turns[self.direction]
        x, y = self.current_position

        if left_direction == "Up":
            return (x, y + 1)

        elif left_direction == "Down":
            return (x, y - 1)

        elif left_direction == "Left":
            return (x - 1, y)

        else:
            return (x + 1, y)

    def sense_and_act(self, percept):
        # Update memory first
        self.update_internal_state(percept)

        state = (
            self.current_position,
            self.direction,
            percept["wall_ahead"],
            percept["food_here"]
        )

        self.repeated_states[state] = (
            self.repeated_states.get(state, 0) + 1
        )

        left_cell = self.get_left_cell()
        forward_cell = self.get_cell_ahead()

        # IF food is here, collect it
        if percept["food_here"]:
            action = "Suck"

        # IF the same state repeats, choose another direction
        elif self.repeated_states[state] > 1:
            action = "TurnRight"

        # IF wall ahead and left cell was visited, turn right
        elif (
            percept["wall_ahead"]
            and left_cell in self.visited_cells
        ):
            action = "TurnRight"

        # IF wall ahead, turn left
        elif percept["wall_ahead"]:
            action = "TurnLeft"

        # IF forward cell was visited, turn right
        elif forward_cell in self.visited_cells:
            action = "TurnRight"

        # Otherwise move forward
        else:
            action = "MoveForward"

        self.last_action = action
        return action
class GridGameGUI:
    """
    Tkinter graphical interface for the grid environment.
    """

    def __init__(
        self,
        root,
        width=10,
        height=10,
        num_food=12,
        num_opponents=2,
        num_traps=3,
        walls=None,
    ):
        self.root = root
        self.root.title("SE3062 - Multi-Agent Grid Hunt")

        self.env = VisualGridHuntGame(
            width=width,
            height=height,
            num_food=num_food,
            num_opponents=num_opponents,
            num_traps=num_traps,
            custom_walls=walls,
        )
        self.agent = ModelBasedAgent()

        max_canvas_dimension = 600

        self.cell_size = max(
            20,
            min(
                max_canvas_dimension // self.env.width,
                max_canvas_dimension // self.env.height,
            ),
        )

        canvas_width = self.env.width * self.cell_size
        canvas_height = self.env.height * self.cell_size

        self.canvas = tk.Canvas(
            root,
            width=canvas_width,
            height=canvas_height,
            bg="white",
        )
        self.canvas.pack()

        self.label = tk.Label(
            root,
            text="Score: 0 | Steps: 0",
            font=("Arial", 14),
        )
        self.label.pack(pady=10)

        self.start_button = tk.Button(
            root,
            text="Start Simulation",
            command=self.run_loop,
            font=("Arial", 12),
            bg="#000066",
            fg="white",
        )
        self.start_button.pack(pady=5)

        self.legend_label = tk.Label(
            root,
            text=(
                "Blue: Agent | Orange: Food | "
                "Grey: Wall | Red: Opponent | "
                "Purple: Toxic Trap"
            ),
            font=("Arial", 10),
        )
        self.legend_label.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):
        """
        Draw the grid, walls, food, traps, opponents,
        and the agent.
        """
        self.canvas.delete("all")

        # Draw cells and walls
        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                if (x, y) in self.env.walls:
                    color = "#64748b"
                else:
                    color = "#f1f5f9"

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline="#cbd5e1",
                )

                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(
                        x1 + self.cell_size / 2,
                        y1 + self.cell_size / 2,
                        text="W",
                        fill="white",
                        font=("Arial", 8, "bold"),
                    )

        # Draw food
        for food_x, food_y in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = food_x * self.cell_size + offset
            y1 = (self.env.height - 1 - food_y) * self.cell_size + offset

            self.canvas.create_oval(
                x1,
                y1,
                x1 + self.cell_size * 0.5,
                y1 + self.cell_size * 0.5,
                fill="#f59e0b",
                outline="#d97706",
            )

        # Draw toxic traps as purple diamonds
        for trap_x, trap_y in self.env.toxic_traps:
            cell_x = trap_x * self.cell_size
            cell_y = (self.env.height - 1 - trap_y) * self.cell_size
            center_x = cell_x + self.cell_size / 2
            center_y = cell_y + self.cell_size / 2
            margin = self.cell_size * 0.18

            self.canvas.create_polygon(
                center_x,
                cell_y + margin,
                cell_x + self.cell_size - margin,
                center_y,
                center_x,
                cell_y + self.cell_size - margin,
                cell_x + margin,
                center_y,
                fill="#9333ea",
                outline="#581c87",
                width=2,
            )

            if self.cell_size >= 40:
                self.canvas.create_text(
                    center_x,
                    center_y,
                    text="T",
                    fill="white",
                    font=("Arial", 9, "bold"),
                )

        # Draw opponents
        for opponent_x, opponent_y in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = opponent_x * self.cell_size + offset
            y1 = (self.env.height - 1 - opponent_y) * self.cell_size + offset

            self.canvas.create_rectangle(
                x1,
                y1,
                x1 + self.cell_size * 0.6,
                y1 + self.cell_size * 0.6,
                fill="#990000",
                outline="#7a0000",
            )

        # Draw the main agent
        agent_x, agent_y = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = agent_x * self.cell_size + offset
        y1 = (self.env.height - 1 - agent_y) * self.cell_size + offset

        self.canvas.create_oval(
            x1,
            y1,
            x1 + self.cell_size * 0.7,
            y1 + self.cell_size * 0.7,
            fill="#000066",
            outline="#1e3a8a",
        )

    def run_loop(self):
        """
        Start the automatic simulation.
        """
        self.start_button.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)
                self.env.execute_action(action)
                percept = self.env.get_percept()

                print(
                    f"Percept: {percept} | "
                    f"Action: {action} | "
                    f"Facing: {self.env.agent_direction} | "
                    f"Estimated position: "
                    f"{self.agent.current_position} | "
                    f"Visited: {self.agent.visited_cells}"
                )

                self.draw_grid()

                self.label.config(
                    text=(
                        f"Score: {self.env.score} | "
                        f"Steps: {self.env.steps} | "
                        f"Action: {action}"
                    )
                )

                self.root.after(250, step)

            else:
                if self.env.collision:
                    end_text = (
                        "Collision! Game Over! "
                        f"Final Score: {self.env.score}"
                    )
                else:
                    end_text = (
                        "Maximum steps reached! "
                        f"Final Score: {self.env.score}"
                    )

                self.label.config(text=end_text)
                self.start_button.config(state="normal")

        step()
u_shaped_walls = {
    (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
    (3, 1), (4, 1), (5, 1), (6, 1),
    (6, 2), (6, 3), (6, 4), (6, 5)
}

if __name__ == "__main__":
    root = tk.Tk()

    app = GridGameGUI(
        root,
        width=10,
        height=10,
        num_food=5,
        num_opponents=0,
        num_traps=0,
        walls=u_shaped_walls
    )

    root.mainloop()