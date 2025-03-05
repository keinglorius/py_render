from PIL import Image

def convert_png_to_bmp(input_file, output_file):
    image = Image.open(input_file).convert("RGBA")
    background = Image.new("RGBA", image.size, (255, 255, 255))
    alpha_composite = Image.alpha_composite(background, image)
    alpha_composite.convert("RGB").save(output_file, "BMP")

def convert_bmp_to_eps(input_file, output_file):
    image = Image.open(input_file)
    image = image.convert('RGB')
    image.save(output_file, 'EPS')

def convert_bmp_to_black(input_file, output_file):
    image = Image.open(input_file).convert("RGB")
    black_image = Image.new("RGB", image.size, (0, 0, 0))
    black_image.paste(image, mask=image.split()[3])
    black_image.save(output_file, "BMP")



if __name__ == "__main__":
    input_png = 'img/sample.png'
    source_bmp = 'img/sample.bmp'
    convert_png_to_bmp(input_png, source_bmp)
    convert_bmp_to_eps(source_bmp, 'export/eps/sample.eps')

    print(f"Converted {input_png} to {source_bmp}")
