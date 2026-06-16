import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 遊戲視窗與網格設定
GRID_SIZE = 30  # 每個格子的大小 (像素)
COLS, ROWS = 10, 20  # 網格行數與列數
WIDTH = COLS * GRID_SIZE
HEIGHT = ROWS * GRID_SIZE
FPS = 60

# 顏色定義 (RGB)
BLACK = (20, 20, 20)
GRAY = (50, 50, 50)
WHITE = (255, 255, 255)
COLORS = [
    (0, 255, 255),  # I - 青色
    (255, 255, 0),  # O - 黃色
    (128, 0, 128),  # T - 紫色
    (0, 255, 0),  # S - 綠色
    (255, 0, 0),  # Z - 紅色
    (0, 0, 255),  # J - 藍色
    (255, 165, 0)  # L - 橘色
]

# 方塊形狀定義 (使用 4x4 或 3x3 矩陣坐標)
SHAPES = [
    [[1, 5, 9, 13], [4, 5, 6, 7]],  # I
    [[1, 2, 5, 6]],  # O
    [[1, 4, 5, 6], [1, 5, 9, 6], [4, 5, 6, 9], [1, 4, 5, 9]],  # T
    [[1, 2, 4, 5], [0, 4, 5, 9]],  # S
    [[0, 1, 5, 6], [1, 5, 4, 8]],  # Z
    [[1, 5, 8, 9], [4, 5, 6, 2], [0, 1, 5, 9], [4, 5, 6, 8]],  # J
    [[1, 5, 9, 10], [4, 5, 6, 0], [0, 1, 5, 9], [4, 5, 6, 2]]  # L
]


class Piece:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.randint(0, len(SHAPES) - 1)
        self.color = COLORS[self.type]
        self.rotation = 0

    def image(self):
        return SHAPES[self.type][self.rotation]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(SHAPES[self.type])


class Tetris:
    def __init__(self):
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.score = 0
        self.game_over = False
        self.current_piece = Piece(3, 0)

    def check_collision(self, piece, offset_x=0, offset_y=0, check_rotation=False):
        """檢查方塊是否與牆壁或固定方塊發生碰撞"""
        temp_rotation = piece.rotation
        if check_rotation:
            piece.rotate()

        collision = False
        for i in range(4):
            for j in range(4):
                if i * 4 + j in piece.image():
                    next_x = piece.x + j + offset_x
                    next_y = piece.y + i + offset_y

                    # 檢查邊界與是否碰到既有方塊
                    if next_x < 0 or next_x >= COLS or next_y >= ROWS:
                        collision = True
                    elif next_y >= 0 and self.grid[next_y][next_x] != 0:
                        collision = True

        if check_rotation:
            # 復原旋轉狀態
            piece.rotation = temp_rotation
        return collision

    def lock_piece(self):
        """將方塊固定在網格中"""
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.current_piece.image():
                    if self.current_piece.y + i >= 0:
                        self.grid[self.current_piece.y + i][self.current_piece.x + j] = self.current_piece.color
        self.clear_lines()
        # 生成新方塊
        self.current_piece = Piece(3, 0)
        # 如果新方塊一出生就碰撞，代表死棋了
        if self.check_collision(self.current_piece):
            self.game_over = True

    def clear_lines(self):
        """消除滿行並計分"""
        lines_cleared = 0
        new_grid = [row for row in self.grid if any(cell == 0 for cell in row)]
        lines_cleared = ROWS - len(new_grid)

        # 補足被消除的行數
        for _ in range(lines_cleared):
            new_grid.insert(0, [0] * COLS)

        self.grid = new_grid
        self.score += lines_cleared * 100

    def move_down(self):
        if not self.check_collision(self.current_piece, offset_y=1):
            self.current_piece.y += 1
        else:
            self.lock_piece()

    def move_side(self, dx):
        if not self.check_collision(self.current_piece, offset_x=dx):
            self.current_piece.x += dx

    def rotate_piece(self):
        if not self.check_collision(self.current_piece, check_rotation=True):
            self.current_piece.rotate()


def draw_grid(screen, grid):
    """繪製已經固定的方塊和背景網格線"""
    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if grid[r][c] != 0:
                pygame.draw.rect(screen, grid[r][c], rect)
            pygame.draw.rect(screen, GRAY, rect, 1)


def draw_piece(screen, piece):
    """繪製當前正在下落的方塊"""
    for i in range(4):
        for j in range(4):
            if i * 4 + j in piece.image():
                rect = pygame.Rect((piece.x + j) * GRID_SIZE, (piece.y + i) * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(screen, piece.color, rect)
                pygame.draw.rect(screen, WHITE, rect, 1)  # 白色邊框讓方塊更明顯


def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Python 俄羅斯方塊")
    clock = pygame.time.Clock()
    game = Tetris()

    fall_time = 0
    fall_speed = 500  # 方塊每 500 毫秒（0.5秒）往下掉一格

    font = pygame.font.SysFont("Arial", 24)

    while True:
        # 計算時間差（毫秒）
        fall_time += clock.get_rawtime()
        clock.tick(FPS)

        # 自動下落邏輯
        if not game.game_over:
            if fall_time >= fall_speed:
                game.move_down()
                fall_time = 0

        # 事件監聽（鍵盤操作）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and not game.game_over:
                if event.key == pygame.K_LEFT:
                    game.move_side(-1)
                elif event.key == pygame.K_RIGHT:
                    game.move_side(1)
                elif event.key == pygame.K_DOWN:
                    game.move_down()
                elif event.key == pygame.K_UP:
                    game.rotate_piece()
                elif event.key == pygame.K_SPACE:  # 空白鍵瞬間下落（Hard Drop）
                    while not game.check_collision(game.current_piece, offset_y=1):
                        game.current_piece.y += 1
                    game.lock_piece()

            # 遊戲結束後按 R 鍵重開
            if event.type == pygame.KEYDOWN and game.game_over:
                if event.key == pygame.K_r:
                    game = Tetris()

        # 畫面繪製
        screen.fill(BLACK)
        draw_grid(screen, game.grid)
        if not game.game_over:
            draw_piece(screen, game.current_piece)

        # 顯示分數
        score_text = font.render(f"Score: {game.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # 遊戲結束畫面
        if game.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # 半透明遮罩
            screen.blit(overlay, (0, 0))

            over_text = font.render("GAME OVER", True, (255, 0, 0))
            retry_text = font.render("Press 'R' to Restart", True, WHITE)

            screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 30))
            screen.blit(retry_text, (WIDTH // 2 - retry_text.get_width() // 2, HEIGHT // 2 + 10))

        pygame.display.flip()


if __name__ == "__main__":
    main()