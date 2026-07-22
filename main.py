import pygame

import settings as cfg
from game.entities import Ball, Bonus, Brick, LaserBullet, Paddle
from game.level import load_level
from screens.game_screen import draw_hud, update_bonuses, update_lasers


def _bounce_off_rect(ball: Ball, rect: pygame.Rect):
    """ Checks if the Ball collides with the given rect. """

    # Calculate ball's overlaps and find the smallest one
    overlap_left = ball.rect.right - rect.left
    overlap_right = rect.right - ball.rect.left
    overlap_top = ball.rect.bottom - rect.top
    overlap_bottom = rect.bottom - ball.rect.top

    min_overlap = min(
        overlap_bottom,
        overlap_left,
        overlap_right,
        overlap_top)

    # Calculate the Ball's final velocities
    if min_overlap == overlap_top and ball.vy > 0:
        ball.rect.bottom = rect.top
        ball.vy *= -1
    elif min_overlap == overlap_bottom and ball.vy < 0:
        ball.rect.top = rect.bottom
        ball.vy *= -1
    elif min_overlap == overlap_left and ball.vx > 0:
        ball.rect.right = rect.left
        ball.vx *= -1
    elif min_overlap == overlap_right and ball.vx < 0:
        ball.rect.left = rect.right
        ball.vx *= -1


def _handle_ball_vs_bricks(
    ball: Ball,
    bricks: list[Brick],
    bonuses: list[Bonus],
) -> int:

    scored = 0
    for brick in bricks[:]:
        if not ball.rect.colliderect(brick.rect):
            continue
        _bounce_off_rect(ball, brick.rect)
        if brick.hp == -1:
            continue
        bonus_type = brick.hit()

        if brick.hp <= 0:
            bricks.remove(brick)
            scored += 10
            if bonus_type:
                bonuses.append(Bonus(brick.rect.center, bonus_type))
    return scored


def _handle_ball_vs_paddle(ball: Ball, paddle: Paddle) -> None:
    """ Handles Ball bounce over the Paddle. """
    _bounce_off_rect(ball, paddle.rect)
    offset = (ball.rect.centerx - paddle.rect.centerx) / (paddle.rect.width / 2)
    max_vx = cfg.MAX_BALL_SPEED_X
    ball.vx = max(-max_vx, min(max_vx, offset * max_vx))


def _spawn_ball(paddle: Paddle) -> Ball:
    """ Creates a new Ball right above the Paddle. """
    return Ball(paddle.rect.centerx, paddle.rect.top - cfg.BALL_RADIUS - 2)


def main():
    pygame.init()
    screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
    pygame.display.set_caption("Arkanoid")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)

    running = True
    paddle = Paddle()

    bricks, rows, cols = load_level(1)
    balls = [_spawn_ball(paddle)]
    bonuses: list[Bonus] = []
    lasers: list[LaserBullet] = []

    score = 0
    lives = cfg.START_LIVES

    while running:
        # Main Loop
        screen.fill(cfg.BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:   # Press "close" button
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                lasers.extend(paddle.shoot())

        # Update Section
        keys = pygame.key.get_pressed()

        paddle.move(keys)

        for ball in balls[:]:
            ball.update()
            score += _handle_ball_vs_bricks(ball, bricks, bonuses)

            if ball.rect.colliderect(paddle.rect) and ball.vy > 0:
                _handle_ball_vs_paddle(ball, paddle)

            if ball.rect.top > cfg.HEIGHT:
                balls.remove(ball)

        if not balls:
            lives -= 1
            if lives <= 0:
                running = False
            else:
                balls.append(_spawn_ball(paddle))

        lives = update_bonuses(bonuses, paddle, balls, lives)
        score += update_lasers(lasers, bricks)

        # Draw Section
        for brick in bricks:
            brick.draw(screen)

        paddle.draw(screen)

        for ball in balls:
            ball.draw(screen)

        for bonus in bonuses:
            bonus.draw(screen)

        for bullet in lasers:
            bullet.draw(screen)

        draw_hud(screen, font, score, lives)

        pygame.display.flip()   # Screen Update
        clock.tick(cfg.FPS)         # FPS (Frames Per Second)

    pygame.quit()


if __name__ == "__main__":
    main()
