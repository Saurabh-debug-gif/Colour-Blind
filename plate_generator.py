from PIL import Image, ImageDraw, ImageFont

def generate_plate(number, bg_color, text_color, save_path):
    size = 300
    img = Image.new("RGB", (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 120)
    except IOError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), number, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (size - w) // 2
    y = (size - h) // 2

    draw.text((x, y), number, fill=text_color, font=font)
    img.save(save_path)