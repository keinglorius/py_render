import cv2
import numpy as np
from PIL import Image, ImageFilter
import svgwrite
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPS

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os



def convert_png_to_svg(image_path, output_path):
    # Load ảnh PNG
    image = Image.open(image_path).convert("RGBA")
    img_array = np.array(image)

    # Lấy kích thước ảnh
    height, width = img_array.shape[:2]

    # Tạo file SVG
    dwg = svgwrite.Drawing(output_path, profile='tiny', size=(width, height))

    # Duyệt qua từng pixel để vẽ lên SVG
    for y in range(height):
        for x in range(width):
            r, g, b, a = img_array[y, x]  # Lấy màu và độ trong suốt
            if a > 0:  # Bỏ qua pixel trong suốt
                color = f"rgb({r},{g},{b})"
                opacity = a / 255  # Chuyển độ trong suốt về dạng 0-1
                dwg.add(dwg.rect(insert=(x, y), size=(1, 1), fill=color, fill_opacity=opacity, stroke="none"))

    # Lưu file SVG
    dwg.save()
    print(f"SVG with full color and transparency saved to {output_path}")

def convert_svg_to_ai(svg_path, ai_path):
    # Convert SVG to PDF
    drawing = svg2rlg(svg_path)
    pdf_path = svg_path.replace('.svg', '.pdf')

    # Create a PDF with a layer
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setTitle("Vector Layer")
    renderPDF.draw(drawing, c, 0, 0)
    c.showPage()
    c.save()

    # Remove the AI file if it already exists
    if os.path.exists(ai_path):
        os.remove(ai_path)

    # Rename the PDF to AI
    os.rename(pdf_path, ai_path)
    print(f"AI file saved to {ai_path}")

def convert_svg_to_eps(svg_path, eps_path):
    # Convert SVG to EPS
    drawing = svg2rlg(svg_path)
    with open(eps_path, 'wb') as eps_file:
        renderPS.drawToFile(drawing, eps_file)
    print(f"EPS file saved to {eps_path}")


