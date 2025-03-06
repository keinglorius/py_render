import subprocess

def png_to_eps(input_png, output_eps):
    command = [
        "autotrace",
        "--output-format", "eps",  # Xuất EPS
        "--centerline",            # Dò đường trung tâm (chỉ bắt nét chính)
        "--color-count", "2",      # Giảm màu (hữu ích nếu có nhiều màu)
        "--output-file", output_eps,
        input_png
    ]
    subprocess.run(command)


if __name__ == "__main__":
    # input_png = 'images/black.png'
    # output_bmp = 'images/export/eps/black.eps'
    # png_to_eps_vector(input_png, output_bmp)
    # print(f"Converted {input_png} to {output_bmp}")

    input_png = f'images/origin.png'
    output_bmp = f'images/export/eps/origin.eps'
    png_to_eps(input_png, output_bmp)
    print(f"Converted {input_png} to {output_bmp}")

    # input_png = f'images/outline.png'
    # output_bmp = f'images/export/eps/outline.eps'
    # png_to_eps_outline(input_png, output_bmp)
    # print(f"Converted {input_png} to {output_bmp}")