import glob
import os
from PIL import Image


def center_icon(file_path, output_size=(250, 250), margin=25):
    """Finds the drawing inside an image, strips away uneven white padding,

    and centers it on a square canvas.
    """
    img = Image.open(file_path).convert("RGBA")

    # Step 1: Convert to grayscale to find non-white pixels (the icon drawing)
    gray = img.convert("L")
    # Mark pixels darker than near-white (240) as the icon body
    bw = gray.point(lambda p: 255 if p < 240 else 0)

    # Step 2: Get the tight bounding box around the actual drawing
    bbox = bw.getbbox()
    if not bbox:
        return  # Skip if empty image

    icon_drawing = img.crop(bbox)

    # Step 3: Resize drawing proportionally to fit canvas with uniform padding
    max_w = output_size[0] - (margin * 2)
    max_h = output_size[1] - (margin * 2)

    w, h = icon_drawing.size
    scale = min(max_w / w, max_h / h)
    new_w, new_h = int(w * scale), int(h * scale)

    resized_drawing = icon_drawing.resize(
        (new_w, new_h), Image.Resampling.LANCZOS
    )

    # Step 4: Create a clean white square canvas and paste the drawing dead-center
    canvas = Image.new("RGBA", output_size, (255, 255, 255, 255))
    paste_x = (output_size[0] - new_w) // 2
    paste_y = (output_size[1] - new_h) // 2

    canvas.paste(resized_drawing, (paste_x, paste_y), mask=resized_drawing)

    # Save over the existing file in assets/
    canvas.save(file_path)
    print(f"Perfectly centered: {file_path}")


# Run on all PNG files inside the assets folder
asset_files = glob.glob("assets/*.png")

if not asset_files:
    print(
        "No images found in assets/ folder. Make sure your icons are inside assets/!"
    )
else:
    for file in asset_files:
        center_icon(file)
    print("\n All assets have been auto-centered!")