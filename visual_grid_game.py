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
        self.agent_pos = [0, 0]
        self.agent_direction = "Up"

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

    def execute_action(self, action: str):
        """
        Execute one movement action for the agent.
        """
        self.steps += 1
        self.collision = False

        new_pos = list(self.agent_pos)

        if action == "Up":
            self.agent_direction = "Up"
            new_pos[1] = min(self.height - 1, new_pos[1] + 1)

        elif action == "Down":
            self.agent_direction = "Down"
            new_pos[1] = max(0, new_pos[1] - 1)

        elif action == "Left":
            self.agent_direction = "Left"
            new_pos[0] = max(0, new_pos[0] - 1)

        elif action == "Right":
            self.agent_direction = "Right"
            new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        else:
            print(f"Unknown action: {action}")
            return

        # Wall collision
        if tuple(new_pos) in self.walls:
            self.score -= 5
            print("Wall hit! Score reduced by 5.")
        else:
            self.agent_pos = new_pos

            # Toxic trap collision
            if tuple(self.agent_pos) in self.toxic_traps:
                self.score -= 15
                print("Toxic trap encountered! Score reduced by 15.")

        # Food collection
        current_pos = tuple(self.agent_pos)

        if current_pos in self.food_positions:
            self.food_positions.remove(current_pos)
            self.score += 20
            print("Food collected! Score increased by 20.")

        # Move opponents
        for opponent in self.opponents:
            self.move_opponent(opponent)

            if opponent == self.agent_pos:
                self.score -= 50
                self.collision = True
                print("Opponent collision! Score reduced by 50.")

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
        return (
            len(self.food_positions) == 0
            or self.steps >= 60
            or self.collision
        )


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
                action = random.choice(["Up", "Down", "Left", "Right"])
                self.env.execute_action(action)
                percept = self.env.get_percept()

                print(
                    f"Action: {action} | "
                    f"Facing: {self.env.agent_direction} | "
                    f"Wall ahead: {percept['wall_ahead']} | "
                    f"Food here: {percept['food_here']}"
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
                elif len(self.env.food_positions) == 0:
                    end_text = (
                        "All food collected! "
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


if __name__ == "__main__":
    root = tk.Tk()

    app = GridGameGUI(
        root,
        width=12,
        height=12,
        num_food=15,
        num_opponents=2,
        num_traps=4,
    )

    root.mainloop()