"""Shadow Quest 2.0.0: a self-contained top-down dungeon adventure."""

import sys
from pathlib import Path
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
COIN_VALUE = 10
POTION_HEAL = 25
POWER_UP_DURATION = 8.0
POWERED_ATTACK_DAMAGE = 50
HIGH_SCORE_FILE = Path(__file__).with_name("shadow_quest_high_score.txt")

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
COIN = (246, 194, 71)
KEY_COLOR = (246, 218, 103)
POTION = (210, 83, 118)
POWER_UP = (148, 104, 237)
PATROL = (88, 154, 218)
BOSS = (179, 71, 161)


class GameState(Enum):
    MAIN_MENU = auto()
    INSTRUCTIONS = auto()
    PLAYING = auto()
    PAUSED = auto()
    LEVEL_COMPLETE = auto()
    GAME_OVER = auto()
    FINAL_VICTORY = auto()


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
    """Fixed grid layouts and collision geometry for the three levels."""

    LAYOUTS = (
      (
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
            ),
            (
                "#########################",
                "#.....#........#........#",
                "#.....#........#........#",
                "#.....####.#####..####..#",
                "#.......................#",
                "#..####........#######..#",
                "#..#..#........#.....#..#",
                "#..#..#..####..#.....#..#",
                "#.....#..#..#..#.....#..#",
                "#..####..#..#..#######..#",
                "#........#..............#",
                "#..######.######........#",
                "#........#..............#",
                "#........#...........D..#",
                "#.......................#",
                "#########################",
        ),
        (
                "#########################",
                "#.....#........#........#",
                "#.....#..####..#........#",
                "#.....#..#....##..####..#",
                "#........#..............#",
                "#..####..#####..#######.#",
                "#..#..#........#.....#..#",
                "#..#..######...#.....#..#",
                "#..#...........#.....#..#",
                "#..#######.#######.###..#",
                "#........#..............#",
                "#..######.######........#",
                "#........#..............#",
                "#........#...........D..#",
                "#.......................#",
                "#########################",
      ),
    )

    def __init__(self, level_number=1):
        self.level_number = level_number
        self.layout = self.LAYOUTS[level_number - 1]
        self.walls = []
        self.exit_rect = None
        for row, line in enumerate(self.layout):
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

    def draw(self, surface, exit_unlocked=False):
        surface.fill(FLOOR)
        for row, line in enumerate(self.layout):
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

        self._draw_exit(surface, exit_unlocked)
        for column, row in self.decorations:
            self._draw_torch(surface, column * TILE_SIZE + TILE_SIZE // 2,
                             HUD_HEIGHT + row * TILE_SIZE + TILE_SIZE // 2)

    def _draw_torch(self, surface, x, y):
        pygame.draw.circle(surface, (106, 65, 48), (x, y + 7), 5)
        pygame.draw.rect(surface, (119, 76, 49), (x - 2, y + 4, 4, 12))
        pygame.draw.circle(surface, GOLD, (x, y - 1), 6)
        pygame.draw.circle(surface, (255, 229, 142), (x, y - 2), 3)

    def _draw_exit(self, surface, exit_unlocked):
        if not self.exit_rect:
            return
        frame_color = EXIT if exit_unlocked else (102, 102, 111)
        light_color = EXIT_LIGHT if exit_unlocked else (141, 145, 160)
        pygame.draw.rect(surface, (57, 34, 37), self.exit_rect, border_radius=4)
        pygame.draw.rect(surface, frame_color, self.exit_rect, 3, border_radius=4)
        pygame.draw.rect(surface, light_color,
                         (self.exit_rect.centerx - 3, self.exit_rect.top + 9, 6, 6))
        pygame.draw.line(surface, light_color, self.exit_rect.midtop,
                         (self.exit_rect.centerx, self.exit_rect.top - 8), 2)


class Collectible:
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.collected = False
        self.radius = 11

    @property
    def rect(self):
        return pygame.Rect(round(self.position.x - self.radius),
                           round(self.position.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def draw(self, surface):
        raise NotImplementedError


class Coin(Collectible):
    def draw(self, surface):
        pygame.draw.circle(surface, (102, 69, 30), self.rect.center, self.radius + 3)
        pygame.draw.circle(surface, COIN, self.rect.center, self.radius)
        pygame.draw.circle(surface, (255, 235, 142), self.rect.center, 4)


class Key(Collectible):
    def draw(self, surface):
        pygame.draw.circle(surface, KEY_COLOR, (self.rect.centerx - 4, self.rect.centery - 2), 6, 3)
        pygame.draw.line(surface, KEY_COLOR, (self.rect.centerx + 1, self.rect.centery + 3),
                         (self.rect.right + 4, self.rect.centery + 9), 4)
        pygame.draw.line(surface, KEY_COLOR, (self.rect.right, self.rect.centery + 5),
                         (self.rect.right + 5, self.rect.centery), 3)


class Potion(Collectible):
    def draw(self, surface):
        body = self.rect.inflate(-6, -3)
        pygame.draw.rect(surface, POTION, body, border_radius=5)
        pygame.draw.rect(surface, (246, 212, 199), (body.centerx - 4, body.top - 5, 8, 6))
        pygame.draw.line(surface, (255, 163, 195), body.midleft, body.midright, 2)


class AttackPowerUp(Collectible):
    def draw(self, surface):
        points = [(self.rect.centerx, self.rect.top), (self.rect.right, self.rect.centery),
                  (self.rect.centerx, self.rect.bottom), (self.rect.left, self.rect.centery)]
        pygame.draw.polygon(surface, POWER_UP, points)
        pygame.draw.polygon(surface, (224, 202, 255), points, 2)
        pygame.draw.line(surface, TEXT, (self.rect.centerx, self.rect.top + 4),
                         (self.rect.centerx, self.rect.bottom - 4), 2)


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
        self.power_up_timer = 0.0

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
        self.power_up_timer = 0.0

    @property
    def alive(self):
        return self.health > 0

    def update(self, delta_time):
        self.damage_cooldown = max(0.0, self.damage_cooldown - delta_time)
        self.attack_cooldown = max(0.0, self.attack_cooldown - delta_time)
        self.attack_effect_timer = max(0.0, self.attack_effect_timer - delta_time)
        self.power_up_timer = max(0.0, self.power_up_timer - delta_time)
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
                attack_damage = POWERED_ATTACK_DAMAGE if self.power_up_timer > 0 else PLAYER_ATTACK_DAMAGE
                enemy.take_damage(attack_damage)

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


class PatrolEnemy(Enemy):
    def __init__(self, dungeon, position, patrol_end, health=60, speed=70, contact_damage=14):
        super().__init__(dungeon, position, health, speed, contact_damage)
        self.patrol_start = pygame.Vector2(position)
        self.patrol_end = pygame.Vector2(patrol_end)
        self.patrol_direction = 1

    def update(self, delta_time, player):
        super().update(delta_time, player)
        if not self.alive:
            return
        target = self.patrol_end if self.patrol_direction > 0 else self.patrol_start
        direction = target - self.position
        if direction.length_squared() < 4:
            self.patrol_direction *= -1
            return
        self.position += direction.normalize() * self.speed * delta_time
        if self.dungeon.collides(self.rect):
            self.position -= direction.normalize() * self.speed * delta_time
            self.patrol_direction *= -1

    def draw(self, surface):
        body = self.rect
        color = TEXT if self.hit_flash_timer > 0 else PATROL
        pygame.draw.rect(surface, (24, 35, 56), body.inflate(8, 8), border_radius=5)
        pygame.draw.rect(surface, color, body, border_radius=4)
        pygame.draw.line(surface, (196, 228, 255), body.topleft, body.bottomright, 3)
        pygame.draw.line(surface, (196, 228, 255), body.topright, body.bottomleft, 3)
        bar = pygame.Rect(body.left - 6, body.top - 12, body.width + 12, 5)
        pygame.draw.rect(surface, HEALTH_EMPTY, bar, border_radius=2)
        health_width = round(bar.width * self.health / self.max_health)
        if health_width:
            pygame.draw.rect(surface, HEALTH_GREEN, (bar.left, bar.top, health_width, bar.height), border_radius=2)


class BossEnemy(ChaserEnemy):
    def __init__(self, dungeon, position, health=250, speed=52, contact_damage=28):
        super().__init__(dungeon, position, health, speed, contact_damage)
        self.radius = 25

    def draw(self, surface):
        body = self.rect
        color = TEXT if self.hit_flash_timer > 0 else BOSS
        pygame.draw.circle(surface, (53, 18, 59), body.center, self.radius + 8)
        pygame.draw.circle(surface, color, body.center, self.radius)
        pygame.draw.circle(surface, (255, 196, 247), (body.centerx - 9, body.centery - 6), 5)
        pygame.draw.circle(surface, (255, 196, 247), (body.centerx + 9, body.centery - 6), 5)
        bar = pygame.Rect(body.left - 12, body.top - 16, body.width + 24, 8)
        pygame.draw.rect(surface, HEALTH_EMPTY, bar, border_radius=3)
        health_width = round(bar.width * self.health / self.max_health)
        if health_width:
            pygame.draw.rect(surface, BOSS, (bar.left, bar.top, health_width, bar.height), border_radius=3)


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
        self.victory_buttons = []
        self.level_number = 1
        self.score = 0
        self.enemies_defeated = 0
        self.high_score = self.load_high_score()
        self.notification = ""
        self.notification_timer = 0.0
        self.transition_timer = 0.0
        self.next_level_number = 1
        self._build_buttons()
        self.load_level(1, reset_player=True)

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
        self.victory_buttons = [
            Button("PLAY AGAIN", (center_x, 425, 250, 54), self.start_game, self.button_font),
            Button("MAIN MENU", (center_x, 495, 250, 54), self.show_menu, self.button_font),
        ]

    def load_high_score(self):
        try:
            return max(0, int(HIGH_SCORE_FILE.read_text(encoding="ascii").strip()))
        except (OSError, ValueError):
            try:
                HIGH_SCORE_FILE.write_text("0", encoding="ascii")
            except OSError:
                pass
            return 0

    def save_high_score(self):
        if self.score <= self.high_score:
            return
        self.high_score = self.score
        try:
            HIGH_SCORE_FILE.write_text(str(self.high_score), encoding="ascii")
        except OSError:
            pass

    def announce(self, message):
        self.notification = message
        self.notification_timer = 2.0

    def load_level(self, level_number, reset_player=False):
        self.level_number = level_number
        self.dungeon = Dungeon(level_number)
        if reset_player or not hasattr(self, "player"):
            self.player = Player(self.dungeon)
        else:
            self.player.dungeon = self.dungeon
            self.player.position = self.player.start_position.copy()
            self.player.direction = pygame.Vector2(0, 1)
            self.player.attack_cooldown = 0.0
            self.player.attack_effect_timer = 0.0
            self.player.power_up_timer = 0.0
        self.key = Key((20.5 * TILE_SIZE, HUD_HEIGHT + 13.5 * TILE_SIZE))
        coin_positions = (
            (5.5, 2.5), (11.5, 4.5), (19.5, 2.5), (5.5, 12.5),
            (13.5, 10.5), (19.5, 13.5),
        )
        self.coins = [Coin((column * TILE_SIZE, HUD_HEIGHT + row * TILE_SIZE))
                      for column, row in coin_positions[:3 + level_number]]
        self.potions = [Potion((8.5 * TILE_SIZE, HUD_HEIGHT + 14.5 * TILE_SIZE))]
        self.power_up = AttackPowerUp((16.5 * TILE_SIZE, HUD_HEIGHT + 6.5 * TILE_SIZE))
        self.enemies = self.create_enemies(level_number)

    def create_enemies(self, level_number):
        chaser_positions = {
            1: ((10.5, 4.5), (18.5, 4.5)),
            2: ((10.5, 4.5), (18.5, 4.5), (4.5, 12.5)),
            3: ((10.5, 4.5), (18.5, 4.5), (4.5, 12.5)),
        }[level_number]
        enemies = [ChaserEnemy(self.dungeon, (column * TILE_SIZE, HUD_HEIGHT + row * TILE_SIZE))
                   for column, row in chaser_positions]
        patrol_positions = {
            1: [((11.5, 12.5), (16.5, 12.5))],
            2: [((5.5, 4.5), (10.5, 4.5)), ((15.5, 12.5), (20.5, 12.5))],
            3: [((5.5, 4.5), (10.5, 4.5)), ((15.5, 12.5), (20.5, 12.5))],
        }[level_number]
        for start, end in patrol_positions:
            enemies.append(PatrolEnemy(
                self.dungeon,
                (start[0] * TILE_SIZE, HUD_HEIGHT + start[1] * TILE_SIZE),
                (end[0] * TILE_SIZE, HUD_HEIGHT + end[1] * TILE_SIZE),
            ))
        if level_number == 3:
            enemies.append(BossEnemy(self.dungeon, (21.5 * TILE_SIZE, HUD_HEIGHT + 12.5 * TILE_SIZE)))
        return enemies

    def new_level(self):
        self.load_level(self.level_number, reset_player=True)

    def start_game(self):
        self.score = 0
        self.enemies_defeated = 0
        self.load_level(1, reset_player=True)
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
                self.update_game(delta_time)
            elif self.state == GameState.LEVEL_COMPLETE:
                self.update_transition(delta_time)
            self.draw()
        pygame.quit()
        sys.exit()

    @property
    def exit_unlocked(self):
        boss_alive = any(isinstance(enemy, BossEnemy) and enemy.alive for enemy in self.enemies)
        return self.key.collected and not boss_alive

    def update_game(self, delta_time):
        self.notification_timer = max(0.0, self.notification_timer - delta_time)
        self.player.update(delta_time)
        for enemy in self.enemies:
            enemy.update(delta_time, self.player)
            if enemy.alive and enemy.rect.colliderect(self.player.rect):
                self.player.take_damage(enemy.contact_damage)
        self.collect_items()
        defeated = [enemy for enemy in self.enemies if not enemy.alive]
        if defeated:
            self.enemies_defeated += len(defeated)
            self.score += sum(100 if isinstance(enemy, BossEnemy) else 25 for enemy in defeated)
            self.enemies = [enemy for enemy in self.enemies if enemy.alive]
            if any(isinstance(enemy, BossEnemy) for enemy in defeated):
                self.announce("BOSS DEFEATED!")
        if not self.player.alive:
            self.state = GameState.GAME_OVER
            self.save_high_score()
            return
        if self.player.rect.colliderect(self.dungeon.exit_rect) and self.exit_unlocked:
            self.advance_level()

    def collect_items(self):
        player_rect = self.player.rect
        if not self.key.collected and player_rect.colliderect(self.key.rect):
            self.key.collected = True
            self.score += 25
            self.announce("KEY FOUND!")
        for coin in self.coins:
            if not coin.collected and player_rect.colliderect(coin.rect):
                coin.collected = True
                self.score += COIN_VALUE
        for potion in self.potions:
            if not potion.collected and player_rect.colliderect(potion.rect):
                potion.collected = True
                old_health = self.player.health
                self.player.health = min(self.player.max_health, self.player.health + POTION_HEAL)
                if self.player.health > old_health:
                    self.announce("HEALTH RESTORED!")
        if not self.power_up.collected and player_rect.colliderect(self.power_up.rect):
            self.power_up.collected = True
            self.player.power_up_timer = POWER_UP_DURATION
            self.announce("ATTACK POWERED!")

    def advance_level(self):
        self.save_high_score()
        if self.level_number == 3:
            self.state = GameState.FINAL_VICTORY
            return
        self.next_level_number = self.level_number + 1
        self.transition_timer = 0.8
        self.announce(f"LEVEL {self.level_number} COMPLETE!")
        self.state = GameState.LEVEL_COMPLETE

    def update_transition(self, delta_time):
        self.transition_timer = max(0.0, self.transition_timer - delta_time)
        if self.transition_timer == 0:
            self.load_level(self.next_level_number)
            self.announce(f"LEVEL {self.next_level_number} BEGIN!")
            self.state = GameState.PLAYING

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
                    GameState.LEVEL_COMPLETE, GameState.GAME_OVER,
                    GameState.FINAL_VICTORY):
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
        if self.state == GameState.FINAL_VICTORY:
            return self.victory_buttons
        return []

    def draw(self):
        if self.state in (GameState.PLAYING, GameState.PAUSED,
                  GameState.LEVEL_COMPLETE, GameState.GAME_OVER):
            self.draw_game()
        elif self.state == GameState.FINAL_VICTORY:
            self.draw_victory()
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
        self.draw_centered(f"HIGH SCORE: {self.high_score}", 285, self.small_font, TEXT)
        for index, button in enumerate(self.menu_buttons):
            button.draw(self.screen, index == self.menu_selection)
        self.draw_centered("Use mouse or arrow keys to navigate", 590, self.small_font, MUTED)

    def draw_instructions(self):
        self.draw_background()
        self.draw_centered("HOW TO PLAY", 125, self.heading_font, GOLD_BRIGHT)
        panel = pygame.Rect(220, 165, 560, 365)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=8)
        pygame.draw.rect(self.screen, (80, 71, 89), panel, 2, border_radius=8)
        instructions = [
            ("WASD / Arrow Keys", "Move your hero through the dungeon"),
            ("SPACE", "Attack enemies in the direction you face"),
            ("ESC", "Pause the game"),
            ("Explore", "Collect keys, coins, potions, and power-ups"),
            ("Objective", "Unlock the exit and defeat the final boss"),
        ]
        for index, (label, description) in enumerate(instructions):
            y = 190 + index * 58
            self.screen.blit(self.body_font.render(label, True, GOLD_BRIGHT), (295, y))
            self.screen.blit(self.small_font.render(description, True, TEXT), (295, y + 28))
        self.instruction_buttons[0].draw(self.screen)

    def draw_game(self):
        self.dungeon.draw(self.screen, self.exit_unlocked)
        for item in self.coins + self.potions + [self.key, self.power_up]:
            if not item.collected:
                item.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)
        pygame.draw.rect(self.screen, INK, (0, 0, SCREEN_WIDTH, HUD_HEIGHT))
        self.screen.blit(self.heading_font.render("SHADOW QUEST", True, GOLD_BRIGHT), (20, 16))
        self.screen.blit(self.small_font.render(
            f"HP: {self.player.health}/{self.player.max_health}", True, TEXT), (260, 8))
        health_bar = pygame.Rect(260, 34, 150, 12)
        pygame.draw.rect(self.screen, HEALTH_EMPTY, health_bar, border_radius=4)
        health_width = round(health_bar.width * self.player.health / self.player.max_health)
        if health_width:
            pygame.draw.rect(self.screen, HEALTH_GREEN,
                             (health_bar.left, health_bar.top, health_width, health_bar.height), border_radius=4)
        self.screen.blit(self.small_font.render(
            f"SCORE: {self.score}", True, TEXT), (440, 8))
        self.screen.blit(self.small_font.render(
            f"LEVEL: {self.level_number}/3", True, TEXT), (440, 38))
        self.screen.blit(self.small_font.render(
            f"KEY: {'FOUND' if self.key.collected else 'MISSING'}", True,
            KEY_COLOR if self.key.collected else MUTED), (575, 8))
        self.screen.blit(self.small_font.render(
            f"ENEMIES: {len(self.enemies)} / {self.enemies_defeated}", True, TEXT), (575, 38))
        power_text = f"POWER: {self.player.power_up_timer:.1f}s" if self.player.power_up_timer > 0 else "POWER: --"
        self.screen.blit(self.small_font.render(power_text, True, POWER_UP if self.player.power_up_timer > 0 else MUTED), (790, 8))
        objective = "BOSS: DEFEAT" if any(isinstance(enemy, BossEnemy) for enemy in self.enemies) else (
            "EXIT: UNLOCKED" if self.exit_unlocked else "EXIT: FIND KEY")
        self.screen.blit(self.small_font.render(objective, True, MUTED), (790, 38))
        if self.notification_timer > 0:
            self.draw_centered(self.notification, 100, self.body_font, GOLD_BRIGHT)
        if self.state == GameState.PAUSED:
            self.draw_overlay("PAUSED", "The dungeon waits in silence.", self.pause_buttons)
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_overlay("LEVEL COMPLETE", f"Enemies defeated: {self.enemies_defeated}", self.complete_buttons)
        elif self.state == GameState.GAME_OVER:
            self.draw_overlay("GAME OVER", f"Enemies defeated: {self.enemies_defeated}", self.game_over_buttons)

    def draw_victory(self):
        self.draw_background()
        self.draw_centered("SHADOW QUEST", 150, self.title_font, GOLD_BRIGHT)
        self.draw_centered("VICTORY!", 245, self.heading_font, HEALTH_GREEN)
        self.draw_centered(f"FINAL SCORE: {self.score}", 315, self.body_font, TEXT)
        self.draw_centered(f"ENEMIES DEFEATED: {self.enemies_defeated}", 350, self.body_font, TEXT)
        self.draw_centered("The dungeon has fallen silent.", 390, self.small_font, MUTED)
        self.draw_centered(f"HIGH SCORE: {self.high_score}", 425, self.small_font, GOLD_BRIGHT)
        for index, button in enumerate(self.victory_buttons):
            button.draw(self.screen, index == self.menu_selection)

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