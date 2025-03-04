import cv2
import numpy as np
from PIL import Image, ImageFilter
import svgwrite

def create_vector_outline(image_path, output_path, epsilon_factor=0.002):
    # Load image and convert to grayscale
    image = Image.open(image_path).convert("L")
    image = image.filter(ImageFilter.FIND_EDGES)

    # Convert PIL image to numpy array
    img_array = np.array(image)

    # Apply Gaussian blur to smooth edges
    img_array = cv2.GaussianBlur(img_array, (5, 5), 0)

    # Detect edges using Canny
    edges = cv2.Canny(img_array, 50, 150)

    # Find contours with full resolution
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Get image dimensions
    width, height = image.size

    # Create SVG file
    dwg = svgwrite.Drawing(output_path, profile='tiny')

    for contour in contours:
        # Simplify contour using Douglas-Peucker
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        smooth_contour = cv2.approxPolyDP(contour, epsilon, True)

        # Convert points to SVG path format
        points = [(int(pt[0][0]), int(pt[0][1])) for pt in smooth_contour]
        if len(points) > 1:
            path_data = "M " + " L ".join(f"{x},{y}" for x, y in points) + " Z"
            dwg.add(dwg.path(d=path_data, fill="none", stroke="black", stroke_width="1"))

    # Save SVG file
    dwg.save()
    print(f"Vector outline saved to {output_path}")

if __name__ == "__main__":
    input_image_path = 'img/outlineImg.png'
    output_svg_path = 'img/outlineImg_outline.svg'

    create_vector_outline(input_image_path, output_svg_path,0.00001)
