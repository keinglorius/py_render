import os
import cv2
import subprocess
import numpy as np
from skimage.morphology import skeletonize
from PIL import Image
from bs4 import BeautifulSoup
import svgwrite
from lxml import etree
import re


folder = "im"

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
        '--export-filename', svg_path
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
        if len(paths) > 1:
            for i, path in enumerate(paths):
                if i != 1:
                    path.decompose()

    with open(svg_path, "w", encoding="utf-8") as file:
        file.write(str(soup))

def apply_transformations(d, scale):
    path_commands = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|-?\d*\.?\d+', d)
    transformed_commands = []
    i = 0

    command_params = {
        'M': 2, 'L': 2, 'T': 2,
        'H': 1, 'V': 1,
        'C': 6, 'S': 4, 'Q': 4,
        'A': 7,  # A (rx ry x-axis-rotation large-arc-flag sweep-flag x y)
    }

    prev_command = None

    while i < len(path_commands):
        command = path_commands[i]
        if command.isalpha():
            transformed_commands.append(command)
            prev_command = command
            i += 1
        else:
            num_params = command_params.get(prev_command.upper(), 2)  # Default to (x, y)
            values = [float(path_commands[i + j]) for j in range(num_params)]

            if prev_command.upper() in {'M', 'L', 'T'}:
                values[0] /= scale[0]
                values[1] /= scale[1]
            elif prev_command.upper() == 'H':
                values[0] /= scale[0]
            elif prev_command.upper() == 'V':
                values[0] /= scale[1]
            elif prev_command.upper() in {'C', 'S', 'Q'}:
                for j in range(0, num_params, 2):
                    values[j] /= scale[0]
                    values[j + 1] /= scale[1]
            elif prev_command.upper() == 'A':
                values[0] /= scale[0]  # rx
                values[1] /= scale[1]  # ry
                values[5] /= scale[0]  # x
                values[6] /= scale[1]  # y

            transformed_commands.extend(f'{v:.6f}' for v in values)
            i += num_params

    return ' '.join(transformed_commands)

def extract_scale_from_transform(transform):
    match = re.search(r'scale\((-?\d*\.?\d+),\s*(-?\d*\.?\d+)\)', transform)
    if match:
        return float(match.group(1)), float(match.group(2))
    return 1.0, 1.0