def merge_svgs_to_layers(base_svg_path, layer1_path, layer2_path, output_path):
    # Load base SVG
    base_drawing = svg2rlg(base_svg_path)

    # Load layer 1
    layer1_drawing = svg2rlg(layer1_path)

    # Load layer 2
    layer2_drawing = svg2rlg(layer2_path)

    # Create a new PDF canvas for the merged output
    pdf_path = output_path.replace('.ai', '.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)

    # Draw base SVG
    renderPDF.draw(base_drawing, c, 0, 0)

    # Draw layer 1
    renderPDF.draw(layer1_drawing, c, 0, 0)

    # Draw layer 2
    renderPDF.draw(layer2_drawing, c, 0, 0)

    # Save the merged PDF
    c.showPage()
    c.save()

    # Remove the AI file if it already exists
    if os.path.exists(output_path):
        os.remove(output_path)

    # Rename the PDF to AI
    os.rename(pdf_path, output_path)
    print(f"Merged AI file saved to {output_path}")


def create_smooth_black_filled_vector(image_path, output_path, blur_size=7, threshold_blocksize=15, threshold_c=5, epsilon_factor=0.002):
    # Load ảnh PNG và chuyển sang RGBA
    image = Image.open(image_path).convert("RGBA")
    img_array = np.array(image)

    # Lấy kênh Alpha (xác định vùng trong suốt)
    alpha_channel = img_array[:, :, 3]

    # Tạo mask vùng có màu (alpha > 0)
    mask = alpha_channel > 0

    # Chuyển ảnh thành grayscale
    gray_image = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2GRAY)

    # Làm mờ ảnh để loại bỏ noise nhỏ
    blurred = cv2.GaussianBlur(gray_image, (blur_size, blur_size), 0)

    # Dùng Adaptive Threshold để giữ ranh giới mềm mại
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, threshold_blocksize, threshold_c)

    # Đảo ngược màu (vùng có màu thành đen, vùng trong suốt thành trắng)
    binary[mask] = 0
    binary[~mask] = 255

    # Tìm đường viền mềm mại
    contours, _ = cv2.findContours(255 - binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Làm mịn contour bằng thuật toán Douglas-Peucker
    smoothed_contours = []
    for contour in contours:
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        smoothed_contour = cv2.approxPolyDP(contour, epsilon, True)
        smoothed_contours.append(smoothed_contour)

    # Lấy kích thước ảnh
    height, width = alpha_channel.shape

    # Tạo file SVG
    dwg = svgwrite.Drawing(output_path, profile='tiny', size=(width, height))

    # Vẽ vùng đen lên SVG
    for contour in smoothed_contours:
        points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
        if len(points) > 1:
            path_data = "M " + " L ".join(f"{x},{y}" for x, y in points) + " Z"
            dwg.add(dwg.path(d=path_data, fill="black", stroke="none", stroke_width="0.5"))

    # Lưu file SVG
    dwg.save()
    print(f"Vector saved to {output_path}")


def create_outline_vector(image_path, output_path, blur_size=7, threshold_blocksize=15, threshold_c=5, epsilon_factor=0.002):
    # Load ảnh PNG và chuyển sang RGBA
    image = Image.open(image_path).convert("RGBA")
    img_array = np.array(image)

    # Lấy kênh Alpha (xác định vùng trong suốt)
    alpha_channel = img_array[:, :, 3]

    # Tạo mask vùng có màu (alpha > 0)
    mask = alpha_channel > 0

    # Chuyển ảnh thành grayscale
    gray_image = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2GRAY)

    # Làm mờ ảnh để loại bỏ noise nhỏ
    blurred = cv2.GaussianBlur(gray_image, (blur_size, blur_size), 0)

    # Dùng Adaptive Threshold để giữ ranh giới mềm mại
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, threshold_blocksize, threshold_c)

    # Đảo ngược màu (vùng có màu thành đen, vùng trong suốt thành trắng)
    binary[mask] = 0
    binary[~mask] = 255

    # Tìm đường viền mềm mại
    contours, _ = cv2.findContours(255 - binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Làm mịn contour bằng thuật toán Douglas-Peucker
    smoothed_contours = []
    for contour in contours:
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        smoothed_contour = cv2.approxPolyDP(contour, epsilon, True)
        smoothed_contours.append(smoothed_contour)

    # Lấy kích thước ảnh
    height, width = alpha_channel.shape

    # Tạo file SVG
    dwg = svgwrite.Drawing(output_path, profile='tiny', size=(width, height))

    # Vẽ outline lên SVG
    for contour in smoothed_contours:
        points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
        if len(points) > 1:
            path_data = "M " + " L ".join(f"{x},{y}" for x, y in points) + " Z"
            dwg.add(dwg.path(d=path_data, fill="none", stroke="black", stroke_width="1"))

    # Lưu file SVG
    dwg.save()
    print(f"Outline vector saved to {output_path}")


def create_outer_outline(image_path, output_path, outline_color="black", outline_size=50, blur_radius=5):
    # Load ảnh PNG (đọc kênh alpha để tìm đối tượng)
    image = Image.open(image_path).convert("RGBA")
    img_array = np.array(image)

    # Lấy kênh Alpha xác định vùng có đối tượng
    alpha_channel = img_array[:, :, 3]

    # Tạo mask nhị phân (1 = vùng có đối tượng, 0 = vùng trong suốt)
    mask = alpha_channel > 0
    binary_mask = np.uint8(mask * 255)  # Chuyển thành ảnh nhị phân trắng đen

    # Mở rộng contour bằng Morphological Dilation (tạo outline cách đều)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (outline_size, outline_size))
    dilated = cv2.dilate(binary_mask, kernel, iterations=1)

    # Làm mượt bằng GaussianBlur để tạo viền tròn hơn
    blurred = cv2.GaussianBlur(dilated, (blur_radius, blur_radius), 0)

    # Tìm contour từ mask mở rộng
    contours, _ = cv2.findContours(blurred, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Xuất ra SVG hoặc PNG
    height, width = alpha_channel.shape

    # Tạo file SVG
    dwg = svgwrite.Drawing(output_path, profile='tiny', size=(width, height))
    for contour in contours:
        points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
        if len(points) > 1:
            path_data = "M " + " L ".join(f"{x},{y}" for x, y in points) + " Z"
            dwg.add(dwg.path(d=path_data, fill="none", stroke=outline_color, stroke_width="2"))
    dwg.save()
    print(f"Outer outline saved to {output_path}")



if __name__ == "__main__":
    input_image_path = 'img/sample.png'

    output_sample = 'export/svg/sample.svg'
    output_black = 'export/svg/sample_black.svg'
    # output_outline = 'export/svg/sample_outline.svg'
    output_outline_radius = 'export/svg/sample_outline_radius.svg'


    # Example usage
    convert_png_to_svg(input_image_path, output_sample)
    create_smooth_black_filled_vector(input_image_path, output_black, 3, 11, 35, 0.0002)
    # create_outline_vector(input_image_path, output_outline, 3, 11, 35, 0.0002)
    create_outer_outline(input_image_path, output_outline_radius, "black", 30, 111)


    convert_svg_to_eps(output_black, 'export/eps/sample_black.eps')
    # convert_svg_to_eps(output_outline, 'export/eps/sample_outline.eps')
    convert_svg_to_eps(output_outline_radius, 'export/eps/sample_outline_radius.eps')


    output_merged_svg = 'export/merged_output.ai'

    # Merge the SVGs into layers
    merge_svgs_to_layers(output_sample, output_black, output_outline_radius, output_merged_svg)
