import os
import cv2
import numpy as np
from PIL import Image
import math
import svgwrite
import subprocess
from scipy.interpolate import BarycentricInterpolator
from scipy.interpolate import splprep, splev


# Hàm phát hiện đối tượng trong ảnh PNG không nền
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

# Hàm tính toán xấp xỉ Bezier
def bezier_curve_v1(points, n_points=100):
    """
    Tạo đường Bezier từ các điểm đã cho.
    `points`: Danh sách các điểm, mỗi điểm là tuple (x, y).
    `n_points`: Số lượng điểm trong đường Bezier.
    """
    points = np.array(points)
    x_points = points[:, 0]
    y_points = points[:, 1]

    # Tạo Barycentric Interpolator
    interpolator = BarycentricInterpolator(range(len(x_points)), x_points)
    x_vals = interpolator(np.linspace(0, len(x_points)-1, n_points))

    interpolator = BarycentricInterpolator(range(len(y_points)), y_points)
    y_vals = interpolator(np.linspace(0, len(y_points)-1, n_points))

    return list(zip(x_vals, y_vals))

# Hàm lấy đường viền của đối tượng (chọn contour lớn nhất và làm mượt đường viền)
def get_object_outline_cv(contours, epsilon=2.0):
    if len(contours) == 0:
        return None
    largest_contour = max(contours, key=cv2.contourArea)  # Chọn contour lớn nhất
    approx_curve = cv2.approxPolyDP(largest_contour, epsilon, True)

    return approx_curve

# Hàm xuất file EPS từ đường viền đối tượng
def export_to_eps(outline, output_eps):
    svg_path = "image/temp/temp.svg"

    if outline is None:
        print("Không có outline để xuất EPS.")
        return

    # Lấy kích thước bao quanh path
    x_min = min(p[0][0] for p in outline)
    y_min = min(p[0][1] for p in outline)
    x_max = max(p[0][0] for p in outline)
    y_max = max(p[0][1] for p in outline)

    width = x_max - x_min
    height = y_max - y_min

    # Tạo SVG với kích thước khớp với path
    dwg = svgwrite.Drawing(filename=svg_path, size=(f"{width}px", f"{height}px"), viewBox=f"{x_min} {y_min} {width} {height}")

    # Vẽ path lên SVG
    path_data = "M " + " ".join(f"{p[0][0]},{p[0][1]}" for p in outline) + " Z"
    dwg.add(dwg.path(d=path_data, fill="none", stroke="black"))

    dwg.save()  # Lưu SVG

    # Chuyển từ SVG sang EPS bằng Inkscape
    convert_svg_to_eps_with_inkscape(svg_path, output_eps)

def convert_svg_to_eps_with_inkscape(svg_path, eps_path):
    inkscape_path = r"C:\Program Files\Inkscape\bin\inkscape.exe"  # Đảm bảo đường dẫn chính xác tới Inkscape
    command = [
        inkscape_path,  # Đường dẫn đầy đủ
        svg_path,       # Đường dẫn file SVG đầu vào
        "--export-type=eps",  # Sử dụng tham số đúng cho phiên bản Inkscape mới
        "--export-filename", eps_path  # Đường dẫn file EPS đầu ra
    ]

    subprocess.run(command, check=True)

# Hàm chính để truyền vào file PNG và xuất file EPS
def process_image(input_png, output_eps):
    contours = detect_object(input_png)  # Phát hiện đối tượng
    outline = get_object_outline(contours, 'spline', 0.5, 5000)  # Lấy đường viền đối tượng
    export_to_eps(outline, output_eps)  # Xuất EPS


def smooth_with_kernel(contour, kernel_size=5):
    # Convert contour to float32 for filtering
    contour_float = contour.astype(np.float32)

    # Create the kernel for smoothing
    kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)

    # Apply the filter
    smoothed_contour = cv2.filter2D(contour_float, -1, kernel)

    # Convert back to original dtype
    smoothed_contour = smoothed_contour.astype(contour.dtype)

    return smoothed_contour

def approximate_bezier_curve(contour, num_points=100):
    n = len(contour)
    t_values = np.linspace(0, 1, num_points)
    bezier_curve = []

    for t in t_values:
        point = np.zeros(2)
        for i in range(n):
            binomial_coeff = math.comb(n - 1, i)
            point += binomial_coeff * ((1 - t) ** (n - 1 - i)) * (t ** i) * contour[i][0]
        bezier_curve.append(point)

    return np.array(bezier_curve, dtype=np.int32).reshape(-1, 1, 2)

def spline_interpolation(contour, num_points=100):
    x = contour[:, 0, 0]
    y = contour[:, 0, 1]
    tck, u = splprep([x, y], s=0)
    u_new = np.linspace(u.min(), u.max(), num_points)
    x_new, y_new = splev(u_new, tck, der=0)
    spline_curve = np.vstack((x_new, y_new)).T
    return spline_curve.reshape(-1, 1, 2).astype(np.int32)

def smooth_contour(contour, distance_threshold=50):
    # Calculate the number of points in the contour
    num_points = len(contour)

    # Create an array to store the smoothed contour
    smoothed_contour = np.copy(contour)

    # Iterate over the contour points
    for i in range(3, num_points - 3):
        prev_points = contour[i - 3:i]
        next_points = contour[i + 1:i + 4]

        # Calculate the average of the previous and next points
        avg_prev = np.mean(prev_points, axis=0)
        avg_next = np.mean(next_points, axis=0)

        # Calculate the difference between the average points
        diff = avg_next - avg_prev

        # Smooth the current point
        smoothed_contour[i] = contour[i] + diff * 0.5

    # Check the distance between consecutive points and draw a straight line if necessary
    for i in range(1, num_points):
        pt1 = smoothed_contour[i - 1][0]
        pt2 = smoothed_contour[i][0]
        distance = np.linalg.norm(pt2 - pt1)

        if distance > distance_threshold:
            smoothed_contour[i - 1] = pt1
            smoothed_contour[i] = pt2

    return smoothed_contour

def get_object_outline(contours, method='polyDP', epsilon=2.0, num_points=100):
    if len(contours) == 0:
        return None
    largest_contour = max(contours, key=cv2.contourArea)  # Chọn contour lớn nhất

    return largest_contour
    # largest_contour = cv2.approxPolyDP(largest_contour, epsilon, True)

    if method == 'polyDP':
        approx_curve = cv2.approxPolyDP(largest_contour, epsilon, True)
    elif method == 'bezier':
        approx_curve = approximate_bezier_curve(largest_contour, num_points)
    elif method == 'spline':
        approx_curve = spline_interpolation(largest_contour, num_points)
    elif method == 'kernel':
        approx_curve = smooth_with_kernel(largest_contour, num_points)
    elif method == 'smooth':
        approx_curve = smooth_contour(largest_contour, num_points)
    else:
        raise ValueError("Unknown method: {}".format(method))

    return approx_curve



# Gọi hàm chính
img_name = "outline"
process_image(f"image/{img_name}.png", f"image/export/{img_name}.eps")



