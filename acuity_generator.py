"""
acuity_generator.py
====================
Generates calibrated Snellen letter images.

Real Snellen math:
  At 6 metres, a 20/20 letter subtends 5 arc-minutes of visual angle.
  Letter height = 2 * 6000mm * tan(2.5 arcmin) = 8.73mm
  For 20/X: height = 8.73 * (X / 20) mm

  We simulate 6m viewing at 60cm by scaling proportionally:
  At 60cm the same angular size = 8.73 * (60/600) = 0.873mm per 20/20 letter

  Then convert mm → pixels using actual screen PPI.

Supersampling:
  Render at 4x resolution then downsample with LANCZOS filter.
  This gives sharp, anti-aliased edges matching real printed charts.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import math


# ── Font loader ───────────────────────────────────────────────────────────────
def _get_font(size_px: int) -> ImageFont.FreeTypeFont:
    paths = [
        "Sloan.ttf",                                              # best — real optotype font
        "arial.ttf",                                              # Windows
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",                               # Mac
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size_px)
            except Exception:
                continue
    return ImageFont.load_default()


# ── Core size calculation ─────────────────────────────────────────────────────

def snellen_px(denominator: float, screen_inches: float,
               screen_w_px: int, screen_h_px: int) -> int:
    """
    Calculate the correct font size in pixels for a Snellen denominator
    on a specific screen, at a 60cm viewing distance.

    Parameters
    ----------
    denominator  : Snellen denominator (e.g. 40 for 20/40)
    screen_inches: Diagonal screen size in inches
    screen_w_px  : Horizontal resolution in pixels
    screen_h_px  : Vertical resolution in pixels

    Returns
    -------
    Font size in pixels (integer)
    """
    # Physical screen height in mm
    aspect      = screen_w_px / screen_h_px
    h_inches    = screen_inches / math.sqrt(1.0 + aspect ** 2)
    h_mm        = h_inches * 25.4
    mm_per_px   = h_mm / screen_h_px

    # Real Snellen letter height at 60cm viewing distance
    # Standard test distance is 6000mm; we use 600mm (60cm)
    # So scale factor = 600/6000 = 0.1
    VIEW_DIST_MM  = 600.0
    REAL_DIST_MM  = 6000.0
    BASE_MM_AT_6M = 8.73       # height of 20/20 letter at 6 metres

    letter_mm  = BASE_MM_AT_6M * (denominator / 20.0) * (VIEW_DIST_MM / REAL_DIST_MM)
    font_px    = letter_mm / mm_per_px

    return max(8, int(round(font_px)))


# ── Image generator ───────────────────────────────────────────────────────────

def generate_acuity_image(letters: str, denominator: float,
                           screen_inches: float,
                           screen_w_px: int, screen_h_px: int,
                           contrast: float = 1.0) -> Image.Image:
    """
    Generate a sharp, calibrated Snellen letter row image.

    Parameters
    ----------
    letters      : The letter string to render (e.g. "D H N R S")
    denominator  : Snellen denominator (40 for 20/40)
    screen_inches: Diagonal size of screen in inches
    screen_w_px  : Horizontal resolution
    screen_h_px  : Vertical resolution
    contrast     : 1.0 = full black on white (default)
                   0.5 = 50% grey on white (contrast sensitivity test)

    Returns
    -------
    PIL Image (RGB, white background)
    """
    # Target font size at actual display resolution
    font_px   = snellen_px(denominator, screen_inches, screen_w_px, screen_h_px)

    # ── Supersampling ─────────────────────────────────────────────────────────
    # Render at SCALE × resolution, then downsample for sharp anti-aliasing
    SCALE     = 4
    img_w     = max(1000, font_px * 14)
    img_h     = max(font_px * 3, 150)

    # High-res canvas
    hi_w      = img_w * SCALE
    hi_h      = img_h * SCALE
    hi_img    = Image.new("RGB", (hi_w, hi_h), "white")
    hi_draw   = ImageDraw.Draw(hi_img)
    hi_font   = _get_font(font_px * SCALE)

    # Letter colour based on contrast parameter
    # contrast=1.0 → black (0,0,0)
    # contrast=0.5 → mid-grey (128,128,128)
    grey      = int((1.0 - contrast) * 255)
    fill      = (grey, grey, grey)

    hi_draw.text(
        (hi_w // 2, hi_h // 2),
        letters,
        fill=fill,
        font=hi_font,
        anchor="mm"
    )

    # Downsample with LANCZOS (best quality anti-aliasing)
    img = hi_img.resize((img_w, img_h), Image.LANCZOS)

    return img


# ── Screen info helper ────────────────────────────────────────────────────────

def screen_ppi(screen_inches: float, screen_w_px: int, screen_h_px: int) -> float:
    """Return the pixels-per-inch of a screen."""
    diag_px = math.sqrt(screen_w_px**2 + screen_h_px**2)
    return diag_px / screen_inches