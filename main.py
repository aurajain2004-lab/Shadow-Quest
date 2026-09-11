"""Shadow Quest 1.1.0: a small, extensible top-down dungeon adventure."""

import sys
from enum import Enum, auto

import pygame


# Display and gameplay constants are kept together so later releases can tune them safely.
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
HUD_HEIGHT = 76
TILE_SIZE = 40
FPS = 60
PLAYER_SPEED = 220
PLAYER_SIZE = 24
PLAYER_MAX_HEALTH = 100
PLAYER_ATTACK_RANGE = 72
PLAYER_ATTACK_COOLDOWN = 0.35
PLAYER_ATTACK_DAMAGE = 25
CONTACT_DAMAGE_COOLDOWN = 0.75

INK = (12, 13, 21)
PANEL = (25, 26, 39)
PANEL_LIGHT = (39, 40, 57)
FLOOR = (48, 43, 55)
FLOOR_ALT = (53, 47, 58)
WALL = (25, 27, 38)
WALL_EDGE = (78, 70, 83)
GOLD = (221, 170, 74)
GOLD_BRIGHT = (255, 207, 103)
TEXT = (235, 231, 220)
MUTED = (159, 157, 167)
PLAYER = (86, 167, 177)
PLAYER_LIGHT = (174, 235, 218)
EXIT = (121, 77, 54)
EXIT_LIGHT = (245, 181, 90)
ENEMY = (177, 73, 78)
ENEMY_LIGHT = (246, 137, 111)
HEALTH_GREEN = (92, 190, 115)
HEALTH_EMPTY = (91, 43, 51)


class GameState(Enum):
    MAIN_MENU = auto()
    INSTRUCTIONS = auto()
    PLAYING = auto()
    PAUSED = auto()
    LEVEL_COMPLETE = auto()
    GAME_OVER = auto()


class Button:
    """A keyboard- and mouse-friendly menu button."""

    def __init__(self, text, rect, action, font):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.action = action
        self.font = font
        self.hovered = False

    def update(self, mouse_position):
        self.hovered = self.rect.collidepoint(mouse_position)

    def draw(self, surface, selected=False):
        active = self.hovered or selected
        fill = (72, 65, 83) if active else PANEL_LIGHT
        border = GOLD_BRIGHT if active else (103, 94, 111)
        pygame.draw.rect(surface, fill, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=6)
        label = self.font.render(self.text, True, GOLD_BRIGHT if active else TEXT)
        surface.blit(label, label.get_rect(center=self.rect.center))


