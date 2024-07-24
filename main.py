import pygame
import random
import math
import json
import os

pygame.init()
pygame.mixer.init()  # Ensure mixer is initialized

# Load sound effects
MERGE_SOUND = pygame.mixer.Sound('pop-up.mp3')
GAME_OVER_SOUND = pygame.mixer.Sound('video-game-fail.mp3')

# Frames per second setting
FPS = 120

# Dimensions of the game window
WIDTH, HEIGHT = 800, 800
# Number of rows and columns in the grid
ROWS, COLS = 4, 4

# Dimensions of each rectangle in the grid
RECT_HEIGHT = HEIGHT // ROWS
RECT_WIDTH = WIDTH // COLS

# Colors used in the game
OUTLINE_COLOR = (187, 173, 160)
OUTLINE_THICKNESS = 10
BACKGROUND_COLOR = (205, 192, 180)
FONT_COLOR = (119, 110, 101)

# Fonts used for text rendering
FONT = pygame.font.SysFont("comicsans", 60, bold=True)
END_FONT = pygame.font.SysFont("comicsans", 100, bold=True)
SCORE_FONT = pygame.font.SysFont("comicsans", 40, bold=True)

# Movement velocity for the tiles
MOVE_VEL = 20

# Initialize the game window
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2048")


class Tile:
    # Colors for different tile values
    COLORS = [
        (237, 229, 218),  # 2
        (238, 225, 201),  # 4
        (243, 178, 122),  # 8
        (246, 150, 101),  # 16
        (247, 124, 95),  # 32
        (247, 95, 59),  # 64
        (237, 208, 115),  # 128
        (237, 204, 99),  # 256
        (236, 202, 80),  # 512
        (237, 194, 46),  # 1024
        (237, 204, 97),  # 2048
    ]

    def __init__(self, value, row, col):
        self.value = value
        self.row = row
        self.col = col
        self.x = col * RECT_WIDTH
        self.y = row * RECT_HEIGHT

    def get_color(self):
        """Return the color based on the tile's value."""
        color_index = int(math.log2(self.value)) - 1
        color = self.COLORS[min(color_index, len(self.COLORS) - 1)]
        return color

    def draw(self, window):
        """Draw the tile on the game window."""
        color = self.get_color()
        pygame.draw.rect(window, color, (self.x, self.y, RECT_WIDTH, RECT_HEIGHT))

        # Draw the tile's value in the center
        text = FONT.render(str(self.value), 1, FONT_COLOR)
        window.blit(
            text,
            (
                self.x + (RECT_WIDTH / 2 - text.get_width() / 2),
                self.y + (RECT_HEIGHT / 2 - text.get_height() / 2),
            ),
        )

    def set_pos(self, ceil=False):
        """Set the tile's row and column based on its x and y position."""
        if ceil:
            self.row = math.ceil(self.y / RECT_HEIGHT)
            self.col = math.ceil(self.x / RECT_WIDTH)
        else:
            self.row = math.floor(self.y / RECT_HEIGHT)
            self.col = math.floor(self.x / RECT_WIDTH)

    def move(self, delta):
        """Move the tile by the given delta."""
        self.x += delta[0]
        self.y += delta[1]


def draw_grid(window):
    """Draw the grid lines on the game window."""
    for row in range(1, ROWS):
        y = row * RECT_HEIGHT
        pygame.draw.line(window, OUTLINE_COLOR, (0, y), (WIDTH, y), OUTLINE_THICKNESS)

    for col in range(1, COLS):
        x = col * RECT_WIDTH
        pygame.draw.line(window, OUTLINE_COLOR, (x, 0), (x, HEIGHT), OUTLINE_THICKNESS)

    # Draw the outline around the entire grid
    pygame.draw.rect(window, OUTLINE_COLOR, (0, 0, WIDTH, HEIGHT), OUTLINE_THICKNESS)


