import pygame

from ui.assets import load_image


KIT_PATH = "assets/ui/pixel_kit"
SOURCE_PATH = "assets/ui/pixel_kit/sources"
TILE = 16
BUTTON_HEIGHT = 40
TAB_HEIGHT = 38
SLOT_SIZE = 48
PANEL_SOURCE_BORDER = 96
PANEL_TARGET_BORDER = 48

_KIT_CACHE = {}


def _asset(name):
    if name not in _KIT_CACHE:
        _KIT_CACHE[name] = load_image(f"{KIT_PATH}/{name}")
    return _KIT_CACHE[name]


def _source_asset(name):
    key = f"sources/{name}"
    if key not in _KIT_CACHE:
        _KIT_CACHE[key] = load_image(f"{SOURCE_PATH}/{name}")
    return _KIT_CACHE[key]


def _tile_surface(screen, image, rect):
    if image is None:
        return
    for y in range(rect.y, rect.bottom, image.get_height()):
        for x in range(rect.x, rect.right, image.get_width()):
            target = pygame.Rect(x, y, image.get_width(), image.get_height())
            screen.blit(image, target, area=target.clip(rect).move(-x, -y))


def _blit_scaled(screen, image, source_rect, target_rect):
    source_rect = pygame.Rect(source_rect)
    target_rect = pygame.Rect(target_rect)
    if target_rect.width <= 0 or target_rect.height <= 0:
        return
    piece = image.subsurface(source_rect)
    if piece.get_size() != target_rect.size:
        piece = pygame.transform.scale(piece, target_rect.size)
    screen.blit(piece, target_rect)


def _draw_panel_from_source(screen, rect, image):
    rect = pygame.Rect(rect)
    source_border = PANEL_SOURCE_BORDER
    target_border = min(
        PANEL_TARGET_BORDER,
        max(1, rect.width // 3),
        max(1, rect.height // 3),
    )
    source_w, source_h = image.get_size()
    source_center_w = source_w - source_border * 2
    source_center_h = source_h - source_border * 2
    target_center_w = rect.width - target_border * 2
    target_center_h = rect.height - target_border * 2

    columns = (
        (0, target_border, source_border),
        (target_border, target_center_w, source_center_w),
        (rect.width - target_border, target_border, source_border),
    )
    rows = (
        (0, target_border, source_border),
        (target_border, target_center_h, source_center_h),
        (rect.height - target_border, target_border, source_border),
    )
    source_columns = (0, source_border, source_w - source_border)
    source_rows = (0, source_border, source_h - source_border)

    for row_index, (target_y, target_h, source_h_part) in enumerate(rows):
        for col_index, (target_x, target_w, source_w_part) in enumerate(columns):
            _blit_scaled(
                screen,
                image,
                (
                    source_columns[col_index],
                    source_rows[row_index],
                    source_w_part,
                    source_h_part,
                ),
                (
                    rect.x + target_x,
                    rect.y + target_y,
                    target_w,
                    target_h,
                ),
            )


def draw_panel(screen, rect, fallback_draw=None):
    rect = pygame.Rect(rect)
    source_panel = _source_asset("ui_pixel_kit_panel_01.png")
    if source_panel is not None and source_panel.get_size() == (432, 432):
        _draw_panel_from_source(screen, rect, source_panel)
        return

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
