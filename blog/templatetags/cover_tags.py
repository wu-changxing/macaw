from io import BytesIO
from pathlib import PurePosixPath

from django import template
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps

register = template.Library()

# Widest an index card ever shows a cover, in device pixels: a 1920x1186 cover is
# about 620 px wide on a 1440 desktop and on a 390 px phone at 2x, 930 px at 3x.
CARD_WIDTH = 960
# Making one copy takes ~150 ms, so one page render makes at most this many and
# links the full-size cover for the rest until a later render has made them.
MADE_PER_RENDER = 4


@register.simple_tag(takes_context=True)
def card_cover(context, cover):
    """URL of a CARD_WIDTH-wide WebP copy of a cover image, made on first use."""
    if not cover:
        return ""
    name = f"cards/{PurePosixPath(cover.name).with_suffix('')}-{CARD_WIDTH}.webp"
    if default_storage.exists(name):
        return default_storage.url(name)
    made = context.render_context.get("card_covers_made", 0)
    if made >= MADE_PER_RENDER or not default_storage.exists(cover.name):
        return cover.url  # cover still being generated, or missing: same URL as before
    context.render_context["card_covers_made"] = made + 1
    default_storage.save(name, ContentFile(resized_webp(cover)))
    return default_storage.url(name)


def resized_webp(cover):
    with default_storage.open(cover.name) as file, Image.open(file) as image:
        image = ImageOps.exif_transpose(image)  # browsers honour EXIF rotation; keep it
        image = image.convert("RGBA" if image.mode in ("RGBA", "LA", "P", "PA") else "RGB")
        if image.width > CARD_WIDTH:
            image = image.resize((CARD_WIDTH, round(image.height * CARD_WIDTH / image.width)), Image.LANCZOS)
        out = BytesIO()
        image.save(out, "WEBP", quality=90)
    return out.getvalue()