def draw_restart_button(window):
    """Draw the restart button on the window."""
    button_width = 200
    button_height = 60
    button_color = (0, 128, 0)  # Green color for the button
    button_text_color = (255, 255, 255)  # White text color
    button_x = WIDTH // 2 - button_width // 2
    button_y = HEIGHT // 2 + 100

    pygame.draw.rect(window, button_color, (button_x, button_y, button_width, button_height))
    text = FONT.render("Restart", True, button_text_color)
    window.blit(
        text,
        (
            button_x + (button_width / 2 - text.get_width() / 2),
            button_y + (button_height / 2 - text.get_height() / 2),
        ),
    )


def draw(window, tiles, score, best_score, game_over=False):
    """Draw all elements on the window, including tiles, grid, score, and game over message."""
    window.fill(BACKGROUND_COLOR)

    # Draw all tiles
    for tile in tiles.values():
        tile.draw(window)

    # Draw the grid and score
    draw_grid(window)
    draw_score(window, score, best_score)

    if game_over:
        draw_game_over(window)
        draw_restart_button(window)

    pygame.display.update()


def draw_game_over(window):
    """Draw the 'Game Over' message on the window."""
    text = END_FONT.render("Game Over!", 1, (255, 0, 0))
    window.blit(
        text,
        (
            WIDTH / 2 - text.get_width() / 2,
            HEIGHT / 2 - text.get_height() / 2,
        ),
    )


def draw_score(window, score, best_score):
    """Draw the current score and best score on the window."""
    score_text = SCORE_FONT.render(f"Score: {score}", 1, FONT_COLOR)
    best_score_text = SCORE_FONT.render(f"Best: {best_score}", 1, FONT_COLOR)
    window.blit(score_text, (20, 20))
    window.blit(best_score_text, (WIDTH - best_score_text.get_width() - 20, 20))


def get_random_pos(tiles):
    """Return a random empty position (row, col) in the grid."""
    row, col = None, None
    while True:
        row = random.randrange(0, ROWS)
        col = random.randrange(0, COLS)

        if f"{row}{col}" not in tiles:
            break

    return row, col


def move_tiles(window, tiles, clock, direction, score):
    """Move all tiles in the specified direction and handle merging."""
    updated = True
    blocks = set()  # Set of tiles that have already merged in this move

    # Set up parameters based on movement direction
    if direction == "left":
        sort_func = lambda x: x.col
        reverse = False
        delta = (-MOVE_VEL, 0)
        boundary_check = lambda tile: tile.col == 0
        get_next_tile = lambda tile: tiles.get(f"{tile.row}{tile.col - 1}")
        merge_check = lambda tile, next_tile: tile.x > next_tile.x + MOVE_VEL
        move_check = (
            lambda tile, next_tile: tile.x > next_tile.x + RECT_WIDTH + MOVE_VEL
        )
        ceil = True
    elif direction == "right":
        sort_func = lambda x: x.col
        reverse = True
        delta = (MOVE_VEL, 0)
        boundary_check = lambda tile: tile.col == COLS - 1
        get_next_tile = lambda tile: tiles.get(f"{tile.row}{tile.col + 1}")
        merge_check = lambda tile, next_tile: tile.x < next_tile.x - MOVE_VEL
        move_check = (
            lambda tile, next_tile: tile.x + RECT_WIDTH + MOVE_VEL < next_tile.x
        )
        ceil = False
    elif direction == "up":
        sort_func = lambda x: x.row
        reverse = False
        delta = (0, -MOVE_VEL)
        boundary_check = lambda tile: tile.row == 0
        get_next_tile = lambda tile: tiles.get(f"{tile.row - 1}{tile.col}")
        merge_check = lambda tile, next_tile: tile.y > next_tile.y + MOVE_VEL
        move_check = (
            lambda tile, next_tile: tile.y > next_tile.y + RECT_HEIGHT + MOVE_VEL
        )
        ceil = True
    elif direction == "down":
        sort_func = lambda x: x.row
        reverse = True
        delta = (0, MOVE_VEL)
        boundary_check = lambda tile: tile.row == ROWS - 1
        get_next_tile = lambda tile: tiles.get(f"{tile.row + 1}{tile.col}")
        merge_check = lambda tile, next_tile: tile.y < next_tile.y - MOVE_VEL
        move_check = (
            lambda tile, next_tile: tile.y + RECT_HEIGHT + MOVE_VEL < next_tile.y
        )
        ceil = False

    while updated:
        clock.tick(FPS)
        updated = False
        # Sort tiles in the direction of movement
        sorted_tiles = sorted(tiles.values(), key=sort_func, reverse=reverse)

        for i, tile in enumerate(sorted_tiles):
            if boundary_check(tile):
                continue

            next_tile = get_next_tile(tile)
            if not next_tile:
                tile.move(delta)
            elif (
                    tile.value == next_tile.value
                    and tile not in blocks
                    and next_tile not in blocks
            ):
                if merge_check(tile, next_tile):
                    tile.move(delta)
                else:
                    # Merge tiles
                    next_tile.value *= 2
                    score += next_tile.value
                    sorted_tiles.pop(i)
                    blocks.add(next_tile)

                    # Play merge sound effect
                    MERGE_SOUND.play()
            elif move_check(tile, next_tile):
                tile.move(delta)
            else:
                continue

            tile.set_pos(ceil)
            updated = True

        update_tiles(window, tiles, sorted_tiles)

    return end_move(tiles, score)


