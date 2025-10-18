from PIL import Image, ImageDraw
import os

# Create a 64x64 image with transparency
size = 64
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw gradient circle background (simulate with solid color)
draw.ellipse([2, 2, 62, 62], fill=(16, 185, 129, 255))

# Draw three server racks
def draw_server(y):
    # Server body (white with transparency)
    draw.rounded_rectangle([16, y, 48, y+10], radius=2, fill=(255, 255, 255, 230))
    
    # Status lights (green and teal)
    draw.ellipse([19, y+3, 23, y+7], fill=(16, 185, 129, 255))
    draw.ellipse([24, y+3, 28, y+7], fill=(20, 184, 166, 255))
    
    # Status bars
    draw.rectangle([30, y+3, 44, y+4], fill=(16, 185, 129, 150))
    draw.rectangle([30, y+6, 40, y+7], fill=(20, 184, 166, 150))

draw_server(14)
draw_server(27)
draw_server(40)

# Save as PNG
img.save('favicon.png')
print("Favicon created successfully!")

# Also create 32x32 version
img_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
img_32.save('favicon-32x32.png')

# Create 16x16 version
img_16 = img.resize((16, 16), Image.Resampling.LANCZOS)
img_16.save('favicon-16x16.png')

print("All favicon sizes created!")
