import base64

def decode_ascii85(data):
    # Add the necessary delimiters for base64.a85decode
    data = data.replace("<~", "").replace("~>", "")
    return base64.a85decode(data)

def test_read_eps(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    ascii85_data = ""
    for i, line in enumerate(lines):
        print(f"{i}: {line.strip()}")
        if i >= 8:  # Assuming the encoded data starts from line 8
            # Filter out non-Ascii85 characters
            filtered_line = ''.join(c for c in line.strip() if c in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~')
            ascii85_data += filtered_line

    decoded_data = decode_ascii85(ascii85_data)
    print("\nDecoded Data:")
    print(decoded_data)

# Test the function with the specified EPS file
test_read_eps("image/export/outline_processed.eps")