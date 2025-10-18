from PIL import Image, ImageDraw

def create_favicon(size, filename):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Scale factors
    scale = size / 64
    
    # Draw gradient circle background
    padding = int(2 * scale)
    draw.ellipse([padding, padding, size-padding, size-padding], fill=(16, 185, 129, 255))
    
    # Draw three server racks
    def draw_server(y):
        y = int(y * scale)
        server_width = int(32 * scale)
        server_height = int(10 * scale)
        x_start = int(16 * scale)
        radius = max(2, int(2 * scale))
        
        # Server body
        draw.rounded_rectangle([x_start, y, x_start + server_width, y + server_height], 
                              radius=radius, fill=(255, 255, 255, 230))
        
        # Status lights
        light_y = y + int(5 * scale)
        light_radius = max(1, int(2 * scale))
        
        draw.ellipse([int(21*scale) - light_radius, light_y - light_radius,
                     int(21*scale) + light_radius, light_y + light_radius], 
                     fill=(16, 185, 129, 255))
        draw.ellipse([int(26*scale) - light_radius, light_y - light_radius,
                     int(26*scale) + light_radius, light_y + light_radius], 
                     fill=(20, 184, 166, 255))
        
        # Status bars
        bar_height = max(1, int(1 * scale))
        draw.rectangle([int(30*scale), y + int(3.5*scale), 
                       int(44*scale), y + int(3.5*scale) + bar_height], 
                      fill=(16, 185, 129, 150))
        draw.rectangle([int(30*scale), y + int(6*scale), 
                       int(40*scale), y + int(6*scale) + bar_height], 
                      fill=(20, 184, 166, 150))
    
    draw_server(14)
    draw_server(27)
    draw_server(40)
    
    img.save(filename)
    print(f"Created {filename}")

# Create different sizes
create_favicon(192, 'logo192.png')
create_favicon(512, 'logo512.png')

print("All PWA icons created successfully!")
