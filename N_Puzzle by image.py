import pygame
import sys
import random
from PIL import Image
import heapq

# Initialize pygame
pygame.init()

# Game settings
GRID_SIZE = 3  # 3x3 grid
TILE_SIZE = 200
WIDTH, HEIGHT = GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
MARGIN = 2

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)  # Added for congratulations message

# Create screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("N-Puzzle Game with A* Solver")


def load_and_split_image(image_path):
    """Load an image and split it into tiles"""
    try:
        img = Image.open(image_path)
        img = img.resize((WIDTH, HEIGHT))

        tiles = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                left = x * TILE_SIZE
                upper = y * TILE_SIZE
                right = left + TILE_SIZE
                lower = upper + TILE_SIZE
                tile = img.crop((left, upper, right, lower))
                tiles.append(tile)
        return tiles
    except:
        # If no image, create colored tiles as fallback
        tiles = []
        for i in range(GRID_SIZE * GRID_SIZE):
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            tile = Image.new("RGB", (TILE_SIZE, TILE_SIZE), color)
            tiles.append(tile)
        return tiles


def create_solvable_board():
    """Create a shuffled but solvable puzzle board"""
    while True:
        board = list(range(GRID_SIZE * GRID_SIZE))
        board[-1] = -1  # Use -1 instead of None for empty tile
        random.shuffle(board)

        # Check if the puzzle is solvable
        if is_solvable(board):
            return board


def is_solvable(board):
    """Check if the puzzle is solvable (for 3x3)"""
    # Count inversions ignoring the empty tile (-1)
    inversions = 0
    flat_board = [x for x in board if x != -1]

    for i in range(len(flat_board)):
        for j in range(i + 1, len(flat_board)):
            if flat_board[i] > flat_board[j]:
                inversions += 1

    # For odd grid sizes, solvable if inversions are even
    return inversions % 2 == 0


def draw_board(board, tiles, solving=False, current_move=None, solved=False):
    """Draw the current board state"""
    screen.fill(WHITE)

    for i, tile_num in enumerate(board):
        if tile_num == -1:
            continue  # Skip empty tile

        row = i // GRID_SIZE
        col = i % GRID_SIZE

        # Convert PIL image to Pygame surface
        tile_surface = pygame.image.fromstring(
            tiles[tile_num].tobytes(), tiles[tile_num].size, tiles[tile_num].mode
        )

        # Highlight the tile being moved by AI
        if solving and i == current_move:
            highlight = pygame.Surface((TILE_SIZE, TILE_SIZE))
            highlight.fill(GREEN)
            screen.blit(highlight, (col * TILE_SIZE, row * TILE_SIZE))

        screen.blit(tile_surface, (col * TILE_SIZE, row * TILE_SIZE))

        # Draw tile border
        border_color = RED if solving and i == current_move else BLACK
        pygame.draw.rect(
            screen, border_color,
            (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE),
            MARGIN
        )

    # Display mode
    font = pygame.font.SysFont(None, 36)
    mode_text = "AI Solving..." if solving else "Manual Mode"
    text_surface = font.render(mode_text, True, BLUE)
    screen.blit(text_surface, (10, 10))

    # Display congratulations message if solved
    if solved:
        congrats_font = pygame.font.SysFont(None, 72)
        congrats_text = congrats_font.render("Congratulations!", True, YELLOW)
        text_rect = congrats_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        # Create a semi-transparent background for the text
        s = pygame.Surface((text_rect.width + 20, text_rect.height + 20))
        s.set_alpha(200)
        s.fill(BLACK)
        screen.blit(s, (text_rect.x - 10, text_rect.y - 10))
        screen.blit(congrats_text, text_rect)

    pygame.display.flip()


