from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT_DIR / "assets"
PNG_PATH = ASSETS_DIR / "fengxi_app_icon.png"
ICO_PATH = ASSETS_DIR / "fengxi_app_icon.ico"
ICON_SIZE = 1024


def rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[index:index + 2], 16) for index in (0, 2, 4)) + (alpha,)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_color(start: tuple[int, int, int, int], end: tuple[int, int, int, int], t: float) -> tuple[int, int, int, int]:
    return tuple(int(round(lerp(start[index], end[index], t))) for index in range(4))


def cubic_points(p0, p1, p2, p3, steps: int = 96):
    points = []
    for step in range(steps + 1):
        t = step / steps
        omt = 1.0 - t
        x = (
            omt * omt * omt * p0[0]
            + 3 * omt * omt * t * p1[0]
            + 3 * omt * t * t * p2[0]
            + t * t * t * p3[0]
        )
        y = (
            omt * omt * omt * p0[1]
            + 3 * omt * omt * t * p1[1]
            + 3 * omt * t * t * p2[1]
            + t * t * t * p3[1]
        )
        points.append((x, y))
    return points


def add_rounded_gradient_tile(canvas: Image.Image) -> None:
    tile = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(tile)
    top = rgba("#183943")
    bottom = rgba("#0E6B77")
    for y in range(ICON_SIZE):
        mix = y / (ICON_SIZE - 1)
        draw.line((0, y, ICON_SIZE, y), fill=lerp_color(top, bottom, mix), width=1)

    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((-180, -120, 700, 640), fill=rgba("#FFF4D0", 88))
    glow_draw.ellipse((360, 420, 1160, 1220), fill=rgba("#052631", 116))
    tile.alpha_composite(glow.filter(ImageFilter.GaussianBlur(80)))

    gusts = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gust_draw = ImageDraw.Draw(gusts)
    gust_color = rgba("#9BE2D7", 28)
    gust_draw.arc((150, 150, 880, 760), start=195, end=348, fill=gust_color, width=16)
    gust_draw.arc((160, 320, 900, 950), start=182, end=320, fill=gust_color, width=12)
    tile.alpha_composite(gusts.filter(ImageFilter.GaussianBlur(2)))

    mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((74, 74, 950, 950), radius=234, fill=255)
    canvas.paste(tile, mask=mask)

    frame = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(frame)
    frame_draw.rounded_rectangle((88, 88, 936, 936), radius=220, outline=rgba("#F2D08A", 110), width=6)
    canvas.alpha_composite(frame)


def stroke_path(
    canvas: Image.Image,
    points,
    fill: tuple[int, int, int, int],
    width: int,
    glow_fill: tuple[int, int, int, int] | None = None,
    glow_width: int | None = None,
    blur_radius: int = 0,
) -> None:
    if glow_fill is not None:
        glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.line(points, fill=glow_fill, width=glow_width or width + 24, joint="curve")
        radius = (glow_width or width + 24) / 2
        for px, py in (points[0], points[-1]):
            glow_draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=glow_fill)
        canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(blur_radius)))

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    layer_draw.line(points, fill=fill, width=width, joint="curve")
    radius = width / 2
    for px, py in (points[0], points[-1]):
        layer_draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=fill)
    canvas.alpha_composite(layer)


def add_wind_mark(canvas: Image.Image) -> None:
    main_ribbon = cubic_points((238, 686), (398, 454), (556, 560), (758, 334))
    lower_ribbon = cubic_points((304, 790), (468, 842), (668, 676), (742, 502))
    inner_cut = cubic_points((348, 670), (500, 562), (588, 572), (664, 454))
    upper_flourish = cubic_points((424, 312), (500, 238), (626, 252), (736, 198))

    stroke_path(
        canvas,
        main_ribbon,
        fill=rgba("#F7EAD0", 255),
        width=110,
        glow_fill=rgba("#71D6D5", 82),
        glow_width=164,
        blur_radius=18,
    )
    stroke_path(
        canvas,
        lower_ribbon,
        fill=rgba("#8FE0D8", 248),
        width=82,
        glow_fill=rgba("#E6FBF6", 56),
        glow_width=126,
        blur_radius=16,
    )
    stroke_path(canvas, inner_cut, fill=rgba("#15515E", 230), width=40)
    stroke_path(canvas, upper_flourish, fill=rgba("#B8F4EC", 240), width=54)

    seal = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    seal_draw = ImageDraw.Draw(seal)
    cx, cy = 778, 232
    size = 104
    rotated_square = []
    for degree in (45, 135, 225, 315):
        radians = math.radians(degree)
        rotated_square.append((cx + math.cos(radians) * size / 2, cy + math.sin(radians) * size / 2))
    seal_draw.polygon(rotated_square, fill=rgba("#F1C76C", 255))
    seal_draw.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=rgba("#FFF5DA", 180))
    canvas.alpha_composite(seal.filter(ImageFilter.GaussianBlur(1)))

    highlight = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    highlight_draw = ImageDraw.Draw(highlight)
    highlight_draw.arc((214, 180, 872, 870), start=204, end=312, fill=rgba("#FFFFFF", 44), width=8)
    canvas.alpha_composite(highlight.filter(ImageFilter.GaussianBlur(1)))


def build_icon() -> Image.Image:
    canvas = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((104, 126, 944, 966), radius=218, fill=rgba("#06131A", 120))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(46)))
    add_rounded_gradient_tile(canvas)
    add_wind_mark(canvas)
    return canvas


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    icon = build_icon()
    icon.save(PNG_PATH)
    icon.save(
        ICO_PATH,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(PNG_PATH)
    print(ICO_PATH)


if __name__ == "__main__":
    main()
