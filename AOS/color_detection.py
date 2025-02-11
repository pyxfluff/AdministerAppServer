from PIL import Image

def get_color(path):
    r, g, b, total_pixels = 0, 0, 0, 0
    pixels = list(Image.open(path).getdata())

    for pixel in pixels:
        if pixel == (0, 0, 0, 0):
            continue

        r += pixel[0]
        g += pixel[1]
        b += pixel[2]
        total_pixels += 1

    print(total_pixels, r, g, b)
    return r / total_pixels, g / total_pixels, b / total_pixels