def get_empty_pos(board):
    """Get the position of the empty tile"""
    for i, tile in enumerate(board):
        if tile == -1:
            return (i % GRID_SIZE, i // GRID_SIZE)  # (col, row)
    return None


def move_tile(board, direction):
    """Move a tile in the specified direction"""
    empty_col, empty_row = get_empty_pos(board)
    empty_idx = empty_row * GRID_SIZE + empty_col

    if direction == "up" and empty_row < GRID_SIZE - 1:
        swap_idx = (empty_row + 1) * GRID_SIZE + empty_col
        board[empty_idx], board[swap_idx] = board[swap_idx], board[empty_idx]
        return swap_idx  # Return the index of the tile that moved
    elif direction == "down" and empty_row > 0:
        swap_idx = (empty_row - 1) * GRID_SIZE + empty_col
        board[empty_idx], board[swap_idx] = board[swap_idx], board[empty_idx]
        return swap_idx
    elif direction == "left" and empty_col < GRID_SIZE - 1:
        swap_idx = empty_row * GRID_SIZE + (empty_col + 1)
        board[empty_idx], board[swap_idx] = board[swap_idx], board[empty_idx]
        return swap_idx
    elif direction == "right" and empty_col > 0:
        swap_idx = empty_row * GRID_SIZE + (empty_col - 1)
        board[empty_idx], board[swap_idx] = board[swap_idx], board[empty_idx]
        return swap_idx
    else:
        return None  # Invalid move


def is_solved(board):
    """Check if the puzzle is solved"""
    for i in range(len(board) - 1):
        if board[i] != i:
            return False
    return board[-1] == -1


def heuristic(board):
    """Calculate Manhattan distance heuristic for A*"""
    distance = 0
    for i in range(GRID_SIZE * GRID_SIZE):
        if board[i] == -1:
            continue
        # Current position
        current_row, current_col = i // GRID_SIZE, i % GRID_SIZE
        # Goal position
        goal_row, goal_col = board[i] // GRID_SIZE, board[i] % GRID_SIZE
        # Add Manhattan distance for this tile
        distance += abs(current_row - goal_row) + abs(current_col - goal_col)
    return distance


def a_star_solve(initial_board, tiles):
    """Solve the puzzle using A* algorithm"""
    # Priority queue: (priority, step, board, path)
    heap = []
    # Use a tuple that can be properly compared by heapq
    initial_priority = (0 + heuristic(initial_board), 0, 0, initial_board[:], [])
    heapq.heappush(heap, initial_priority)

    visited = set()
    visited.add(tuple(initial_board))

    directions = ["up", "down", "left", "right"]
    tiebreaker = 1  # To ensure proper comparison in heap

    while heap:
        _, steps, _, current_board, path = heapq.heappop(heap)

        if is_solved(current_board):
            return path

        for direction in directions:
            new_board = current_board[:]
            moved_tile = move_tile(new_board, direction)

            if moved_tile is not None:
                board_tuple = tuple(new_board)
                if board_tuple not in visited:
                    visited.add(board_tuple)
                    new_path = path + [(direction, moved_tile)]
                    priority = steps + 1 + heuristic(new_board)
                    # Add tiebreaker to ensure proper comparison
                    heapq.heappush(heap, (priority, steps + 1, tiebreaker, new_board, new_path))
                    tiebreaker += 1

    return None  # No solution found (shouldn't happen for solvable puzzles)


def main():
    # Load and split image
    tiles = load_and_split_image("puzzle_image.jpg")
    board = create_solvable_board()

    solving = False
    solution_path = None
    current_step = 0
    solved = False

    draw_board(board, tiles, solving, None, solved)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if not solving and not solved:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Start AI solver
                        solving = True
                        solution_path = a_star_solve(board, tiles)
                        current_step = 0
                    elif event.key == pygame.K_r:
                        # Reset board
                        board = create_solvable_board()
                        solving = False
                        solution_path = None
                        current_step = 0
                        solved = False
                        draw_board(board, tiles, solving, None, solved)
                    elif event.key == pygame.K_UP:
                        move_tile(board, "up")
                        solved = is_solved(board)
                        draw_board(board, tiles, solving, None, solved)
                    elif event.key == pygame.K_DOWN:
                        move_tile(board, "down")
                        solved = is_solved(board)
                        draw_board(board, tiles, solving, None, solved)
                    elif event.key == pygame.K_LEFT:
                        move_tile(board, "left")
                        solved = is_solved(board)
                        draw_board(board, tiles, solving, None, solved)
                    elif event.key == pygame.K_RIGHT:
                        move_tile(board, "right")
                        solved = is_solved(board)
                        draw_board(board, tiles, solving, None, solved)

        # If in solving mode, execute the next move
        if solving and solution_path and current_step < len(solution_path) and not solved:
            direction, moved_tile = solution_path[current_step]
            move_tile(board, direction)
            solved = is_solved(board)
            draw_board(board, tiles, solving, moved_tile, solved)
            current_step += 1
            pygame.time.delay(500)  # Pause for visibility
            if current_step == len(solution_path) or solved:
                solving = False
                if solved:
                    print("AI has solved the puzzle!")

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()