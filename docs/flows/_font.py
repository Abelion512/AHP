"""Shared font lookup for the diagram generators (Pillow >= 10.1)."""

from PIL import ImageFont

DEJAVU = "/usr/share/fonts/truetype/dejavu/"
MAC = "/System/Library/Fonts/Supplemental/"
REG = ["DejaVuSans.ttf", DEJAVU + "DejaVuSans.ttf", "Arial.ttf", MAC + "Arial.ttf", "C:/Windows/Fonts/arial.ttf"]
BOLD = ["DejaVuSans-Bold.ttf", DEJAVU + "DejaVuSans-Bold.ttf", "Arial Bold.ttf", MAC + "Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]


def font(names, size):
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size)
    except TypeError:
        raise RuntimeError("Pillow >= 10.1 is required for readable diagram text") from None
