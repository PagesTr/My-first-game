import pygame

from ui.assets import load_image


KIT_PATH = "assets/ui/pixel_kit"
TILE = 16
BUTTON_HEIGHT = 40
TAB_HEIGHT = 38
SLOT_SIZE = 48

_KIT_CACHE = {}


def _asset(name):
    if name not in _KIT_CACHE:
        _KIT_CACHE[name] = load_image(f"{KIT_PATH}/{name}")
    return _KIT_CACHE[name]


def _tile_surface(screen, image, rect):
    if image is None:
        return
    for y in range(rect.y, rect.bottom, image.get_height()):
        for x in range(rect.x, rect.right, image.get_width()):
            target = pygame.Rect(x, y, image.get_width(), image.get_height())
            screen.blit(image, target, area=target.clip(rect).move(-x, -y))


def draw_panel(screen, rect, fallback_draw=None):
    rect = pygame.Rect(rect)
    parts = {
        name: _asset(name)
        for name in (
            "panel_fill_dark.png",
            "panel_edge_top.png",
            "panel_edge_bottom.png",
            "panel_edge_left.png",
            "panel_edge_right.png",
            "panel_corner_tl.png",
            "panel_corner_tr.png",
            "panel_corner_bl.png",
            "panel_corner_br.png",
        )
    }
    if any(part is None for part in parts.values()):
        if fallback_draw:
            fallback_draw(screen, rect)
        return

    _tile_surface(screen, parts["panel_fill_dark.png"], rect.inflate(-TILE * 2, -TILE * 2))
    _tile_surface(
        screen,
        parts["panel_edge_top.png"],
        pygame.Rect(rect.x + TILE, rect.y, rect.width - TILE * 2, TILE),
    )
    _tile_surface(
        screen,
        parts["panel_edge_bottom.png"],
        pygame.Rect(rect.x + TILE, rect.bottom - TILE, rect.width - TILE * 2, TILE),
    )
    _tile_surface(
        screen,
        parts["panel_edge_left.png"],
        pygame.Rect(rect.x, rect.y + TILE, TILE, rect.height - TILE * 2),
    )
    _tile_surface(
        screen,
        parts["panel_edge_right.png"],
        pygame.Rect(rect.right - TILE, rect.y + TILE, TILE, rect.height - TILE * 2),
    )
    screen.blit(parts["panel_corner_tl.png"], rect.topleft)
    screen.blit(parts["panel_corner_tr.png"], (rect.right - TILE, rect.y))
    screen.blit(parts["panel_corner_bl.png"], (rect.x, rect.bottom - TILE))
    screen.blit(parts["panel_corner_br.png"], (rect.right - TILE, rect.bottom - TILE))


def draw_button(screen, rect, hovered=False, fallback_draw=None):
    rect = pygame.Rect(rect)
    prefix = "button_hover" if hovered else "button"
    left = _asset(f"{prefix}_left.png")
    center = _asset(f"{prefix}_center.png")
    right = _asset(f"{prefix}_right.png")
    if left is None or center is None or right is None:
        if fallback_draw:
            fallback_draw(screen, rect)
        return

    y = rect.centery - BUTTON_HEIGHT // 2
    screen.blit(left, (rect.x, y))
    _tile_surface(
        screen,
        center,
        pygame.Rect(rect.x + TILE, y, rect.width - TILE * 2, BUTTON_HEIGHT),
    )
    screen.blit(right, (rect.right - TILE, y))


def draw_tab(screen, rect, fallback_draw=None):
    rect = pygame.Rect(rect)
    left = _asset("tab_left.png")
    center = _asset("tab_center.png")
    right = _asset("tab_right.png")
    if left is None or center is None or right is None:
        if fallback_draw:
            fallback_draw(screen, rect)
        return

    y = rect.centery - TAB_HEIGHT // 2
    screen.blit(left, (rect.x, y))
    _tile_surface(
        screen,
        center,
        pygame.Rect(rect.x + TILE, y, rect.width - TILE * 2, TAB_HEIGHT),
    )
    screen.blit(right, (rect.right - TILE, y))


def draw_slot(screen, rect, fallback_draw=None):
    rect = pygame.Rect(rect)
    slot = _asset("slot_frame.png")
    if slot is None:
        if fallback_draw:
            fallback_draw(screen, rect)
        return

    if rect.size == (SLOT_SIZE, SLOT_SIZE):
        screen.blit(slot, rect)
        return

    scaled = pygame.transform.scale(slot, rect.size)
    screen.blit(scaled, rect)
