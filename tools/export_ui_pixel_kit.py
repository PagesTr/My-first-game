"""Export the pixel UI kit PNGs from a single Aseprite atlas export.

Workflow:
1. Edit assets/ui/pixel_kit/sources/ui_pixel_kit_worksheet.png in Aseprite,
   or use it as the base layer for a .aseprite source.
2. Export the full atlas as assets/ui/pixel_kit/sources/ui_pixel_kit_worksheet.png.
3. Run: .\\.venv\\Scripts\\python.exe tools\\export_ui_pixel_kit.py

If Aseprite is available in PATH, or ASEPRITE_EXE points to aseprite.exe,
the script can also export the atlas PNG from the .aseprite source first.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pygame


ROOT = Path(__file__).resolve().parents[1]
KIT_DIR = ROOT / "assets" / "ui" / "pixel_kit"
SOURCE_DIR = KIT_DIR / "sources"
SOURCE_ASEPRITE = SOURCE_DIR / "ui_pixel_kit_01.aseprite"
SOURCE_PNG = SOURCE_DIR / "ui_pixel_kit_worksheet.png"
LEGACY_SOURCE_PNG = SOURCE_DIR / "ui_pixel_kit_01.png"


EXPORTS = {
    # Panel pieces, 16x16.
    "panel_corner_tl.png": (0, 0, 16, 16),
    "panel_edge_top.png": (16, 0, 16, 16),
    "panel_corner_tr.png": (32, 0, 16, 16),
    "panel_fill_dark.png": (48, 0, 16, 16),
    "panel_edge_left.png": (64, 0, 16, 16),
    "panel_edge_right.png": (80, 0, 16, 16),
    "panel_corner_bl.png": (96, 0, 16, 16),
    "panel_edge_bottom.png": (112, 0, 16, 16),
    "panel_corner_br.png": (128, 0, 16, 16),

    # Buttons, 16x40.
    "button_left.png": (0, 24, 16, 40),
    "button_center.png": (16, 24, 16, 40),
    "button_right.png": (32, 24, 16, 40),
    "button_hover_left.png": (48, 24, 16, 40),
    "button_hover_center.png": (64, 24, 16, 40),
    "button_hover_right.png": (80, 24, 16, 40),
    "button_disabled_left.png": (96, 24, 16, 40),
    "button_disabled_center.png": (112, 24, 16, 40),
    "button_disabled_right.png": (128, 24, 16, 40),

    # Tabs and slot frame.
    "tab_left.png": (0, 80, 16, 38),
    "tab_center.png": (16, 80, 16, 38),
    "tab_right.png": (32, 80, 16, 38),
    "slot_frame.png": (64, 80, 48, 48),

    # Rarity halos, 48x48.
    "slot_halo_common.png": (0, 128, 48, 48),
    "slot_halo_uncommon.png": (48, 128, 48, 48),
    "slot_halo_rare.png": (96, 128, 48, 48),
    "slot_halo_epic.png": (144, 128, 48, 48),
    "slot_halo_legendary.png": (192, 128, 48, 48),
    "slot_halo_unique.png": (240, 128, 48, 48),
}


def _find_aseprite() -> str | None:
    configured = os.environ.get("ASEPRITE_EXE")
    if configured and Path(configured).exists():
        return configured
    return shutil.which("aseprite") or shutil.which("Aseprite")


def _export_atlas_from_aseprite() -> bool:
    aseprite = _find_aseprite()
    if aseprite is None or not SOURCE_ASEPRITE.exists():
        return False

    subprocess.run(
        [
            aseprite,
            "-b",
            str(SOURCE_ASEPRITE),
            "--save-as",
            str(SOURCE_PNG),
        ],
        check=True,
    )
    return True


def _validate_source(atlas: pygame.Surface) -> None:
    width, height = atlas.get_size()
    missing = []
    for name, (x, y, w, h) in EXPORTS.items():
        if x + w > width or y + h > height:
            missing.append(f"{name}: {(x, y, w, h)} outside {width}x{height}")
    if missing:
        raise ValueError("\n".join(missing))


def export_pngs() -> None:
    source_png = SOURCE_PNG
    if not source_png.exists() and LEGACY_SOURCE_PNG.exists():
        source_png = LEGACY_SOURCE_PNG

    if not source_png.exists():
        exported = _export_atlas_from_aseprite()
        if not exported:
            raise FileNotFoundError(
                "Missing atlas PNG. Export the Aseprite source to:\n"
                f"{SOURCE_PNG}\n\n"
                "Or set ASEPRITE_EXE to your aseprite.exe path and rerun."
            )

    pygame.init()
    try:
        atlas = pygame.image.load(str(source_png))
        _validate_source(atlas)

        for name, rect in EXPORTS.items():
            output = KIT_DIR / name
            piece = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
            piece.blit(atlas, (0, 0), rect)
            pygame.image.save(piece, str(output))
            print(f"exported {output.relative_to(ROOT)}")
    finally:
        pygame.quit()


def main() -> int:
    try:
        export_pngs()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
