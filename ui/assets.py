import pygame


def load_image(path, size=None):
    try:
        image = pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError, OSError):
        return None

    if size is not None:
        image = pygame.transform.smoothscale(image, size)
    return image


def draw_background(screen, image, fallback_color):
    if image is not None:
        screen.blit(image, (0, 0))
        return

    screen.fill(fallback_color)