class Dungeon:
    """Grid layout and drawing for the first dungeon."""

    LAYOUT = (
        "#########################",
        "#.....#........#........#",
        "#.....#........#........#",
        "#.....####.#####........#",
        "#.......................#",
        "#..####........#######..#",
        "#..#..#........#.....#..#",
        "#..#..#........#.....#..#",
        "#..#..####.#####.....#..#",
        "#..#.................#..#",
        "#..#######.###########..#",
        "#........#..............#",
        "#........#..######......#",
        "#........#...........D..#",
        "#.......................#",
        "#########################",
    )

    def __init__(self):
        self.walls = []
        self.exit_rect = None
        for row, line in enumerate(self.LAYOUT):
            for column, tile in enumerate(line):
                rect = pygame.Rect(column * TILE_SIZE, HUD_HEIGHT + row * TILE_SIZE,
                                   TILE_SIZE, TILE_SIZE)
                if tile == "#":
                    self.walls.append(rect)
                elif tile == "D":
                    self.exit_rect = rect.inflate(-12, -8)

        self.decorations = [
            (2, 4), (5, 2), (10, 4), (14, 2), (18, 4), (22, 2),
            (3, 10), (15, 10), (21, 11), (5, 14), (17, 14),
        ]

    def collides(self, rect):
        return any(rect.colliderect(wall) for wall in self.walls)

    def draw(self, surface):
        surface.fill(FLOOR)
        for row, line in enumerate(self.LAYOUT):
            for column, tile in enumerate(line):
                tile_rect = pygame.Rect(column * TILE_SIZE, HUD_HEIGHT + row * TILE_SIZE,
                                        TILE_SIZE, TILE_SIZE)
                if tile != "#":
                    color = FLOOR_ALT if (row + column) % 2 else FLOOR
                    pygame.draw.rect(surface, color, tile_rect)
                    pygame.draw.line(surface, (64, 56, 66), tile_rect.bottomleft,
                                     tile_rect.bottomright, 1)

        for wall in self.walls:
            pygame.draw.rect(surface, WALL, wall)
            pygame.draw.line(surface, WALL_EDGE, wall.topleft, wall.topright, 2)
            pygame.draw.line(surface, (14, 16, 25), wall.bottomleft, wall.bottomright, 2)

        self._draw_exit(surface)
        for column, row in self.decorations:
            self._draw_torch(surface, column * TILE_SIZE + TILE_SIZE // 2,
                             HUD_HEIGHT + row * TILE_SIZE + TILE_SIZE // 2)

    def _draw_torch(self, surface, x, y):
        pygame.draw.circle(surface, (106, 65, 48), (x, y + 7), 5)
        pygame.draw.rect(surface, (119, 76, 49), (x - 2, y + 4, 4, 12))
        pygame.draw.circle(surface, GOLD, (x, y - 1), 6)
        pygame.draw.circle(surface, (255, 229, 142), (x, y - 2), 3)

    def _draw_exit(self, surface):
        if not self.exit_rect:
            return
        pygame.draw.rect(surface, (57, 34, 37), self.exit_rect, border_radius=4)
        pygame.draw.rect(surface, EXIT, self.exit_rect, 3, border_radius=4)
        pygame.draw.rect(surface, EXIT_LIGHT,
                         (self.exit_rect.centerx - 3, self.exit_rect.top + 9, 6, 6))
        pygame.draw.line(surface, EXIT_LIGHT, self.exit_rect.midtop,
                         (self.exit_rect.centerx, self.exit_rect.top - 8), 2)


class Player:
    def __init__(self, dungeon):
        self.dungeon = dungeon
        self.start_position = pygame.Vector2(2.5 * TILE_SIZE, HUD_HEIGHT + 2.5 * TILE_SIZE)
        self.position = self.start_position.copy()
        self.direction = pygame.Vector2(0, 1)
        self.max_health = PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.damage_cooldown = 0.0
        self.attack_cooldown = 0.0
        self.attack_effect_timer = 0.0
        self.attack_direction = self.direction.copy()

    @property
    def rect(self):
        return pygame.Rect(round(self.position.x - PLAYER_SIZE / 2),
                           round(self.position.y - PLAYER_SIZE / 2),
                           PLAYER_SIZE, PLAYER_SIZE)

    def reset(self):
        self.position = self.start_position.copy()
        self.direction = pygame.Vector2(0, 1)
        self.health = self.max_health
        self.damage_cooldown = 0.0
        self.attack_cooldown = 0.0
        self.attack_effect_timer = 0.0

    @property
    def alive(self):
        return self.health > 0

    def update(self, delta_time):
        self.damage_cooldown = max(0.0, self.damage_cooldown - delta_time)
        self.attack_cooldown = max(0.0, self.attack_cooldown - delta_time)
        self.attack_effect_timer = max(0.0, self.attack_effect_timer - delta_time)
        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(
            int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        if movement.length_squared():
            movement = movement.normalize()
            self.direction = movement
            self._move_axis(movement.x * PLAYER_SPEED * delta_time, True)
            self._move_axis(movement.y * PLAYER_SPEED * delta_time, False)

    def attack(self, enemies):
        if self.attack_cooldown > 0 or not self.alive:
            return
        self.attack_cooldown = PLAYER_ATTACK_COOLDOWN
        self.attack_effect_timer = 0.14
        self.attack_direction = self.direction.copy()
        attack_center = self.position + self.attack_direction * PLAYER_ATTACK_RANGE
        for enemy in enemies:
            if enemy.alive and enemy.position.distance_to(attack_center) <= enemy.radius + 24:
                enemy.take_damage(PLAYER_ATTACK_DAMAGE)

    def take_damage(self, amount):
        if self.damage_cooldown > 0 or not self.alive:
            return
        self.health = max(0, self.health - amount)
        self.damage_cooldown = CONTACT_DAMAGE_COOLDOWN

    def _move_axis(self, amount, horizontal):
        if horizontal:
            self.position.x += amount
        else:
            self.position.y += amount
        if self.dungeon.collides(self.rect):
            if horizontal:
                self.position.x -= amount
            else:
                self.position.y -= amount

    def draw(self, surface):
        if self.damage_cooldown > 0 and round(self.damage_cooldown * 14) % 2 == 0:
            return
        body = self.rect
        pygame.draw.circle(surface, (20, 25, 34), body.center, PLAYER_SIZE // 2 + 4)
        pygame.draw.circle(surface, PLAYER, body.center, PLAYER_SIZE // 2)
        pygame.draw.circle(surface, PLAYER_LIGHT, body.center, 7)
        tip = pygame.Vector2(body.center) + self.direction * 17
        pygame.draw.line(surface, PLAYER_LIGHT, body.center, tip, 4)
        pygame.draw.circle(surface, (235, 248, 211), (round(tip.x), round(tip.y)), 3)
        if self.attack_effect_timer > 0:
            attack_tip = self.position + self.attack_direction * (PLAYER_ATTACK_RANGE + 8)
            pygame.draw.line(surface, GOLD_BRIGHT, self.position, attack_tip, 8)
            pygame.draw.circle(surface, (255, 238, 164), (round(attack_tip.x), round(attack_tip.y)), 8, 2)


class Enemy:
    """Base class for enemies that live inside the dungeon."""

    def __init__(self, dungeon, position, health, speed, contact_damage):
        self.dungeon = dungeon
        self.position = pygame.Vector2(position)
        self.max_health = health
        self.health = health
        self.speed = speed
        self.contact_damage = contact_damage
        self.radius = 14
        self.hit_flash_timer = 0.0

    @property
    def alive(self):
        return self.health > 0

    @property
    def rect(self):
        return pygame.Rect(round(self.position.x - self.radius),
                           round(self.position.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        self.hit_flash_timer = 0.12

    def update(self, delta_time, player):
        self.hit_flash_timer = max(0.0, self.hit_flash_timer - delta_time)

    def draw(self, surface):
        pass


class ChaserEnemy(Enemy):
    def __init__(self, dungeon, position, health=75, speed=78, contact_damage=18):
        super().__init__(dungeon, position, health, speed, contact_damage)

    def update(self, delta_time, player):
        super().update(delta_time, player)
        if not self.alive or not player.alive:
            return
        direction = player.position - self.position
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        self._move_axis(direction.x * self.speed * delta_time, True)
        self._move_axis(direction.y * self.speed * delta_time, False)

    def _move_axis(self, amount, horizontal):
        if horizontal:
            self.position.x += amount
        else:
            self.position.y += amount
        if self.dungeon.collides(self.rect):
            if horizontal:
                self.position.x -= amount
            else:
                self.position.y -= amount

    def draw(self, surface):
        body = self.rect
        color = TEXT if self.hit_flash_timer > 0 else ENEMY
        pygame.draw.circle(surface, (37, 19, 28), body.center, self.radius + 4)
        pygame.draw.circle(surface, color, body.center, self.radius)
        pygame.draw.circle(surface, ENEMY_LIGHT, (body.centerx - 5, body.centery - 3), 3)
        pygame.draw.circle(surface, ENEMY_LIGHT, (body.centerx + 5, body.centery - 3), 3)
        bar = pygame.Rect(body.left - 6, body.top - 12, self.radius * 2 + 12, 5)
        pygame.draw.rect(surface, HEALTH_EMPTY, bar, border_radius=2)
        health_width = round(bar.width * self.health / self.max_health)
        if health_width:
            pygame.draw.rect(surface, HEALTH_GREEN, (bar.left, bar.top, health_width, bar.height), border_radius=2)


class Game:
    def __init__(self):
        pygame.init()
        display_info = pygame.display.Info()
        initial_scale = min(
            1.0,
            max(0.5, (display_info.current_w - 80) / SCREEN_WIDTH),
            max(0.5, (display_info.current_h - 120) / SCREEN_HEIGHT),
        )
        initial_size = (round(SCREEN_WIDTH * initial_scale),
                        round(SCREEN_HEIGHT * initial_scale))
        self.window = pygame.display.set_mode(initial_size, pygame.RESIZABLE)
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.viewport = pygame.Rect(0, 0, *initial_size)
        self._update_viewport(*initial_size)
        pygame.display.set_caption("Shadow Quest")
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(None, 78)
        self.heading_font = pygame.font.Font(None, 42)
        self.body_font = pygame.font.Font(None, 28)
        self.button_font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 22)
        self.state = GameState.MAIN_MENU
        self.menu_selection = 0
        self.menu_buttons = []
        self.pause_buttons = []
        self.instruction_buttons = []
        self.complete_buttons = []
        self.game_over_buttons = []
        self._build_buttons()
        self.new_level()

    def _build_buttons(self):
        center_x = SCREEN_WIDTH // 2 - 125
        self.menu_buttons = [
            Button("PLAY", (center_x, 335, 250, 54), self.start_game, self.button_font),
            Button("INSTRUCTIONS", (center_x, 405, 250, 54), self.show_instructions, self.button_font),
            Button("QUIT", (center_x, 475, 250, 54), self.quit, self.button_font),
        ]
        self.instruction_buttons = [
            Button("BACK", (center_x, 555, 250, 54), self.show_menu, self.button_font)
        ]
        self.pause_buttons = [
            Button("RESUME", (center_x, 305, 250, 50), self.resume_game, self.button_font),
            Button("RESTART", (center_x, 370, 250, 50), self.start_game, self.button_font),
            Button("MAIN MENU", (center_x, 435, 250, 50), self.show_menu, self.button_font),
        ]
        self.complete_buttons = [
            Button("MAIN MENU", (center_x, 425, 250, 54), self.show_menu, self.button_font),
            Button("PLAY AGAIN", (center_x, 495, 250, 54), self.start_game, self.button_font),
        ]
        self.game_over_buttons = [
            Button("RESTART", (center_x, 425, 250, 54), self.start_game, self.button_font),
            Button("MAIN MENU", (center_x, 495, 250, 54), self.show_menu, self.button_font),
        ]

    def new_level(self):
        self.dungeon = Dungeon()
        self.player = Player(self.dungeon)
        spawn_positions = (
            (3.5 * TILE_SIZE, HUD_HEIGHT + 4.5 * TILE_SIZE),
            (10.5 * TILE_SIZE, HUD_HEIGHT + 4.5 * TILE_SIZE),
            (18.5 * TILE_SIZE, HUD_HEIGHT + 4.5 * TILE_SIZE),
            (3.5 * TILE_SIZE, HUD_HEIGHT + 11.5 * TILE_SIZE),
            (15.5 * TILE_SIZE, HUD_HEIGHT + 14.5 * TILE_SIZE),
        )
        self.enemies = [ChaserEnemy(self.dungeon, position) for position in spawn_positions]
        self.enemies_defeated = 0

    def start_game(self):
        self.new_level()
        self.state = GameState.PLAYING

    def resume_game(self):
        self.state = GameState.PLAYING

    def show_menu(self):
        self.state = GameState.MAIN_MENU
        self.menu_selection = 0

    def show_instructions(self):
        self.state = GameState.INSTRUCTIONS

    def quit(self):
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            delta_time = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.handle_events()
            if self.state == GameState.PLAYING:
                self.player.update(delta_time)
                for enemy in self.enemies:
                    enemy.update(delta_time, self.player)
                    if enemy.alive and enemy.rect.colliderect(self.player.rect):
                        self.player.take_damage(enemy.contact_damage)
                defeated = [enemy for enemy in self.enemies if not enemy.alive]
                if defeated:
                    self.enemies_defeated += len(defeated)
                    self.enemies = [enemy for enemy in self.enemies if enemy.alive]
                if not self.player.alive:
                    self.state = GameState.GAME_OVER
                elif self.player.rect.colliderect(self.dungeon.exit_rect):
                    self.state = GameState.LEVEL_COMPLETE
            self.draw()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        buttons = self.active_buttons()
        mouse_position = self.to_logical_position(pygame.mouse.get_pos())
        for button in buttons:
            button.update(mouse_position)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                self._update_viewport(*event.size)
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key, len(buttons))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                click_position = self.to_logical_position(event.pos)
                for button in buttons:
                    if button.rect.collidepoint(click_position):
                        button.action()

    def _update_viewport(self, window_width, window_height):
        scale = min(window_width / SCREEN_WIDTH, window_height / SCREEN_HEIGHT)
        scaled_width = round(SCREEN_WIDTH * scale)
        scaled_height = round(SCREEN_HEIGHT * scale)
        self.viewport = pygame.Rect(
            (window_width - scaled_width) // 2,
            (window_height - scaled_height) // 2,
            scaled_width,
            scaled_height,
        )

    def to_logical_position(self, window_position):
        if not self.viewport.width or not self.viewport.height:
            return -1, -1
        scale_x = SCREEN_WIDTH / self.viewport.width
        scale_y = SCREEN_HEIGHT / self.viewport.height
        return (
            round((window_position[0] - self.viewport.left) * scale_x),
            round((window_position[1] - self.viewport.top) * scale_y),
        )

    def handle_key(self, key, button_count):
        if self.state == GameState.PLAYING and key == pygame.K_ESCAPE:
            self.state = GameState.PAUSED
        elif self.state == GameState.PLAYING and key == pygame.K_SPACE:
            self.player.attack(self.enemies)
        elif self.state == GameState.PAUSED and key == pygame.K_ESCAPE:
            self.resume_game()
        elif self.state in (GameState.MAIN_MENU, GameState.PAUSED,
                            GameState.LEVEL_COMPLETE, GameState.GAME_OVER):
            self.menu_selection %= button_count
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_selection = (self.menu_selection - 1) % button_count
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selection = (self.menu_selection + 1) % button_count
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.active_buttons()[self.menu_selection].action()
        elif self.state == GameState.INSTRUCTIONS and key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.show_menu()

    def active_buttons(self):
        if self.state == GameState.MAIN_MENU:
            return self.menu_buttons
        if self.state == GameState.INSTRUCTIONS:
            return self.instruction_buttons
        if self.state == GameState.PAUSED:
            return self.pause_buttons
        if self.state == GameState.LEVEL_COMPLETE:
            return self.complete_buttons
        if self.state == GameState.GAME_OVER:
            return self.game_over_buttons
        return []

    def draw(self):
        if self.state in (GameState.PLAYING, GameState.PAUSED,
                  GameState.LEVEL_COMPLETE, GameState.GAME_OVER):
            self.draw_game()
        elif self.state == GameState.INSTRUCTIONS:
            self.draw_instructions()
        else:
            self.draw_menu()
        self.window.fill(INK)
        scaled_screen = pygame.transform.smoothscale(self.screen, self.viewport.size)
        self.window.blit(scaled_screen, self.viewport.topleft)
        pygame.display.flip()

    def draw_menu(self):
        self.draw_background()
        self.draw_centered("SHADOW QUEST", 150, self.title_font, GOLD_BRIGHT)
        self.draw_centered("A Dungeon Adventure", 215, self.body_font, MUTED)
        pygame.draw.line(self.screen, GOLD, (390, 255), (610, 255), 2)
        for index, button in enumerate(self.menu_buttons):
            button.draw(self.screen, index == self.menu_selection)
        self.draw_centered("Use mouse or arrow keys to navigate", 590, self.small_font, MUTED)

    def draw_instructions(self):
        self.draw_background()
        self.draw_centered("HOW TO PLAY", 125, self.heading_font, GOLD_BRIGHT)
        panel = pygame.Rect(255, 190, 490, 315)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=8)
        pygame.draw.rect(self.screen, (80, 71, 89), panel, 2, border_radius=8)
        instructions = [
            ("WASD / Arrow Keys", "Move your hero through the dungeon"),
            ("SPACE", "Attack enemies in the direction you face"),
            ("ESC", "Pause the game"),
            ("Objective", "Reach the glowing exit door"),
        ]
        for index, (label, description) in enumerate(instructions):
            y = 218 + index * 65
            self.screen.blit(self.body_font.render(label, True, GOLD_BRIGHT), (295, y))
            self.screen.blit(self.small_font.render(description, True, TEXT), (295, y + 28))
        self.instruction_buttons[0].draw(self.screen)

    def draw_game(self):
        self.dungeon.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)
        pygame.draw.rect(self.screen, INK, (0, 0, SCREEN_WIDTH, HUD_HEIGHT))
        self.screen.blit(self.heading_font.render("SHADOW QUEST", True, GOLD_BRIGHT), (26, 18))
        self.screen.blit(self.small_font.render(
            f"HEALTH: {self.player.health} / {self.player.max_health}", True, TEXT), (300, 12))
        health_bar = pygame.Rect(300, 39, 180, 13)
        pygame.draw.rect(self.screen, HEALTH_EMPTY, health_bar, border_radius=4)
        health_width = round(health_bar.width * self.player.health / self.player.max_health)
        if health_width:
            pygame.draw.rect(self.screen, HEALTH_GREEN,
                             (health_bar.left, health_bar.top, health_width, health_bar.height), border_radius=4)
        self.screen.blit(self.small_font.render(
            f"ENEMIES: {len(self.enemies)}  DEFEATED: {self.enemies_defeated}", True, TEXT), (525, 12))
        self.screen.blit(self.small_font.render("OBJECTIVE: REACH THE EXIT", True, MUTED), (525, 39))
        if self.state == GameState.PAUSED:
            self.draw_overlay("PAUSED", "The dungeon waits in silence.", self.pause_buttons)
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_overlay("LEVEL COMPLETE", f"Enemies defeated: {self.enemies_defeated}", self.complete_buttons)
        elif self.state == GameState.GAME_OVER:
            self.draw_overlay("GAME OVER", f"Enemies defeated: {self.enemies_defeated}", self.game_over_buttons)

    def draw_overlay(self, heading, subtitle, buttons):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 8, 15, 205))
        self.screen.blit(overlay, (0, 0))
        self.draw_centered(heading, 205, self.heading_font, GOLD_BRIGHT)
        self.draw_centered(subtitle, 250, self.body_font, TEXT)
        for index, button in enumerate(buttons):
            button.draw(self.screen, index == self.menu_selection)

    def draw_background(self):
        self.screen.fill(INK)
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(self.screen, (19, 20, 31), (0, y), (SCREEN_WIDTH, y), 1)
        pygame.draw.circle(self.screen, (36, 30, 44), (150, 140), 210)
        pygame.draw.circle(self.screen, (28, 36, 45), (860, 570), 260)

    def draw_centered(self, text, y, font, color):
        rendered = font.render(text, True, color)
        self.screen.blit(rendered, rendered.get_rect(center=(SCREEN_WIDTH // 2, y)))


if __name__ == "__main__":
    Game().run()