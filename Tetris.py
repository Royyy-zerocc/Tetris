import pygame
import random
import sys

# -----------------------------------------------------------------------------
# 1. 初始化 Pygame 與基礎設定
# -----------------------------------------------------------------------------
pygame.init()

GRID_SIZE = 30  # 每個格子的大小（像素）
COLS, ROWS = 10, 20  # 網格行數與列數
GAME_WIDTH = COLS * GRID_SIZE  # 遊戲主網格寬度 (300)
SIDEBAR_WIDTH = 180  # 右側提示區寬度
WIDTH = GAME_WIDTH + SIDEBAR_WIDTH  # 總視窗寬度 (480)
HEIGHT = ROWS * GRID_SIZE  # 總視窗高度 (600)
FPS = 60

# 顏色定義 (RGB)
BLACK = (20, 20, 20)
GRAY = (50, 50, 50)
WHITE = (255, 255, 255)
LIGHT_GRAY = (100, 100, 100)
GRID_LINE_COLOR = (40, 40, 40)  # 💡 新增：背景網格線的淡淡灰色

# 7種方塊的形狀定義（用 0 和 1 表示）
SHAPES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1],
          [1, 1]],
    'T': [[0, 1, 0],
          [1, 1, 1]],
    'S': [[0, 1, 1],
          [1, 1, 0]],
    'Z': [[1, 1, 0],
          [0, 1, 1]],
    'J': [[1, 0, 0],
          [1, 1, 1]],
    'L': [[0, 0, 1],
          [1, 1, 1]]
}

# 每種方塊對應的顏色
SHAPE_COLORS = {
    'I': (0, 255, 255),  # 青色
    'O': (255, 255, 0),  # 黃色
    'T': (128, 0, 128),  # 紫色
    'S': (0, 255, 0),  # 綠色
    'Z': (255, 0, 0),  # 紅色
    'J': (0, 0, 255),  # 藍色
    'L': (255, 165, 0)  # 橘色
}


