import os
import cv2
import subprocess
import numpy as np
from skimage.morphology import skeletonize
from PIL import Image

def svg_to_bmp(input_svg, output_bmp):
    inkscape_path = r"C:\Program Files\Inkscape\bin\Inkscape.exe"

    if not os.path.exists(inkscape_path):
        raise FileNotFoundError(f"❌ Không tìm thấy Inkscape tại: {inkscape_path}")

    cmd = [inkscape_path, input_svg, "--export-filename=" + output_bmp, "--export-type=bmp"]

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Chuyển {input_svg} → {output_bmp} thành công!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi chạy Inkscape: {e}")

def preprocess_image(input_path):
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"❌ Không tìm thấy file: {input_path}")

    _, binary = cv2.threshold(img, 1, 255, cv2.THRESH_BINARY)
    return binary

def get_skeleton(input_path):
    binary = preprocess_image(input_path)
    binary[binary > 0] = 1  # Chuyển sang nhị phân 0-1
    binary = cv2.medianBlur(binary, 3)
    skeleton = skeletonize(binary)
    skeleton = (skeleton * 255).astype(np.uint8)
    return skeleton

def save_skeleton_as_pbm(skeleton, pbm_path):
    cv2.imwrite(pbm_path, skeleton, [cv2.IMWRITE_PXM_BINARY, 1])

def convert_pbm_to_eps(pbm_path, eps_path):
    subprocess.run(["potrace", pbm_path, "-e", "-o", eps_path])

def svg_to_eps(input_svg, output_eps):
    temp_bmp = "imag/temp/temp.bmp"

    # Bước 1: Chuyển SVG sang BMP
    svg_to_bmp(input_svg, temp_bmp)

    # Bước 2: Làm mượt viền bằng skeleton
    skeleton = get_skeleton(temp_bmp)
    pbm_path = output_eps.replace(".eps", ".pbm")
    save_skeleton_as_pbm(skeleton, pbm_path)

    # Bước 3: Chuyển PBM sang EPS bằng Potrace
    convert_pbm_to_eps(pbm_path, output_eps)

    # Xóa file tạm
    os.remove(temp_bmp)
    os.remove(pbm_path)

    print(f"✅ Xuất file EPS thành công: {output_eps}")

# 🚀 Chạy chương trình
image = "outlineImg"
svg_to_eps(f"imag/{image}.svg", f"imag/export/{image}.eps")
