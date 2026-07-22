import math
import random

import pygame

import settings as cfg

class Paddle:
    """ Our main player, Paddle, moves only horizontally. """

    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, cfg.PADDLE_WIDTH, cfg.PADDLE_HEIGHT)
        self.rect.midbottom = (cfg.WIDTH // 2, cfg.HEIGHT - 20)
        self.speed = cfg.PADDLE_SPEED
        self.vx = 0
        self.extended = False
        self.laser = False
        self.cooldown = 0

    def resize(self, delta: int) -> None:
        """ Changes the Paddle's width by delta, keeping it centered. """
        new_width = max(
            cfg.PADDLE_MIN_WIDTH,
            min(cfg.PADDLE_MAX_WIDTH, self.rect.width + delta),
        )
        center_x = self.rect.centerx
        self.rect.width = new_width
        self.rect.centerx = center_x
        self.extended = new_width > cfg.PADDLE_WIDTH

        if self.rect.left < cfg.FIELD_LEFT:
            self.rect.left = cfg.FIELD_LEFT
        if self.rect.right > cfg.FIELD_RIGHT:
            self.rect.right = cfg.FIELD_RIGHT

    def shoot(self) -> list["LaserBullet"]:
        """ Fires a pair of bullets if the laser bonus is active. """
        if not self.laser or self.cooldown > 0:
            return []

        self.cooldown = cfg.LASER_COOLDOWN
        return [
            LaserBullet(self.rect.left + 4, self.rect.top),
            LaserBullet(self.rect.right - 4, self.rect.top),
        ]

    def move(self, keys: pygame.key.ScancodeWrapper):
        """ Moves the Paddle if the key is pressed. """
        if self.cooldown > 0:
            self.cooldown -= 1

        self.vx = 0
        if keys[pygame.K_LEFT]:
            self.vx = -self.speed
        elif keys[pygame.K_RIGHT]:
            self.vx = self.speed
        
        self.rect.x += self.vx

        # Restrict the Paddle's movement
        if self.rect.left < cfg.FIELD_LEFT:
            self.rect.left = cfg.FIELD_LEFT
        if self.rect.right > cfg.FIELD_RIGHT:
            self.rect.right = cfg.FIELD_RIGHT

    def draw(self, screen: pygame.Surface) -> None:
        """ Renders the Paddle on the screen. """
        pygame.draw.rect(screen, cfg.PADDLE_COLOR, self.rect, border_radius=5)


class Brick:
    """
        Class for Game's brick.

        HP = -1: Level Boundary
        HP = 0: Indestructable
        HP = 1, 2: One / Two hit
    """
    
    def __init__(self, col: int, row: int, hp: int) -> None:
        self.hp = hp
        self.color = cfg.BRICK_COLORS[hp]
        self.rect = pygame.Rect(
            cfg.FIELD_LEFT + col * cfg.BRICK_WIDTH,
            cfg.TOP_OFFSET + row * cfg.BRICK_HEIGHT,
            cfg.BRICK_WIDTH,
            cfg.BRICK_HEIGHT,
        )

    def draw(self, screen: pygame.Surface) -> None:
        """ Renders a Brick in a certain row and col. """
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, cfg.DARK_GRAY, self.rect, 2)
    
    def hit(self) -> str | None:
        """ Handles the Brick Hit, returns a bonus type if one is dropped. """
        if self.hp > 0:
            self.hp -= 1
            if self.hp > 0:
                self.color = cfg.BRICK_COLORS[self.hp]
                return None
            if random.random() < cfg.BONUS_PROBABILITY:
                return random.choice(cfg.BONUS_TYPES)
        return None

class Ball:
    """ Ball Actor class. """

    def __init__(self, x: int, y: int) -> None:
        self.radius = cfg.BALL_RADIUS
        self.rect = pygame.Rect(
            x - self.radius,
            y - self.radius,
            2 * self.radius,
            2 * self.radius,
        )
        self.vx = float(cfg.BALL_SPEED_X)
        self.vy = float(cfg.BALL_SPEED_Y)
        self._fx = 0.0
        self._fy = 0.0

    @property
    def speed(self) -> float:
        """ Current speed of the Ball, regardless of direction. """
        return math.hypot(self.vx, self.vy)

    def scale_speed(self, factor: float) -> None:
        """ Speeds the Ball up or slows it down, keeping its direction. """
        speed = self.speed
        if speed == 0:
            return

        new_speed = max(cfg.MIN_BALL_SPEED, min(cfg.MAX_BALL_SPEED, speed * factor))
        ratio = new_speed / speed
        self.vx *= ratio
        self.vy *= ratio

    def update(self) -> None:
        """ Updates the Ball's position for the each frame. """
        self._fx += self.vx
        self._fy += self.vy

        step_x = int(self._fx)
        step_y = int(self._fy)
        self._fx -= step_x
        self._fy -= step_y

        self.rect.x += step_x
        self.rect.y += step_y

    def draw(self, screen: pygame.surface) -> None:
        """ Renders the Ball. """
        colour = cfg.BALL_COLOR
        pygame.draw.circle(screen, colour, self.rect.center, self.radius)


class Bonus:
    """ Bonus emitted from a destroyed brick. """

    TYPES = {
        "extend": {"color": cfg.GREEN, "letter": "E"},
        "multiball": {"color": cfg.MAGENTA, "letter": "M"},
        "laser": {"color": cfg.YELLOW, "letter": "L"},
        "extra_life": {"color": cfg.CYAN, "letter": "1"},
        "shrink": {"color": cfg.ORANGE, "letter": "R"},
        "speed_up": {"color": cfg.RED, "letter": "F"},
        "speed_down": {"color": cfg.BLUE, "letter": "S"},
    }

    _label_font: pygame.font.Font | None = None

    def __init__(self, center: tuple[int, int], bonus_type: str) -> None:
        self.type = bonus_type
        self.rect = pygame.Rect(0, 0, 24, 24)
        self.rect.center = center
        self.vy = 3

        props = Bonus.TYPES[bonus_type]
        self.color = props["color"]
        self.letter = props["letter"]

    @classmethod
    def _get_label_font(cls) -> pygame.font.Font:
        """ Creates the label font once, on the first draw. """
        if cls._label_font is None:
            cls._label_font = pygame.font.Font(None, 24)
        return cls._label_font

    def update(self) -> None:
        """ Makes the Bonus fall down the screen. """
        self.rect.y += self.vy

    def draw(self, screen: pygame.Surface) -> None:
        """ Renders the Bonus with its letter. """
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        text = self._get_label_font().render(self.letter, True, cfg.BLACK)
        screen.blit(text, text.get_rect(center=self.rect.center))


class LaserBullet:
    """ Laser Bullet, flies upwards and destroys bricks. """

    def __init__(self, x: int, y: int) -> None:
        self.rect = pygame.Rect(x - 2, y, 4, 10)
        self.vy = -10

    def update(self) -> None:
        """ Moves the Bullet upwards. """
        self.rect.y += self.vy

    def draw(self, screen: pygame.Surface) -> None:
        """ Renders the Bullet. """
        pygame.draw.rect(screen, cfg.YELLOW, self.rect)