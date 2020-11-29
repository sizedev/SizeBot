from decimal import Decimal
import io
import importlib.resources as pkg_resources
import math
from functools import lru_cache
from sizeroyale.lib.units import SV

import requests
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageOps import grayscale

import sizeroyale.data
from sizeroyale.lib.errors import DownloadError
from sizeroyale.lib.utils import chunkList, truncate

discord_gray = (0x36, 0x39, 0x3F, 255)


@lru_cache(50)
def download_image(url):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        return Image.open(io.BytesIO(r.content))
    else:
        raise DownloadError(f"Image could not be downloaded: {url!r}.")


# https://note.nkmk.me/en/python-pillow-square-circle-thumbnail/
def crop_center(pil_img: Image, crop_width, crop_height) -> Image:
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


# https://note.nkmk.me/en/python-pillow-square-circle-thumbnail/
def crop_max_square(pil_img: Image) -> Image:
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


def merge_images(images: list) -> Image:
    widths = [i.size[0] for i in images]
    heights = [i.size[1] for i in images]

    result_width = sum(widths)
    result_height = max(heights)

    result = Image.new('RGBA', (result_width, result_height))

    current_width = 0
    for i in images:
        result.paste(im = i, box = (current_width, 0))
        current_width += i.size[0]
    return result


def merge_images_vertical(images: list) -> Image:
    widths = [i.size[0] for i in images]
    heights = [i.size[1] for i in images]

    result_width = max(widths)
    result_height = sum(heights)

    result = Image.new('RGBA', (result_width, result_height))

    current_height = 0
    for n, i in enumerate(images):
        pos = 0
        if n == len(images) - 1:
            pos = (result_width - i.width) // 2
        result.paste(im = i, box = (pos, current_height))
        current_height += i.size[1]
    return result


@lru_cache(maxsize = 50)
def create_profile_picture(system: str, url: str, name: str, team, height: Decimal, dead: bool):
    px = 200
    size = (px, px)

    raw_image = download_image(url)
    height_text = SV.format(height, system)

    i = raw_image.convert("RGBA")
    i = crop_max_square(i)
    i = i.resize(size)
    rgbimg = Image.new("RGBA", i.size)
    rgbimg.paste(discord_gray, (0, 0, px, px))
    rgbimg.paste(i, (0, 0), i)
    i = rgbimg
    d = ImageDraw.Draw(i)
    with pkg_resources.path(sizeroyale.data, "Roobert-SemiBold.otf") as p:
        fnt_semibold = ImageFont.truetype(str(p.absolute()), size = 20)
    with pkg_resources.path(sizeroyale.data, "Roobert-RegularItalic.otf") as p:
        fnt_italic = ImageFont.truetype(str(p.absolute()), size = 14)
    with pkg_resources.path(sizeroyale.data, "Roobert-Regular.otf") as p:
        fnt = ImageFont.truetype(str(p.absolute()), size = 14)
    tname = name
    while fnt_semibold.getsize(name)[0] > i.width:
        tname = truncate(name, len(name) - 1)
    textwidth, textheight = fnt_semibold.getsize(name)
    d.text(((i.width - textwidth) // 2, i.height - textheight - 20),
           tname, align = "center", font = fnt_semibold, fill = (0, 0, 0),
           stroke_width = 2, stroke_fill = (255, 255, 255))
    d.text((10, 10),
           team, align = "center", font = fnt_italic, fill = (0, 0, 0),
           stroke_width = 2, stroke_fill = (255, 255, 255))
    d.text(((i.width - textwidth) // 2, i.height - textheight + 3),
           height_text, align = "center", font = fnt, fill = (0, 0, 0),
           stroke_width = 2, stroke_fill = (255, 255, 255))

    if dead:
        i = kill(i)

    return i


def kill(image: Image, *, gray: bool = True, x: bool = True, color = (255, 0, 0), width: int = 5) -> Image:
    i = image
    if gray:
        i = grayscale(i)
        rgbimg = Image.new("RGBA", i.size)
        rgbimg.paste(i)
        i = rgbimg
    if x:
        draw = ImageDraw.Draw(i)
        draw.line((0, 0) + i.size, fill = color, width = width)
        draw.line((0, i.size[1], i.size[0], 0), fill = color, width = width)
    return i


def create_stats_screen(players) -> Image:
    image_list = [p.image for p in sorted(players.values())]
    height = math.ceil(math.sqrt(len(image_list)))

    images = [merge_images(chunk) for chunk in chunkList(image_list, height)]

    return merge_images_vertical(images)