def end_move(tiles, score):
    """Check if the game is lost or continue by adding a new tile."""
    if len(tiles) == 16:
        # Play game over sound effect
        GAME_OVER_SOUND.play()
        return "lost", score

    row, col = get_random_pos(tiles)
    tiles[f"{row}{col}"] = Tile(random.choice([2, 4]), row, col)
    return "continue", score


def update_tiles(window, tiles, sorted_tiles):
    """Update the tiles dictionary and redraw the game window."""
    tiles.clear()
    for tile in sorted_tiles:
        tiles[f"{tile.row}{tile.col}"] = tile

    draw(window, tiles, 0, 0)


def generate_tiles():
    """Generate two initial tiles with value 2."""
    tiles = {}
    for _ in range(2):
        row, col = get_random_pos(tiles)
        tiles[f"{row}{col}"] = Tile(2, row, col)

    return tiles


def save_best_score(score):
    """Save the best score if the current score is higher."""
    best_score = load_best_score()
    if score > best_score:
        with open('best_score.json', 'w') as file:
            json.dump(score, file)


def load_best_score():
    """Load the best score from the saved file, or return 0 if not found."""
    if os.path.exists('best_score.json'):
        with open('best_score.json', 'r') as file:
            return json.load(file)
    return 0


def main(window):
    """Main function to run the game loop."""
    clock = pygame.time.Clock()
    run = True

    # Initialize game state
    tiles = generate_tiles()
    score = 0
    best_score = load_best_score()
    game_over = False

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_LEFT:
                    result, score = move_tiles(window, tiles, clock, "left", score)
                if event.key == pygame.K_RIGHT:
                    result, score = move_tiles(window, tiles, clock, "right", score)
                if event.key == pygame.K_UP:
                    result, score = move_tiles(window, tiles, clock, "up", score)
                if event.key == pygame.K_DOWN:
                    result, score = move_tiles(window, tiles, clock, "down", score)

                if result == "lost":
                    draw(window, tiles, score, best_score, game_over=True)
                    save_best_score(score)
                    game_over = True

            if event.type == pygame.MOUSEBUTTONDOWN and game_over:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                button_width = 200
                button_height = 60
                button_x = WIDTH // 2 - button_width // 2
                button_y = HEIGHT // 2 + 100
                if (button_x <= mouse_x <= button_x + button_width and
                        button_y <= mouse_y <= button_y + button_height):
                    tiles = generate_tiles()
                    score = 0
                    game_over = False

        if not game_over:
            draw(window, tiles, score, best_score)
        else:
            draw(window, tiles, score, best_score, game_over=True)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(WINDOW)
