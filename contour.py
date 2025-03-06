import subprocess

def png_to_eps(input_png, output_eps):
    command = [
        "C:\\Program Files\\Inkscape\\bin\\inkscape.exe",
        input_png,
        "--actions=SelectAll;TraceBitmap;export-filename:" + output_eps + ";export-overwrite",
        "--export-type=eps"
    ]
    subprocess.run(command)

if __name__ == "__main__":
    input_png = 'D:\\images\\black.png'
    output_eps = 'D:\\images\\black.eps'
    png_to_eps(input_png, output_eps)
    print(f"Converted {input_png} to {output_eps}")