def get_path_bbox(path_elem):
    """ Tính toán bounding box của path từ dữ liệu `d` """
    d_attr = path_elem.get("d", "")
    if not d_attr:
        return None

    # Trích xuất tất cả các số (tọa độ) từ `d`
    coords = list(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", d_attr)))

    if len(coords) < 2:
        return None  # Không đủ dữ liệu để tính bbox

    # Xác định min/max tọa độ
    min_x, min_y = min(coords[::2]), min(coords[1::2])
    max_x, max_y = max(coords[::2]), max(coords[1::2])

    return {
        "x": min_x,
        "y": min_y,
        "width": max_x - min_x,
        "height": max_y - min_y
    }

def fit_path_to_viewbox(path_elem, view_box):
    parent_g = path_elem.getparent()
    while parent_g is not None and parent_g.tag != f"{{{SVG_NS}}}g":
        parent_g = parent_g.getparent()
    existing_transform = parent_g.get("transform", "").strip() if parent_g is not None else ""

    # Nếu <g> không có transform, kiểm tra transform của path
    if not existing_transform:
        existing_transform = path_elem.get("transform", "").strip()

    new_transform = f"{existing_transform}"

    path_elem.set("transform", new_transform.strip())






SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

def process_svg(svg_path, svg_clip, output_svg):
    """Xử lý SVG, áp dụng clip-path và căn chỉnh image theo path."""
    tree_path = etree.parse(svg_path)
    tree_clip = etree.parse(svg_clip)

    root_clip = tree_clip.getroot()
    root_path = tree_path.getroot()

    image_elem = root_path.find(f".//{{{SVG_NS}}}image")
    if image_elem is None:
        raise ValueError("Không tìm thấy <image> trong svg_path")

    path_elem = root_clip.find(f".//{{{SVG_NS}}}path")
    if path_elem is None:
        raise ValueError("Không tìm thấy <path> trong svg_clip")

    width = root_path.get("width", "100%")
    height = root_path.get("height", "100%")
    view_box = root_clip.get("viewBox", "0 0 100 100")

    fit_path_to_viewbox(path_elem, view_box)

    new_svg = etree.Element(
        "svg",
        nsmap={"svg": SVG_NS, "xlink": XLINK_NS},
        version="1.1",
        id="COLOR",
        x="0px",
        y="0px",
        width=width,
        height=height,
        viewBox=view_box,
        style=f"enable-background:new {view_box};")

    main_group = etree.SubElement(new_svg, "g")

    defs = etree.SubElement(main_group, "defs")
    path_id = "SVGID_1_"
    path_elem.set("id", path_id)
    defs.append(path_elem)

    clip_id = "SVGID_clip"
    clip_path = etree.SubElement(main_group, "clipPath", id=clip_id)
    etree.SubElement(clip_path, "use", attrib={f"{{{XLINK_NS}}}href": f"#{path_id}", "style": "overflow:visible;"}, nsmap={"xlink": XLINK_NS})

    # Loại bỏ <g>, gán clip-path trực tiếp vào <image>
    image_elem.set("style", f"overflow:visible; clip-path:url(#{clip_id});")

    main_group.append(image_elem)

    new_tree = etree.ElementTree(new_svg)
    new_tree.write(output_svg, pretty_print=True, xml_declaration=True, encoding="UTF-8")


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

def gray(gray_name, black_name):
    svg_path = f'{folder}/export/svg/{black_name}.svg'
    gray_svg_path = f'{folder}/export/svg/{gray_name}.svg'

    # Load SVG
    tree = etree.parse(svg_path)
    root = tree.getroot()

    # Tìm tất cả các path và fill màu xám
    for path in root.findall(f".//{{{SVG_NS}}}path"):
        path.set("fill", "#787878")

    # Lưu SVG mới
    tree.write(gray_svg_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    convert_svg_to_eps(gray_svg_path, f'{folder}/export/{gray_name}.eps')

    print(f'✅ Xuất file EPS thành công: {folder}/export/{gray_name}.eps')

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

def color(name_png, black_name):
    input_path = f'{folder}/{name_png}.png'
    svg_path = f'{folder}/export/svg/{name_png}.svg'
    temp_bmp = f'{folder}/temp/{name_png}.bmp'

    convert_png_to_svg_vector(input_path, svg_path)

    process_svg(svg_path, f'{folder}/export/svg/{black_name}.svg', svg_path)
    convert_svg_to_eps(svg_path, f'{folder}/export/{name_png}.eps')

    # Xóa tạm BMP
    if os.path.exists(temp_bmp):
        os.remove(temp_bmp)

    print(f'✅ Xuất file SVG thành công: {svg_path}')

def merge_eps_to_ai(output_ai, *eps_files):
    """Merge multiple EPS files into a single AI file using Inkscape CLI."""
    if len(eps_files) < 2:
        raise ValueError("Cần ít nhất 2 file EPS để gộp.")

    # Tạo file SVG trung gian để nhập các EPS
    temp_svg = "merged_temp.svg"

    # Lệnh import tất cả EPS vào SVG
    cmd_import = ["inkscape", "--export-filename=" + temp_svg]
    for eps in eps_files:
        cmd_import.append("--import-file=" + eps)

    # Thực thi lệnh import
    subprocess.run(cmd_import, check=True)

    # Xuất SVG thành AI
    cmd_export = ["inkscape", temp_svg, "--export-filename=" + output_ai]
    subprocess.run(cmd_export, check=True)

    print(f"Đã gộp {len(eps_files)} file EPS thành {output_ai}")

#########################
# End
#########################

# 🚀 Chạy chương trình

black_name = "layer1"
black(black_name)

gray_name = "layer2"
gray(gray_name, black_name)

outline_name = "outlineImg"
outline(outline_name)

color_name = "originImg"
color(color_name, black_name)


# def merge_eps_to_ai(output_file, eps_files):
#     dwg = svgwrite.Drawing(output_file, profile="tiny")

#     for i, eps in enumerate(eps_files):
#         layer = dwg.add(dwg.g(id=f"Layer_{i+1}"))
#         layer.add(dwg.image(href=eps, insert=(0, 0), size=("100%", "100%")))

#     dwg.save()

# eps_files = [
#     f'{folder}/export/{black_name}.eps',
#     f'{folder}/export/{gray_name}.eps',
#     f'{folder}/export/{outline_name}.eps',
#     f'{folder}/export/{color_name}.eps'
# ]
# merge_eps_to_ai(f'{folder}/export/output.ai', eps_files)