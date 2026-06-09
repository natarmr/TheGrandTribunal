import os

from PIL import Image

SPRITE_SUFFIXES = ("talking", "listening", "thinking", "damage", "victory")
SPRITE_SOURCE_MAP = {
    "oscar_wilde.png": "wilde",
    "nietzsche.png": "nietzsche",
    "schopenhauer.png": "schopenhauer",
    "socrates.png": "plato",
}


def trim_image(img):
    rgba = img.convert("RGBA")
    datas = rgba.getdata()

    width, height = rgba.size
    min_x, min_y = width, height
    max_x, max_y = -1, -1

    for y in range(height):
        for x in range(width):
            r, g, b, a = datas[y * width + x]
            is_transparent = a == 0
            is_white = r == 255 and g == 255 and b == 255 and a == 255

            if not is_transparent and not is_white:
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

    if min_x > max_x or min_y > max_y:
        return img, (0, 0, width, height)

    crop_box = (min_x, min_y, max_x + 1, max_y + 1)
    return img.crop(crop_box), crop_box


def split_sprite_sheet(image_path, num_sprites, out_dir, prefix):
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    os.makedirs(out_dir, exist_ok=True)

    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return

    width, height = img.size
    segment_width = width // num_sprites

    print(f"\nProcessing: {image_path} (Prefix: {prefix})")
    print("-" * 50)

    for i in range(num_sprites):
        left = i * segment_width
        right = (i + 1) * segment_width
        segment = img.crop((left, 0, right, height))

        trimmed_segment, trim_box = trim_image(segment)

        abs_left = left + trim_box[0]
        abs_upper = trim_box[1]
        abs_right = left + trim_box[2]
        abs_lower = trim_box[3]

        out_name = f"{prefix}_{SPRITE_SUFFIXES[i]}.png"
        out_path = os.path.join(out_dir, out_name)

        trimmed_segment.save(out_path, "PNG")

        print(f"[{SPRITE_SUFFIXES[i]:<10}] Segment Box: ({left}, 0, {right}, {height})")
        print(
            f"             Final Crop relative to original: ({abs_left}, {abs_upper}, {abs_right}, {abs_lower})"
        )
        print(f"             Saved as {out_name}")


if __name__ == "__main__":
    out_dir = "sprites"

    for img_file, prefix in SPRITE_SOURCE_MAP.items():
        split_sprite_sheet(img_file, 5, out_dir, prefix)
