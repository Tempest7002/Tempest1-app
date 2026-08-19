import os
from PIL import Image

# Create assets folder if it doesn't exist
os.makedirs("assets", exist_ok=True)

image_path = "Muscles.jpg"

try:
    img = Image.open(image_path)
    w, h = img.size

    # Calculate cell dimensions
    cell_w = w / 4
    cell_h = h / 4

    # Size of the square crop (80% of cell size to leave nice margins around icons)
    box_size = min(cell_w, cell_h) * 0.82


    def crop_cell_center(row, col):
        """Crops a clean square around the center of any grid cell."""
        center_x = (col + 0.5) * cell_w
        center_y = (row + 0.5) * cell_h

        left = center_x - (box_size / 2)
        top = center_y - (box_size / 2)
        right = center_x + (box_size / 2)
        bottom = center_y + (box_size / 2)

        return (left, top, right, bottom)


    # Grid position mapping (row 0-3, col 0-3)
    muscle_grid = {
        "chest": (3, 0),  # Bottom-Left
        "back": (0, 3),  # Top-Right
        "shoulders": (0, 2),  # Top Row, 3rd
        "arms": (3, 2),  # Bottom Row, 3rd
        "legs": (1, 2),  # 2nd Row, 3rd
        "core": (0, 0),  # Top-Left
    }

    for muscle, (row, col) in muscle_grid.items():
        box = crop_cell_center(row, col)
        cropped_img = img.crop(box)

        # Save as a clean standard square image
        cropped_img.save(f"assets/{muscle}.png")
        print(f"Cleanly cropped & saved assets/{muscle}.png")

    print("\n Success! All icons cropped cleanly without distortion.")

except FileNotFoundError:
    print(f"Error: Couldn't find '{image_path}' in your project folder.")