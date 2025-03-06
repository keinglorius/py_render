import os
import cv2
import subprocess
import numpy as np
from skimage.morphology import skeletonize
import networkx as nx
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev
import matplotlib.patches as patches
from scipy.spatial import Delaunay
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from PIL import Image
from bs4 import BeautifulSoup
import svgwrite

folder = "imag"

#########################
# Convert pillow, potrace, inkscape
#########################

def convert_bmp_to_eps(bmp_path, eps_path):
    subprocess.run(["potrace", bmp_path, "-e", "-o", eps_path])

def convert_bmp_to_svg(bmp_path, svg_path):
    subprocess.run(["potrace", bmp_path, "-s", "-o", svg_path])

def convert_svg_to_eps(svg_path, eps_path):
    subprocess.run(["inkscape", svg_path, "--export-filename", eps_path, "--export-ps-level=3"])

def convert_png_to_bmp(png_path, bmp_path):
    img = Image.open(png_path).convert("RGBA")
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    img = Image.alpha_composite(background, img)
    img = img.convert("RGB")
    img.save(bmp_path, "BMP")

def convert_png_to_svg(png_path, svg_path):
    subprocess.run(['inkscape', png_path, '--export-filename', svg_path], check=True)

def convert_png_to_svg_vector(png_path, svg_path):
    subprocess.run([
        'inkscape', png_path,
        '--export-filename', svg_path,
        '--trace-bitmap',
        '--export-plain-svg'
    ], check=True)

def convert_png_to_svg_pixel(png_path, svg_path):
    image = Image.open(png_path).convert("RGBA")
    width, height = image.size

    # Tạo tệp SVG
    dwg = svgwrite.Drawing(svg_path, profile='tiny', size=(width, height))

    # Vòng lặp qua từng pixel
    for y in range(height):
        for x in range(width):
            r, g, b, a = image.getpixel((x, y))
            if a > 0:  # Nếu pixel không trong suốt
                fill_color = svgwrite.rgb(r, g, b)
                dwg.add(dwg.rect(insert=(x, y), size=(1, 1), fill=fill_color))

    # Lưu tệp SVG
    dwg.save()

#########################
# End
#########################



#########################
# Other function
#########################
def process_image(input_path):
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"❌ Không tìm thấy file: {input_path}")

    if img.shape[-1] == 4:
        alpha = img[:, :, 3]
        binary = np.where(alpha == 0, 0, 255).astype(np.uint8)
    else:
        binary = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(binary, 1, 255, cv2.THRESH_BINARY)

    return binary

def get_skeleton(input_path):
    binary = process_image(input_path)
    binary[binary > 0] = 1  # Convert to binary 0-1
    binary = cv2.medianBlur(binary, 3)
    skeleton = skeletonize(binary)
    skeleton = (skeleton * 255).astype(np.uint8)
    return skeleton

def clean_svg(svg_path):
    with open(svg_path, "r", encoding="utf-8") as file:
        svg_data = file.read()

    soup = BeautifulSoup(svg_data, "xml")
    for g in soup.find_all("g"):
        g["fill"] = "none"
        g["stroke"] = "black"
        paths = g.find_all("path")
        if paths:
            paths[0].decompose()

    with open(svg_path, "w", encoding="utf-8") as file:
        file.write(str(soup))

#########################
# Main
#########################
def black(name_png):
    input_path = f'{folder}/{name_png}.png'
    temp_bmp = f'{folder}/temp/{name_png}.bmp'

    convert_png_to_bmp(input_path, temp_bmp)
    convert_bmp_to_svg(temp_bmp, f'{folder}/export/svg/{name_png}.svg')
    convert_bmp_to_eps(temp_bmp, f'{folder}/export/{name_png}.eps')

    os.remove(temp_bmp)

    print(f'✅ Xuất file EPS thành công: {folder}/export/{name_png}.eps')

def outline(name_png):
    input_path = f'{folder}/{name_png}.png'
    svg_path = f'{folder}/export/svg/{name_png}.svg'
    temp_bmp = f'{folder}/temp/{name_png}.bmp'

    skeleton = get_skeleton(input_path)
    cv2.imwrite(temp_bmp, skeleton, [cv2.IMWRITE_PXM_BINARY, 1])
    convert_bmp_to_svg(temp_bmp, svg_path)
    clean_svg(svg_path)
    convert_svg_to_eps(svg_path, f'{folder}/export/{name_png}.eps')

    os.remove(temp_bmp)

    print(f'✅ Xuất file EPS thành công: {folder}/export/{name_png}.eps')

def color(name_png, black_name_svg):
    input_path = f'{folder}/{name_png}.png'
    svg_path = f'{folder}/export/svg/{name_png}.svg'
    black_svg_path = f'{folder}/export/svg/{black_name_svg}.svg'
    temp_bmp = f'{folder}/temp/{name_png}.bmp'


    convert_png_to_svg_pixel(input_path, svg_path)
    convert_svg_to_eps(svg_path, f'{folder}/export/{name_png}.eps')

    # apply_mask_to_svg(svg_path, black_svg_path)

    # Xóa tạm BMP
    if os.path.exists(temp_bmp):
        os.remove(temp_bmp)

    print(f'✅ Xuất file SVG thành công: {svg_path}')

#########################
# End
#########################

# 🚀 Chạy chương trình

black_name = "1black"
black(black_name)

outline_name = "1outline"
outline(outline_name)

color_name = "1origin"
color(color_name, black_name)