# -----------------------------------------------------------------------------
# 2. 俄羅斯方塊核心邏輯類別
# -----------------------------------------------------------------------------
class TetrisGame:
    def __init__(self):
        # 初始化遊戲地圖（全空，用黑色 (20,20,20) 代表沒方塊）
        self.grid = [[BLACK for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.game_over = False

        # 一開始就先抽好「當前方塊」和「下一個方塊」
        self.current_shape_key = random.choice(list(SHAPES.keys()))
        self.current_piece = SHAPES[self.current_shape_key]
        self.current_color = SHAPE_COLORS[self.current_shape_key]

        self.next_shape_key = random.choice(list(SHAPES.keys()))
        self.next_piece = SHAPES[self.next_shape_key]
        self.next_color = SHAPE_COLORS[self.next_shape_key]

        # 方塊初始出生位置（上方中央）
        self.piece_x = COLS // 2 - len(self.current_piece[0]) // 2
        self.piece_y = 0

    def reset_current_piece(self):
        """當方塊固定後，把預備好的下一個方塊遞補上來，並抽新的下一個方塊"""
        self.current_shape_key = self.next_shape_key
        self.current_piece = self.next_piece
        self.current_color = self.next_color

        # 抽取全新的「下一個方塊」
        self.next_shape_key = random.choice(list(SHAPES.keys()))
        self.next_piece = SHAPES[self.next_shape_key]
        self.next_color = SHAPE_COLORS[self.next_shape_key]

        # 重設出生位置
        self.piece_x = COLS // 2 - len(self.current_piece[0]) // 2
        self.piece_y = 0

        # 如果一出生就撞到，代表頂天了，Game Over
        if self.check_collision(self.current_piece, self.piece_x, self.piece_y):
            self.game_over = True

    def check_collision(self, piece, offset_x, offset_y):
        """檢查方塊是否撞到邊界或已經落下的方塊"""
        for r, row in enumerate(piece):
            for c, cell in enumerate(row):
                if cell:
                    new_x = offset_x + c
                    new_y = offset_y + r
                    # 檢查超出左右邊界或底部的邊界
                    if new_x < 0 or new_x >= COLS or new_y >= ROWS:
                        return True
                    # 檢查是否撞到網格內現有的方塊（非黑色代表有方塊）
                    if new_y >= 0 and self.grid[new_y][new_x] != BLACK:
                        return True
        return False

    def lock_piece(self):
        """將方塊固定到網格中，並檢查消行與加分"""
        for r, row in enumerate(self.current_piece):
            for c, cell in enumerate(row):
                if cell:
                    if self.piece_y + r >= 0:
                        self.grid[self.piece_y + r][self.piece_x + c] = self.current_color

        self.clear_lines()
        self.reset_current_piece()

    def clear_lines(self):
        """檢查是否有整行填滿，並進行消行加分"""
        new_grid = [row for row in self.grid if any(cell == BLACK for cell in row)]
        cleared = ROWS - len(new_grid)
        if cleared > 0:
            self.score += cleared * 100
            # 補足上方空行
            while len(new_grid) < ROWS:
                new_grid.insert(0, [BLACK for _ in range(COLS)])
            self.grid = new_grid

    def move_side(self, dx):
        """左右移動方塊"""
        if not self.check_collision(self.current_piece, self.piece_x + dx, self.piece_y):
            self.piece_x += dx

    def move_down(self):
        """向下移動方塊（自動下落或手動加速用）。回傳 True 代表移動成功，False 代表撞到底了"""
        if not self.check_collision(self.current_piece, self.piece_x, self.piece_y + 1):
            self.piece_y += 1
            return True
        else:
            self.lock_piece()
            return False

    def rotate(self):
        """順時針旋轉方塊，若轉了會撞到，會嘗試進行左右修正 (簡單壁面踢擊)"""
        # 矩陣轉置並翻轉，達到順時針旋轉
        rotated = [list(x) for x in zip(*self.current_piece[::-1])]

        # 嘗試在原本位置，或往左移、往右移 1 格內看能不能順利旋轉
        for kick in [0, -1, 1]:
            if not self.check_collision(rotated, self.piece_x + kick, self.piece_y):
                self.current_piece = rotated
                self.piece_x += kick
                break

    def hard_drop(self):
        """利用 while 迴圈讓方塊在瞬間以最高速衝到底部，並立刻固定"""
        while self.move_down():
            pass  # 一直呼叫 move_down 直到它回傳 False 為止


# -----------------------------------------------------------------------------
# 3. 畫面繪製函式
# -----------------------------------------------------------------------------
def draw_screen(screen, game):
    screen.fill(BLACK)

    # 💡 新增：繪製背景輔助網格線（直條線與橫條線）
    for c in range(COLS + 1):
        pygame.draw.line(screen, GRID_LINE_COLOR, (c * GRID_SIZE, 0), (c * GRID_SIZE, HEIGHT))
    for r in range(ROWS + 1):
        pygame.draw.line(screen, GRID_LINE_COLOR, (0, r * GRID_SIZE), (GAME_WIDTH, r * GRID_SIZE))

    # A. 繪製左側主網格與已經落下的方塊
    for r in range(ROWS):
        for c in range(COLS):
            if game.grid[r][c] != BLACK:  # 只有非黑色（有方塊）的地方才著色，不覆蓋剛畫好的背景格線
                pygame.draw.rect(screen, game.grid[r][c], (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE - 1, GRID_SIZE - 1))

    # B. 繪製左側正在掉落的當前方塊
    if not game.game_over:
        for r, row in enumerate(game.current_piece):
            for c, cell in enumerate(row):
                if cell:
                    x = (game.piece_x + c) * GRID_SIZE
                    y = (game.piece_y + r) * GRID_SIZE
                    pygame.draw.rect(screen, game.current_color, (x, y, GRID_SIZE - 1, GRID_SIZE - 1))

    # C. 繪製左側與右側提示區的分割線
    pygame.draw.line(screen, LIGHT_GRAY, (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 2)

    # 💡 繪製右側的「下一個方塊 (Next) 提示區」與分數
    font = pygame.font.SysFont('Microsoft JhengHei', 24)  # 使用微軟正黑體，防中文字型碎裂

    # 畫 "Next:" 字樣
    next_label = font.render('NEXT:', True, WHITE)
    screen.blit(next_label, (GAME_WIDTH + 20, 30))

    # 畫下一個方塊的微縮模型
    for r, row in enumerate(game.next_piece):
        for c, cell in enumerate(row):
            if cell:
                # 把下一個方塊畫在右側中間
                x = GAME_WIDTH + 40 + c * GRID_SIZE
                y = 80 + r * GRID_SIZE
                pygame.draw.rect(screen, game.next_color, (x, y, GRID_SIZE - 1, GRID_SIZE - 1))

    # D. 繪製分數顯示
    score_label = font.render('SCORE:', True, WHITE)
    screen.blit(score_label, (GAME_WIDTH + 20, 250))

    score_text = font.render(str(game.score), True, (0, 255, 255))  # 青色分數字
    screen.blit(score_text, (GAME_WIDTH + 20, 290))

    # E. 繪製 Game Over 字樣
    if game.game_over:
        over_font = pygame.font.SysFont('Microsoft JhengHei', 36, bold=True)
        over_text = over_font.render('GAME OVER', True, (255, 0, 0))
        # 居中顯示在左側遊戲網格內
        screen.blit(over_text, (GAME_WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 20))

    pygame.display.flip()


# -----------------------------------------------------------------------------
# 4. 主程式進入點
# -----------------------------------------------------------------------------
def main():
    # ✨ 已修復：移除了多餘的 set_index
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("經典俄羅斯方塊 - 升級版")
    clock = pygame.time.Clock()
    game = TetrisGame()

    fall_time = 0

    # 💡 新增：長按加速的速度設定
    NORMAL_SPEED = 500  # 正常的自動下落速度（毫秒）
    FAST_SPEED = 40  # 長按住下鍵時的超高速下落（毫秒）

    fall_speed = NORMAL_SPEED
    last_time = pygame.time.get_ticks()

    while True:
        current_time = pygame.time.get_ticks()
        fall_time += current_time - last_time
        last_time = current_time

        # 自動下落邏輯
        if fall_time >= fall_speed:
            if not game.game_over:
                game.move_down()
            fall_time = 0

        # 事件監聽（鍵盤操作）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ⬇️ 偵測「按下」鍵盤
            if event.type == pygame.KEYDOWN:
                if game.game_over:
                    # 輸了之後按隨便一個鍵可以重新開始
                    game = TetrisGame()
                    fall_speed = NORMAL_SPEED  # 重設速度
                else:
                    if event.key == pygame.K_LEFT:
                        game.move_side(-1)
                    elif event.key == pygame.K_RIGHT:
                        game.move_side(1)
                    elif event.key == pygame.K_UP:
                        game.rotate()
                    # 💡 變更：只要「按著」下方向鍵，下落判定速度立刻變成 40 毫秒一次！
                    elif event.key == pygame.K_DOWN:
                        fall_speed = FAST_SPEED
                    elif event.key == pygame.K_SPACE:
                        game.hard_drop()

            # 💡 新增：偵測「放開」鍵盤
            elif event.type == pygame.KEYUP:
                if not game.game_over:
                    # 💡 如果放開了下方向鍵，下落速度立刻恢復正常的慢速
                    if event.key == pygame.K_DOWN:
                        fall_speed = NORMAL_SPEED

        # 繪製畫面
        draw_screen(screen, game)
        clock.tick(FPS)


if __name__ == "__main__":
    main()