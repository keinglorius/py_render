from PIL import Image, ImageFilter
import svgwrite

def create_vector_outline(image_path, output_path):
    # Open the image
    image = Image.open(image_path).convert("L")  # Convert to grayscale
    image = image.filter(ImageFilter.FIND_EDGES)  # Find edges

    # Create a new SVG drawing
    dwg = svgwrite.Drawing(output_path, profile='tiny')

    # Get image dimensions
    width, height = image.size

    # Add image dimensions to SVG
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill='white'))

    # Convert image to SVG path
    for y in range(height):
        for x in range(width):
            pixel = image.getpixel((x, y))
            if pixel < 128:  # Threshold value to determine edge
                dwg.add(dwg.circle(center=(x, y), r=0.5, fill='black'))

    # Save the SVG file
    dwg.save()

if __name__ == "__main__":
    # Paths to the input image and output SVG file
    input_image_path = 'img/CMYK_sample.png'
    output_svg_path = 'img/CMYK_sample_outline.svg'

    # Create the vector outline
    create_vector_outline(input_image_path, output_svg_path)
    print(f"Vector outline saved to {output_svg_path}")