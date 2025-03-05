from PIL import Image
import cv2
import numpy as np
import subprocess
import os

def png_to_bmp(input_png, output_bmp):
    # Đọc ảnh và chuyển sang chế độ grayscale
    image = Image.open(input_png).convert('L')

    # Tạo một ảnh binary (để dễ dàng sử dụng với potrace)
    binary = image.point(lambda x: 0 if x < 128 else 255, '1')

    # Lưu ảnh binary thành file bitmap tạm thời
    binary.save(output_bmp)

def png_to_eps_vector(input_png, output_eps):
    # Tên file bitmap tạm thời
    temp_bmp = 'temp.bmp'

    # Chuyển đổi PNG sang bitmap
    png_to_bmp(input_png, temp_bmp)

    # Sử dụng potrace để chuyển đổi bitmap thành đối tượng và lưu thành file EPS
    subprocess.run(['potrace', temp_bmp, '-b', 'eps', '-o', output_eps])

    # Xóa file bitmap tạm thời
    os.remove(temp_bmp)

def color_image_to_vector(input_image, output_eps, temp_eps="temp_vector.eps"):
    # Đọc ảnh có hỗ trợ kênh alpha
    image = cv2.imread(input_image, cv2.IMREAD_UNCHANGED)

    # Nếu ảnh có kênh alpha, sử dụng làm mask tách nền
    if image.shape[2] == 4:
        alpha_channel = image[:, :, 3]  # Lấy kênh alpha
        _, binary = cv2.threshold(alpha_channel, 1, 255, cv2.THRESH_BINARY)
    else:
        # Nếu không có kênh alpha, chuyển ảnh sang grayscale rồi áp dụng threshold
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    # Lưu ảnh đen trắng 1-bit để dùng với Potrace
    temp_bmp = "temp_bitmap.bmp"
    cv2.imwrite(temp_bmp, binary)

    # Dùng Potrace để chuyển bitmap thành vector EPS
    subprocess.run(["potrace", temp_bmp, "-b", "eps", "-o", temp_eps])

    # Ghi lại file EPS với màu gốc bằng cách chồng ảnh màu lên EPS vector
    merge_color_with_vector(temp_eps, input_image, output_eps)

    # Xóa file tạm
    os.remove(temp_bmp)
    os.remove(temp_eps)

def merge_color_with_vector(vector_eps, input_image, output_eps):

    # Dùng Inkscape để import vector EPS và ảnh màu, sau đó xuất file cuối cùng
    inkscape_path = "C:\\Program Files\\Inkscape\\bin\\inkscape.exe"  # Cập nhật đường dẫn nếu cần
    command = f'"{inkscape_path}" --batch-process --actions="file-open:{vector_eps};file-import:{input_image};file-save-as:{output_eps};file-close"'

    subprocess.run(command, shell=True)


def png_to_eps_outline(input_png, output_eps):
    # Đọc ảnh grayscale
    image = cv2.imread(input_png, cv2.IMREAD_GRAYSCALE)

    # Dùng Canny để phát hiện đường viền
    edges = cv2.Canny(image, 100, 200)

    # Lưu ảnh đường viền thành file bitmap 1-bit
    temp_bmp = "temp_edges.bmp"
    cv2.imwrite(temp_bmp, edges)

    # Dùng Potrace để chuyển bitmap thành vector EPS với chế độ centerline
    subprocess.run(["potrace", "-c", temp_bmp, "-b", "eps", "-o", output_eps])

    # Xóa file tạm
    os.remove(temp_bmp)


if __name__ == "__main__":
    images = ['black', 'origin']
    images_outline = ['outline']


    input_png = 'images/black.png'
    output_bmp = 'images/export/eps/black.eps'
    png_to_eps_vector(input_png, output_bmp)
    print(f"Converted {input_png} to {output_bmp}")

    input_png = f'images/origin.png'
    output_bmp = f'images/export/eps/origin.eps'
    color_image_to_vector(input_png, output_bmp)
    print(f"Converted {input_png} to {output_bmp}")

    input_png = f'images/outline.png'
    output_bmp = f'images/export/eps/outline.eps'
    png_to_eps_outline(input_png, output_bmp)
    print(f"Converted {input_png} to {output_bmp}")

