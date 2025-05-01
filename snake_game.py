import os
import random
import time
import msvcrt
import sys
from time import perf_counter
from colorama import Fore, Back, Style, init

# Initialize colorama with proper Windows terminal support
init(autoreset=True, convert=True)

# Constants for ANSI control codes
CURSOR_HOME = '\033[H'
CLEAR_SCREEN = '\033[2J'
CLEAR_LINE = '\033[K'
HIDE_CURSOR = '\033[?25l'
SHOW_CURSOR = '\033[?25h'

class SnakeGame:
    def __init__(self, width=20, height=10):
        self.width = width
        self.height = height
        self.snake = [(width // 2, height // 2)]  # Start with snake in the middle
        self.direction = (1, 0)  # Initially moving right
        self.next_direction = (1, 0)  # For direction buffering
        self.food = self.generate_food()
        self.score = 0
        self.game_over = False
        self.speed = 0.2  # Initial game speed (seconds between moves) - slower for better control
        self.previous_board = None  # For screen buffering
        self.max_speed = 0.08  # Maximum speed (minimum delay) - not too frantic
        self.speed_factor = 0.99  # Factor for speed increase - more gradual progression
        
        # Interpolation variables for smooth movement
        self.move_progress = 0.0  # Progress between moves (0.0 to 1.0)
        self.last_positions = []  # For tracking previous positions
        
        # Direction change control
        self.last_direction_change = 0  # Last time direction was changed
        self.direction_change_delay = 0.05  # Minimum time between direction changes
    
    def generate_food(self):
        """Generate food at a random position not occupied by the snake"""
        while True:
            food = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            if food not in self.snake:
                return food
    
    def change_direction(self, key):
        """Change snake direction based on key press with buffering to prevent instant reversal"""
        current_time = perf_counter()
        
        # Check if enough time has passed since last direction change
        if current_time - self.last_direction_change < self.direction_change_delay:
            return
        
        new_direction = None
        
        # Arrow keys and WASD
        if key == b'w' or key == b'H':  # Up arrow or W
            new_direction = (0, -1)
        elif key == b's' or key == b'P':  # Down arrow or S
            new_direction = (0, 1)
        elif key == b'a' or key == b'K':  # Left arrow or A
            new_direction = (-1, 0)
        elif key == b'd' or key == b'M':  # Right arrow or D
            new_direction = (1, 0)
            
        # Only change direction if not going in opposite direction
        if new_direction:
            opposite_dir = (-self.direction[0], -self.direction[1])
            if new_direction != opposite_dir:
                self.next_direction = new_direction
                self.last_direction_change = current_time
    
    def move(self):
        """Move the snake one step in the current direction"""
        if self.game_over:
            return
        
        # Apply buffered direction change
        self.direction = self.next_direction
        
        # Reset move progress for new movement step
        self.move_progress = 0.0
        
        # Save previous positions for interpolation
        self.last_positions = [(x, y) for x, y in self.snake]
        
        # Calculate new head position
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % self.width, (head_y + dy) % self.height)
        
        # Check collision with self
        if new_head in self.snake:
            self.game_over = True
            return
        
        # Add new head
        self.snake.insert(0, new_head)
        
        # Check if food was eaten
        if new_head == self.food:
            self.score += 1
            self.food = self.generate_food()
            # Speed up more smoothly with each food eaten
            if self.speed > self.max_speed:
                # Smooth progression with diminishing returns
                self.speed = max(self.max_speed, self.speed * self.speed_factor)
        else:
            # Remove tail if no food was eaten
            self.snake.pop()
    
    def update_progress(self, delta_time):
        """Update movement progress for interpolation"""
        if not self.game_over and len(self.last_positions) > 0:
            # Calculate how much to advance the movement progress
            # We want to reach 1.0 when it's time for the next move
            self.move_progress = min(1.0, self.move_progress + (delta_time / self.speed))

    def get_segment_character(self, index):
        """Determine the appropriate character for a snake segment based on its position and neighbors"""
        if index >= len(self.snake):
            return ' '
            
        # For the head, use directional characters
        if index == 0:
            dx, dy = self.direction
            if dx == 1:  # Right
                return Fore.GREEN + '▶'
            elif dx == -1:  # Left
                return Fore.GREEN + '◀'
            elif dy == 1:  # Down
                return Fore.GREEN + '▼'
            else:  # Up
                return Fore.GREEN + '▲'
                
        # For the tail
        if index == len(self.snake) - 1:
            return Fore.LIGHTGREEN_EX + '▪'
            
        # For body segments, determine connection type
        prev_x, prev_y = self.snake[index - 1]
        curr_x, curr_y = self.snake[index]
        next_x, next_y = self.snake[index + 1]
        
        # Determine direction to previous and next segments
        dx1 = prev_x - curr_x
        dy1 = prev_y - curr_y
        dx2 = next_x - curr_x
        dy2 = next_y - curr_y
        
        # Handle wrap-around for directions
        if abs(dx1) > 1:  # Wrapped horizontally
            dx1 = -1 if dx1 > 0 else 1
        if abs(dy1) > 1:  # Wrapped vertically
            dy1 = -1 if dy1 > 0 else 1
        if abs(dx2) > 1:  # Wrapped horizontally
            dx2 = -1 if dx2 > 0 else 1
        if abs(dy2) > 1:  # Wrapped vertically
            dy2 = -1 if dy2 > 0 else 1
            
        # Determine character based on connection directions
        if (dx1 == 0 and dx2 == 0) or (dy1 == 0 and dy2 == 0):
            # Straight horizontal or vertical segment
            return Fore.LIGHTGREEN_EX + ('─' if dy1 == 0 and dy2 == 0 else '│')
        else:
            # Corner segment
            if (dx1 == -1 and dy2 == -1) or (dx2 == -1 and dy1 == -1):
                return Fore.LIGHTGREEN_EX + '┐'
            elif (dx1 == 1 and dy2 == -1) or (dx2 == 1 and dy1 == -1):
                return Fore.LIGHTGREEN_EX + '┌'
            elif (dx1 == -1 and dy2 == 1) or (dx2 == -1 and dy1 == 1):
                return Fore.LIGHTGREEN_EX + '┘'
            elif (dx1 == 1 and dy2 == 1) or (dx2 == 1 and dy1 == 1):
                return Fore.LIGHTGREEN_EX + '└'
            else:
                return Fore.LIGHTGREEN_EX + '●'  # Fallback

    def draw(self):
        """Draw the game board"""
        # Create current board state
        board = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Place snake on board with proper segment characters
        for i, (x, y) in enumerate(self.snake):
            board[y][x] = self.get_segment_character(i)
        
        # Place food on board
        x, y = self.food
        board[y][x] = Fore.RED + '♦'  # Food (diamond shape is distinct from snake)
        
        # Create a more reliable string representation for comparison
        current_board_str = ''.join([''.join(row) for row in board]) + str(self.score) + str(self.game_over)
        
        # Only redraw if the board has changed or this is the first draw
        if self.previous_board != current_board_str:
            self.previous_board = current_board_str
            
            # Move cursor to home position
            sys.stdout.write(CURSOR_HOME)
            
            # Draw title bar
            sys.stdout.write(f"{Fore.CYAN}Snake Game - {Fore.YELLOW}Score: {self.score}{CLEAR_LINE}\n")
            
            # Draw top border
            sys.stdout.write(f"{Fore.CYAN}┌{'─' * self.width}┐{CLEAR_LINE}\n")
            
            # Draw board content
            for row in board:
                sys.stdout.write(f"{Fore.CYAN}│{''.join(row)}{Fore.CYAN}│{CLEAR_LINE}\n")
            
            # Draw bottom border
            sys.stdout.write(f"{Fore.CYAN}└{'─' * self.width}┘{CLEAR_LINE}\n")
            
            # Print status message (game over or controls)
            if self.game_over:
                sys.stdout.write(f"{Fore.RED}Game Over! {Fore.WHITE}Press 'R' to restart or 'Q' to quit.{CLEAR_LINE}\n")
            else:
                sys.stdout.write(f"{Fore.WHITE}Use WASD or arrow keys to move. {Fore.YELLOW}Speed: {1/self.speed:.1f} moves/sec{CLEAR_LINE}\n")
            
            # Force display update
            sys.stdout.flush()


def run_game():
    """Run the snake game"""
    # Constants for frame control
    TARGET_FPS = 60  # 60 frames per second for smooth visuals
    FRAME_TIME = 1.0 / TARGET_FPS
    
    # Ensure terminal is in the right mode and clear any previous content
    os.system('cls')  # First clear with native Windows command
    print(CLEAR_SCREEN, end='')  # Then use ANSI clear to be thorough
    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()
    
    # Short delay to ensure terminal is ready
    time.sleep(0.1)
    
    # Display welcome screen
    print(f"{Fore.CYAN}╔═════════════════════════════════╗")
    print(f"{Fore.CYAN}║       {Fore.YELLOW}SNAKE GAME{Fore.CYAN}              ║")
    print(f"{Fore.CYAN}╠═════════════════════════════════╣")
    print(f"{Fore.CYAN}║ {Fore.WHITE}Use WASD or arrow keys to move  {Fore.CYAN}║")
    print(f"{Fore.CYAN}║ {Fore.WHITE}Eat {Fore.RED}♦{Fore.WHITE} food to grow and score      {Fore.CYAN}║")
    print(f"{Fore.CYAN}║ {Fore.WHITE}Snake head looks like: {Fore.GREEN}▶ ◀ ▼ ▲{Fore.WHITE}    {Fore.CYAN}║")
    print(f"{Fore.CYAN}║ {Fore.WHITE}Don't hit yourself!             {Fore.CYAN}║")
    print(f"{Fore.CYAN}║                                 {Fore.CYAN}║")
    print(f"{Fore.CYAN}║ {Fore.GREEN}Press any key to start...        {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚═════════════════════════════════╝")
    sys.stdout.flush()  # Ensure welcome screen is displayed
    
    # Small delay to ensure everything is visible
    time.sleep(0.3)
    
    # Wait for key press to start
    msvcrt.getch()
    
    # Initialize the game
    game = SnakeGame()
    
    # Make sure keyboard buffer is clear before starting
    while msvcrt.kbhit():
        msvcrt.getch()  # Clear any pending keystrokes
    
    # Timing variables
    last_move_time = perf_counter()
    last_frame_time = perf_counter()
    
    # Clear screen and reset cursor position before game starts
    os.system('cls')  # Use Windows cls for a complete clear
    sys.stdout.write(CURSOR_HOME)
    sys.stdout.flush()

    while True:
        frame_start_time = perf_counter()
        
        # Check for keyboard input - always process input immediately
        if msvcrt.kbhit():
            key = msvcrt.getch()
            
            # Check for restart or quit if game over
            if game.game_over:
                if key == b'r' or key == b'R':
                    # Create a new game and reset timers
                    game = SnakeGame()
                    last_move_time = perf_counter()
                    last_frame_time = perf_counter()
                    
                    # Clear screen for fresh start
                    os.system('cls')
                elif key == b'q' or key == b'Q':
                    break
            # If game is active, process direction changes
            else:
                game.change_direction(key)
        # Current time for timing calculations
        current_time = perf_counter()
        
        # Calculate delta time for this frame (time since last frame)
        delta_time = current_time - last_frame_time
        
        # Update interpolation progress
        game.update_progress(delta_time)
        
        # Move snake at regular intervals based on game speed
        if current_time - last_move_time > game.speed:
            game.move()
            last_move_time = current_time
        
        # Update display at consistent frame rate
        frame_elapsed = current_time - last_frame_time
        if frame_elapsed >= FRAME_TIME:
            # Update display
            game.draw()
            
            # Update frame timing with adjustment for timing drift
            last_frame_time = current_time - (frame_elapsed % FRAME_TIME)
        
        # Calculate how long to sleep to maintain frame rate with high precision
        frame_end_time = perf_counter()
        frame_duration = frame_end_time - frame_start_time
        
        # Calculate sleep time ensuring we don't oversleep and maintain consistent frame rate
        # We use max() to ensure we don't get negative sleep times
        sleep_time = max(0.001, FRAME_TIME - frame_duration)  # Ensure at least 1ms sleep to prevent CPU hogging
        
        # Small delay to reduce CPU usage while maintaining frame rate
        time.sleep(sleep_time)
    
    # Clear screen and show cursor before exiting
    os.system('cls')
    sys.stdout.write(SHOW_CURSOR)
    sys.stdout.flush()
    time.sleep(0.2)  # Brief pause before exit message
    print(f"{Fore.CYAN}Thanks for playing Snake Game!")

if __name__ == "__main__":
    try:
        # Ensure we have a fresh terminal state before starting
        os.system('cls')
        run_game()
    except KeyboardInterrupt:
        # Ensure cursor is visible if the game is interrupted
        os.system('cls')
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()
        time.sleep(0.2)  # Brief pause
        print(f"{Fore.YELLOW}Game terminated by user.")
    except Exception as e:
        # Show cursor and report any errors
        os.system('cls')
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()
        time.sleep(0.2)  # Brief pause
        print(f"{Fore.RED}An error occurred: {e}")
        import traceback
        traceback.print_exc()  # Print full error details

