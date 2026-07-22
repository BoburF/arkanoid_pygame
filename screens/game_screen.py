import pygame

import settings as cfg
from game.entities import Ball, Bonus, LaserBullet, Paddle


def apply_bonus(
    bonus_type: str,
    paddle: Paddle,
    balls: list[Ball],
    lives: int,
) -> int:
    """ Applies the effect of a caught Bonus and returns the number of lives. """
    if bonus_type == "extend":
        paddle.resize(cfg.PADDLE_RESIZE_STEP)

    elif bonus_type == "shrink":
        paddle.resize(-cfg.PADDLE_RESIZE_STEP)

    elif bonus_type == "speed_up":
        for ball in balls:
            ball.scale_speed(cfg.BALL_SPEED_FACTOR)

    elif bonus_type == "speed_down":
        for ball in balls:
            ball.scale_speed(1 / cfg.BALL_SPEED_FACTOR)

    elif bonus_type == "multiball":
        for ball in balls[:]:
            clone = Ball(ball.rect.centerx, ball.rect.centery)
            clone.vx = -ball.vx
            clone.vy = ball.vy
            balls.append(clone)

    elif bonus_type == "laser":
        paddle.laser = True

    elif bonus_type == "extra_life":
        lives += 1

    return lives


def update_bonuses(
    bonuses: list[Bonus],
    paddle: Paddle,
    balls: list[Ball],
    lives: int,
) -> int:
    """ Moves the Bonuses, applies the caught ones, returns the number of lives. """
    for bonus in bonuses[:]:
        bonus.update()

        if bonus.rect.colliderect(paddle.rect):
            bonuses.remove(bonus)
            lives = apply_bonus(bonus.type, paddle, balls, lives)
        elif bonus.rect.top > cfg.HEIGHT:
            bonuses.remove(bonus)

    return lives


def update_lasers(lasers: list[LaserBullet], bricks: list, particles=None) -> int:
    """ Moves the Bullets, destroys the hit Bricks, returns the scored points. """
    scored = 0
    for bullet in lasers[:]:
        bullet.update()

        if bullet.rect.bottom < 0:
            lasers.remove(bullet)
            continue

        for brick in bricks:
            if not bullet.rect.colliderect(brick.rect):
                continue
            lasers.remove(bullet)
            if brick.hp > 0:
                brick.hit()
                if brick.hp <= 0:
                    bricks.remove(brick)
                    scored += 10
            break

    return scored


def draw_hud(screen: pygame.Surface, font: pygame.font.Font, score: int, lives: int) -> None:
    """ Renders the score and the remaining lives in the top bar. """
    screen.blit(font.render(f"SCORE: {score}", True, cfg.WHITE), (cfg.FIELD_LEFT, 20))
    lives_text = font.render(f"LIVES: {lives}", True, cfg.WHITE)
    screen.blit(lives_text, lives_text.get_rect(topright=(cfg.FIELD_RIGHT, 20)))
