import numpy as np
import cv2
from PIL import Image
from svgpathtools import Path, QuadraticBezier
import subprocess
from svgpathtools import Path, QuadraticBezier

def contour_to_bezier_v2(contours, epsilon_factor=0.001):
    bezier_paths = []

    for contour in contours:
        contour = contour.reshape(-1, 2)

        # Giảm số lượng điểm bằng approxPolyDP (độ chính xác dựa trên epsilon)
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        path = Path()

        for i in range(len(approx)):
            p0 = approx[i - 1][0] if i > 0 else approx[-1][0]
            p1 = approx[i][0]
            p2 = approx[(i + 1) % len(approx)][0]

            # Xác định điểm điều khiển Bézier từ fitEllipse (nếu có đủ điểm)
            if len(approx) >= 5:
                (x, y), (MA, ma), angle = cv2.fitEllipse(contour)
                control_point = (x, y)
            else:
                control_point = (p0 + p2) / 2

            bezier_path = QuadraticBezier(complex(*p0), complex(*control_point), complex(*p1))
            path.append(bezier_path)

        bezier_paths.append(path)

    return bezier_paths


# Hàm chuyển các contour thành các đường Bézier bậc 2 (Quadratic Bézier)
def contour_to_bezier(contours):
    bezier_paths = []

    for contour in contours:
        contour = contour.reshape(-1, 2)  # Chuyển contour thành mảng 2D
        path = Path()

        # Tạo các điểm Bézier từ các điểm contour
        for i in range(len(contour)):
            p0 = contour[i - 1] if i > 0 else contour[-1]  # previous point
            p1 = contour[i]  # current point
            p2 = contour[(i + 1) % len(contour)]  # next point

            # Tạo điểm điều khiển trung gian cho đường Bézier
            control_point = (p0 + p2) / 2  # Điều chỉnh điều khiển điểm giữa

            # Tạo một Quadratic Bézier từ ba điểm
            bezier_path = QuadraticBezier(p0, control_point, p1)
            path.append(bezier_path)

        bezier_paths.append(path)

    return bezier_paths

# Hàm chuyển các đường Bézier thành file SVG
def save_as_svg(bezier_paths, output_path):
    min_x = min(segment.start.real for path in bezier_paths for segment in path)
    min_y = min(segment.start.imag for path in bezier_paths for segment in path)
    max_x = max(segment.end.real for path in bezier_paths for segment in path)
    max_y = max(segment.end.imag for path in bezier_paths for segment in path)

    width = max_x - min_x
    height = max_y - min_y

    svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {width} {height}">\n'

    # Duyệt qua các đường Bézier và thêm vào SVG
    for path in bezier_paths:
        for segment in path:
            d = f'M {segment.start.real} {segment.start.imag} Q {segment.control.real} {segment.control.imag} {segment.end.real} {segment.end.imag}'
            svg_content += f'<path d="{d}" stroke="black" stroke-width="1" fill="none" />\n'

    svg_content += '</svg>'

    with open(output_path, 'w') as file:
        file.write(svg_content)


# Hàm sử dụng Inkscape để chuyển SVG thành EPS
def convert_svg_to_eps(svg_path, eps_path):
    # Đảm bảo rằng bạn có Inkscape được cài đặt và có đường dẫn chính xác tới tệp thực thi Inkscape
    inkscape_path = r"C:\Program Files\Inkscape\bin\inkscape.exe"  # Cập nhật đường dẫn Inkscape nếu cần
    subprocess.run([inkscape_path, svg_path, '--export-filename', eps_path])

# Hàm phát hiện các đối tượng từ ảnh và trả về các contour
def detect_object(input_path):
    img = Image.open(input_path).convert("RGBA")
    img_np = np.array(img)

    # Tạo ảnh nhị phân từ kênh alpha (định dạng không nền)
    alpha_channel = img_np[:, :, 3]
    _, binary = cv2.threshold(alpha_channel, 1, 255, cv2.THRESH_BINARY)

    # Áp dụng Gaussian Blur để làm mượt viền
    blurred = cv2.GaussianBlur(binary, (3, 3), 3)

    # Tìm đường viền của đối tượng
    contours, _ = cv2.findContours(blurred, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    return contours

# Ví dụ sử dụng
img_name = "outline"
input_path = f"image/{img_name}.png"
contours = detect_object(input_path)


# Chuyển các contour thành Bézier và lưu thành SVG
bezier_paths = contour_to_bezier_v2(contours)
svg_path = f"image/export/{img_name}.svg"
save_as_svg(bezier_paths, svg_path)

# Chuyển SVG thành EPS bằng Inkscape
eps_path = f"image/export/{img_name}.eps"
convert_svg_to_eps(svg_path, eps_path)
