import pygame
import sys
import random
from PIL import Image
import heapq

# Initialize pygame
pygame.init()

# Initial game settings
INITIAL_GRID_SIZE = 3  # Default 3x3 grid
TILE_SIZE = 150
CONTROLS_WIDTH = 200  # Width for controls panel

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (120, 120, 120)
LIGHT_BLUE = (173, 216, 230)

# Create screen (will be resized later)
screen = pygame.display.set_mode((INITIAL_GRID_SIZE * TILE_SIZE + CONTROLS_WIDTH, INITIAL_GRID_SIZE * TILE_SIZE))
pygame.display.set_caption("N-Puzzle Game with A* Solver")

# Define button class
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = pygame.font.SysFont(None, 30)
        
    def draw(self):
        # Draw button
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=5)
        
        # Draw text
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)
    
    def update(self, mouse_pos):
        if self.is_hovered(mouse_pos):
            self.current_color = self.hover_color
        else:
            self.current_color = self.color

# Define text input box class
class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = BLACK
        self.text = text
        self.font = pygame.font.SysFont(None, 30)
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle active if clicked on the input box
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            # Change color based on active state
            self.color = BLUE if self.active else BLACK
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return self.text  # Return the text when Enter is pressed
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    # Only allow numeric input
                    if event.unicode.isdigit():
                        self.text += event.unicode
                # Re-render the text
                self.txt_surface = self.font.render(self.text, True, self.color)
        return None

    def update(self):
        # Resize the box if the text is too long
        width = max(60, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Draw the text
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Draw the rect
        pygame.draw.rect(screen, self.color, self.rect, 2, border_radius=5)


def load_and_split_image(image_path, grid_size, tile_size):
    """Load an image and split it into tiles"""
    puzzle_width = grid_size * tile_size
    try:
        img = Image.open(image_path)
        img = img.resize((puzzle_width, puzzle_width))  # Use puzzle_width for square image

        tiles = []
        for y in range(grid_size):
            for x in range(grid_size):
                left = x * tile_size
                upper = y * tile_size
                right = left + tile_size
                lower = upper + tile_size
                tile = img.crop((left, upper, right, lower))
                tiles.append(tile)
        return tiles
    except:
        # If no image, create colored tiles as fallback
        tiles = []
        for i in range(grid_size * grid_size):
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            tile = Image.new("RGB", (tile_size, tile_size), color)
            tiles.append(tile)
        return tiles


def create_solvable_board(grid_size):
    """Create a shuffled but solvable puzzle board"""
    while True:
        board = list(range(grid_size * grid_size))
        board[-1] = -1  # Use -1 instead of None for empty tile
        random.shuffle(board)

        # Check if the puzzle is solvable
        if is_solvable(board, grid_size):
            return board


def is_solvable(board, grid_size):
    """Check if the puzzle is solvable"""
    # Count inversions ignoring the empty tile (-1)
    inversions = 0
    flat_board = [x for x in board if x != -1]

    for i in range(len(flat_board)):
        for j in range(i + 1, len(flat_board)):
            if flat_board[i] > flat_board[j]:
                inversions += 1

    # For odd grid sizes, solvable if inversions are even
    if grid_size % 2 == 1:
        return inversions % 2 == 0
    else:
        # For even grid sizes, need to consider row of blank
        blank_row = board.index(-1) // grid_size
        return (inversions + blank_row) % 2 == 1


def draw_board(board, tiles, buttons, input_box, grid_size, tile_size, solving=False, current_move=None, solved=False):
    """Draw the current board state and GUI elements"""
    puzzle_width = grid_size * tile_size
    screen.fill(WHITE)
    
    # Draw right panel with controls (light gray background)
    pygame.draw.rect(screen, GRAY, (puzzle_width, 0, CONTROLS_WIDTH, puzzle_width))
    
    # Draw vertical separator line
    pygame.draw.line(screen, BLACK, (puzzle_width, 0), (puzzle_width, puzzle_width), 2)
    
    # Draw the puzzle board (left side)
    for i, tile_num in enumerate(board):
        if tile_num == -1:
            continue  # Skip empty tile

        row = i // grid_size
        col = i % grid_size

        # Convert PIL image to Pygame surface
        tile_surface = pygame.image.fromstring(
            tiles[tile_num].tobytes(), tiles[tile_num].size, tiles[tile_num].mode
        )

        # Highlight the tile being moved by AI
        if solving and i == current_move:
            highlight = pygame.Surface((tile_size, tile_size))
            highlight.fill(GREEN)
            screen.blit(highlight, (col * tile_size, row * tile_size))

        screen.blit(tile_surface, (col * tile_size, row * tile_size))

        # Draw tile border
        border_color = RED if solving and i == current_move else BLACK
        pygame.draw.rect(
            screen, border_color,
            (col * tile_size, row * tile_size, tile_size, tile_size),
            2  # Margin
        )

    # Draw all buttons
    for button in buttons:
        button.draw()
        
    # Draw input box
    input_box.draw(screen)
    
    # Draw label for input box
    font = pygame.font.SysFont(None, 30)
    label = font.render("Grid Size:", True, BLACK)
    screen.blit(label, (input_box.rect.x, input_box.rect.y - 30))

    # Display mode on the right panel
    font = pygame.font.SysFont(None, 36)
    mode_text = "AI Solving..." if solving else "Manual Mode"
    text_surface = font.render(mode_text, True, BLUE)
    text_rect = text_surface.get_rect(center=(puzzle_width + CONTROLS_WIDTH//2, 50))
    screen.blit(text_surface, text_rect)

    # Display congratulations message if solved
    if solved:
        congrats_font = pygame.font.SysFont(None, 60)
        congrats_text = congrats_font.render("Congratulations!", True, YELLOW)
        text_rect = congrats_text.get_rect(center=(puzzle_width//2, puzzle_width//2))
        # Create a semi-transparent background for the text
        s = pygame.Surface((text_rect.width + 20, text_rect.height + 20))
        s.set_alpha(200)
        s.fill(BLACK)
        screen.blit(s, (text_rect.x - 10, text_rect.y - 10))
        screen.blit(congrats_text, text_rect)

    pygame.display.flip()


def get_empty_pos(board, grid_size):
    """Get the position of the empty tile"""
    for i, tile in enumerate(board):
        if tile == -1:
            return (i % grid_size, i // grid_size)  # (col, row)
    return None


def move_tile(board, direction, grid_size):
    """Move a tile in the specified direction"""
    empty_col, empty_row = get_empty_pos(board, grid_size)
    empty_idx = empty_row * grid_size + empty_col

    if direction == "up" and empty_row < grid_size - 1:
        swap_idx = (empty_row + 1) * grid_size + empty_col
        board[empty_idx], board[swap_idx] = board[swap_idx], board[empty_idx]
        return swap_idx  # Return the index of the tile that moved
    elif direction == "down" and empty_row > 0:
        swap_idx = (empty_row - 1) * grid_size + empty_col
        board[empty_idx], board[swap_idx] = board[swap_idx], board[empty_idx]
        return swap_idx
    elif direction == "left" and empty_col < grid_size - 1:
        swap_idx = empty_row * grid_size + (empty_col + 1)
        board[empty_idx], board[swap_idx] = board[swap_idx], board[empty_idx]
        return swap_idx
    elif direction == "right" and empty_col > 0:
        swap_idx = empty_row * grid_size + (empty_col - 1)
        board[empty_idx], board[swap_idx] = board[swap_idx], board[empty_idx]
        return swap_idx
    else:
        return None  # Invalid move


def is_solved(board, grid_size):
    """Check if the puzzle is solved"""
    for i in range(len(board) - 1):
        if board[i] != i:
            return False
    return board[-1] == -1


def heuristic(board, grid_size):
    """Calculate Manhattan distance heuristic for A*"""
    distance = 0
    for i in range(grid_size * grid_size):
        if board[i] == -1:
            continue
        # Current position
        current_row, current_col = i // grid_size, i % grid_size
        # Goal position
        goal_row, goal_col = board[i] // grid_size, board[i] % grid_size
        # Add Manhattan distance for this tile
        distance += abs(current_row - goal_row) + abs(current_col - goal_col)
    return distance


def a_star_solve(initial_board, tiles, grid_size):
    """Solve the puzzle using A* algorithm"""
    # Priority queue: (priority, step, board, path)
    heap = []
    # Use a tuple that can be properly compared by heapq
    initial_priority = (0 + heuristic(initial_board, grid_size), 0, 0, initial_board[:], [])
    heapq.heappush(heap, initial_priority)

    visited = set()
    visited.add(tuple(initial_board))

    directions = ["up", "down", "left", "right"]
    tiebreaker = 1  # To ensure proper comparison in heap

    while heap:
        _, steps, _, current_board, path = heapq.heappop(heap)

        if is_solved(current_board, grid_size):
            return path

        for direction in directions:
            new_board = current_board[:]
            moved_tile = move_tile(new_board, direction, grid_size)

            if moved_tile is not None:
                board_tuple = tuple(new_board)
                if board_tuple not in visited:
                    visited.add(board_tuple)
                    new_path = path + [(direction, moved_tile)]
                    priority = steps + 1 + heuristic(new_board, grid_size)
                    # Add tiebreaker to ensure proper comparison
                    heapq.heappush(heap, (priority, steps + 1, tiebreaker, new_board, new_path))
                    tiebreaker += 1

    return None  # No solution found (shouldn't happen for solvable puzzles)


def main():
    # Initial game state
    grid_size = INITIAL_GRID_SIZE
    tile_size = TILE_SIZE
    puzzle_width = grid_size * tile_size
    height = puzzle_width
    
    # Load and split image
    tiles = load_and_split_image("puzzle_image.jpg", grid_size, tile_size)
    board = create_solvable_board(grid_size)
    
    # Resize screen
    screen = pygame.display.set_mode((puzzle_width + CONTROLS_WIDTH, height))

    # Create buttons - all positioned in the right panel
    control_center_x = puzzle_width + CONTROLS_WIDTH // 2
    
    # Direction buttons
    up_button = Button(control_center_x - 30, height//2 - 90, 60, 40, "Up", GRAY, DARK_GRAY)
    down_button = Button(control_center_x - 30, height//2 + 10, 60, 40, "Down", GRAY, DARK_GRAY)
    left_button = Button(control_center_x - 70, height//2 - 40, 60, 40, "Left", GRAY, DARK_GRAY)
    right_button = Button(control_center_x + 10, height//2 - 40, 60, 40, "Right", GRAY, DARK_GRAY)
    
    # Action buttons
    solve_button = Button(control_center_x - 50, height//2 + 80, 100, 40, "Solve (A*)", GREEN, (100, 255, 100))
    reset_button = Button(control_center_x - 50, height//2 + 140, 100, 40, "Reset", RED, (255, 100, 100))
    
    # Input box for grid size
    input_box = InputBox(control_center_x - 30, height//2 - 150, 60, 32, str(grid_size))
    
    # All buttons
    buttons = [up_button, down_button, left_button, right_button, solve_button, reset_button]

    solving = False
    solution_path = None
    current_step = 0
    solved = False

    draw_board(board, tiles, buttons, input_box, grid_size, tile_size, solving, None, solved)

    running = True
    clock = pygame.time.Clock()
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # Update button hover states
        for button in buttons:
            button.update(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle input box events
            new_grid_size = input_box.handle_event(event)
            if new_grid_size is not None:
                try:
                    new_size = int(new_grid_size)
                    if 2 <= new_size <= 6:  # Reasonable limits for puzzle size
                        if new_size != grid_size:
                            # Change grid size
                            grid_size = new_size
                            tile_size = min(150, 600 // grid_size)  # Adjust tile size to fit
                            puzzle_width = grid_size * tile_size
                            height = puzzle_width
                            
                            # Resize screen
                            screen = pygame.display.set_mode((puzzle_width + CONTROLS_WIDTH, height))
                            
                            # Recreate buttons with new positions
                            control_center_x = puzzle_width + CONTROLS_WIDTH // 2
                            up_button = Button(control_center_x - 30, height//2 - 90, 60, 40, "Up", GRAY, DARK_GRAY)
                            down_button = Button(control_center_x - 30, height//2 + 10, 60, 40, "Down", GRAY, DARK_GRAY)
                            left_button = Button(control_center_x - 70, height//2 - 40, 60, 40, "Left", GRAY, DARK_GRAY)
                            right_button = Button(control_center_x + 10, height//2 - 40, 60, 40, "Right", GRAY, DARK_GRAY)
                            solve_button = Button(control_center_x - 50, height//2 + 80, 100, 40, "Solve (A*)", GREEN, (100, 255, 100))
                            reset_button = Button(control_center_x - 50, height//2 + 140, 100, 40, "Reset", RED, (255, 100, 100))
                            input_box = InputBox(control_center_x - 30, height//2 - 150, 60, 32, str(grid_size))
                            buttons = [up_button, down_button, left_button, right_button, solve_button, reset_button]
                            
                            # Reload tiles and create new board
                            tiles = load_and_split_image("puzzle_image.jpg", grid_size, tile_size)
                            board = create_solvable_board(grid_size)
                            solving = False
                            solution_path = None
                            current_step = 0
                            solved = False
                except ValueError:
                    pass  # Invalid input

            if not solving and not solved:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Reset board
                        board = create_solvable_board(grid_size)
                        solving = False
                        solution_path = None
                        current_step = 0
                        solved = False
                    elif event.key == pygame.K_UP:
                        move_tile(board, "up", grid_size)
                        solved = is_solved(board, grid_size)
                    elif event.key == pygame.K_DOWN:
                        move_tile(board, "down", grid_size)  
                        solved = is_solved(board, grid_size)
                    elif event.key == pygame.K_LEFT:
                        move_tile(board, "left", grid_size)
                        solved = is_solved(board, grid_size)
                    elif event.key == pygame.K_RIGHT:
                        move_tile(board, "right", grid_size)
                        solved = is_solved(board, grid_size)
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if up_button.is_hovered(mouse_pos):
                        move_tile(board, "up", grid_size)
                        solved = is_solved(board, grid_size)
                    elif down_button.is_hovered(mouse_pos):
                        move_tile(board, "down", grid_size)  
                        solved = is_solved(board, grid_size)
                    elif left_button.is_hovered(mouse_pos):
                        move_tile(board, "left", grid_size)
                        solved = is_solved(board, grid_size)
                    elif right_button.is_hovered(mouse_pos):
                        move_tile(board, "right", grid_size)
                        solved = is_solved(board, grid_size)
                    elif solve_button.is_hovered(mouse_pos):
                        # Start AI solver
                        solving = True
                        solution_path = a_star_solve(board, tiles, grid_size)
                        current_step = 0
                    elif reset_button.is_hovered(mouse_pos):
                        # Reset board
                        board = create_solvable_board(grid_size)
                        solving = False
                        solution_path = None
                        current_step = 0
                        solved = False

        # Update input box
        input_box.update()

        # If in solving mode, execute the next move
        if solving and solution_path and current_step < len(solution_path) and not solved:
            direction, moved_tile = solution_path[current_step]
            move_tile(board, direction, grid_size)
            solved = is_solved(board, grid_size)
            draw_board(board, tiles, buttons, input_box, grid_size, tile_size, solving, moved_tile, solved)
            current_step += 1
            pygame.time.delay(300)  # Pause for visibility
            if current_step == len(solution_path) or solved:
                solving = False
                if solved:
                    print("AI has solved the puzzle!")
        else:
            # Redraw board with updated state
            draw_board(board, tiles, buttons, input_box, grid_size, tile_size, solving, None, solved)

        clock.tick(30)  # Limit to 30 frames per second

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
