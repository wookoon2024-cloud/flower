"""
Asset generator for AI Plant Widget
Creates high quality PNG graphics for 5 plant species (classic, sunflower, cactus, clover, cherry)
across 6 growth stages (1-6), reaction icons, and app icons.
"""
import os
import math
from PIL import Image, ImageDraw

def draw_pot(draw: ImageDraw.ImageDraw, face_type: int = 1):
    # Pot body (Flush with bottom at Y=198)
    draw.polygon([(50, 143), (150, 143), (135, 198), (65, 198)], fill="#D27D46", outline="#9C4A1E", width=3)
    draw.rounded_rectangle([(42, 133), (158, 145)], radius=5, fill="#E68A4E", outline="#9C4A1E", width=3)
    # Soil
    draw.ellipse([(55, 138), (145, 148)], fill="#5C3A21")
    # Cute Face
    draw.ellipse([(85, 158), (93, 166)], fill="#3E2723")
    draw.ellipse([(107, 158), (115, 166)], fill="#3E2723")
    if face_type == 1:
        draw.arc([(94, 163), (106, 173)], start=0, end=180, fill="#3E2723", width=2)
    elif face_type == 2:
        draw.arc([(92, 159), (108, 175)], start=0, end=180, fill="#D81B60", width=3)
    else:
        # Super happy face
        draw.arc([(90, 157), (110, 177)], start=0, end=180, fill="#E91E63", width=3)
        draw.polygon([(97, 167), (103, 167), (100, 172)], fill="#FF4081")
    # Cheeks
    draw.ellipse([(76, 163), (84, 169)], fill="#FF8A80")
    draw.ellipse([(116, 163), (124, 169)], fill="#FF8A80")

def create_assets(output_dir="assets"):
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Classic Species (🌸 기본 다정한 화분, 1~6단계)
    for stg in range(1, 7):
        img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        draw_pot(d, 3 if stg >= 5 else (2 if stg >= 3 else 1))
        
        if stg == 1:
            # Seedling sprout
            d.arc([(92, 90), (115, 135)], start=180, end=300, fill="#4CAF50", width=4)
            d.ellipse([(80, 85), (102, 105)], fill="#81C784", outline="#2E7D32", width=2)
        elif stg == 2:
            # Two healthy sprout leaves
            d.arc([(90, 80), (120, 135)], start=180, end=300, fill="#4CAF50", width=5)
            d.pieslice([(75, 75), (105, 105)], start=180, end=300, fill="#81C784", outline="#2E7D32", width=2)
            d.pieslice([(95, 70), (125, 100)], start=240, end=360, fill="#A5D6A7", outline="#2E7D32", width=2)
        elif stg == 3:
            # Multi-leaf growing shoot
            d.line([(100, 130), (100, 70)], fill="#388E3C", width=6)
            d.pieslice([(55, 80), (100, 115)], start=160, end=320, fill="#66BB6A", outline="#2E7D32", width=2)
            d.pieslice([(100, 65), (145, 100)], start=220, end=380, fill="#81C784", outline="#2E7D32", width=2)
            d.pieslice([(65, 55), (100, 85)], start=140, end=290, fill="#A5D6A7", outline="#2E7D32", width=2)
        elif stg == 4:
            # First delicate flower bud
            d.line([(100, 130), (100, 60)], fill="#2E7D32", width=6)
            d.pieslice([(50, 70), (100, 110)], start=160, end=320, fill="#4CAF50", outline="#1B5E20", width=2)
            d.pieslice([(100, 70), (150, 110)], start=220, end=380, fill="#66BB6A", outline="#1B5E20", width=2)
            d.ellipse([(86, 36), (114, 64)], fill="#F48FB1", outline="#C2185B", width=2)
            d.ellipse([(92, 42), (108, 58)], fill="#F06292")
        elif stg == 5:
            # Blooming flower
            d.line([(100, 130), (100, 55)], fill="#2E7D32", width=7)
            d.pieslice([(50, 75), (98, 115)], start=160, end=320, fill="#4CAF50", outline="#1B5E20", width=2)
            d.pieslice([(102, 75), (150, 115)], start=220, end=380, fill="#66BB6A", outline="#1B5E20", width=2)
            for p in [(75, 20, 105, 50), (95, 20, 125, 50), (65, 40, 95, 70), (105, 40, 135, 70), (75, 55, 105, 85), (95, 55, 125, 85)]:
                d.ellipse(p, fill="#FF80AB", outline="#C2185B", width=2)
            d.ellipse([(85, 38), (115, 68)], fill="#FFEE58", outline="#F57F17", width=2)
        elif stg == 6:
            # Legendary Full Bloom with sparkling aura & golden crown flower
            d.line([(100, 130), (100, 50)], fill="#1B5E20", width=8)
            d.pieslice([(40, 70), (98, 115)], start=160, end=320, fill="#388E3C", outline="#1B5E20", width=2)
            d.pieslice([(102, 70), (160, 115)], start=220, end=380, fill="#4CAF50", outline="#1B5E20", width=2)
            for ang in range(0, 360, 40):
                rad = math.radians(ang)
                px = 100 + int(32 * math.cos(rad))
                py = 42 + int(32 * math.sin(rad))
                d.ellipse([(px-12, py-12), (px+12, py+12)], fill="#FF4081", outline="#C2185B", width=2)
            d.ellipse([(80, 22), (120, 62)], fill="#FFEB3B", outline="#F57F17", width=3)
            # Golden sparkles around
            for sx, sy in [(45, 30), (155, 28), (35, 65), (165, 65)]:
                d.polygon([(sx, sy-6), (sx+4, sy), (sx+10, sy+1), (sx+5, sy+5), (sx+6, sy+11), (sx, sy+7), (sx-6, sy+11), (sx-5, sy+5), (sx-10, sy+1), (sx-4, sy)], fill="#FFD700")

        img.save(os.path.join(output_dir, f"stage_{stg}.png"))
        img.save(os.path.join(output_dir, f"stage_classic_{stg}.png"))

    # 2. Sunflower (🌻 해바라기, 1~6단계)
    for stg in range(1, 7):
        img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        draw_pot(d, 3 if stg >= 5 else (2 if stg >= 3 else 1))
        if stg == 1:
            d.arc([(90, 90), (110, 135)], start=180, end=320, fill="#4CAF50", width=4)
            d.ellipse([(75, 82), (95, 102)], fill="#FFD54F", outline="#F57F17", width=2)
        elif stg == 2:
            d.arc([(90, 85), (110, 135)], start=180, end=320, fill="#4CAF50", width=5)
            d.ellipse([(70, 75), (95, 95)], fill="#FFD54F", outline="#F57F17", width=2)
            d.ellipse([(105, 75), (130, 95)], fill="#FFD54F", outline="#F57F17", width=2)
        elif stg == 3:
            d.line([(100, 130), (100, 65)], fill="#2E7D32", width=7)
            d.pieslice([(50, 75), (98, 115)], start=160, end=320, fill="#4CAF50", outline="#1B5E20", width=2)
            d.pieslice([(102, 75), (150, 115)], start=220, end=380, fill="#66BB6A", outline="#1B5E20", width=2)
        elif stg == 4:
            d.line([(100, 130), (100, 55)], fill="#2E7D32", width=7)
            d.pieslice([(45, 70), (98, 115)], start=160, end=320, fill="#4CAF50", outline="#1B5E20", width=2)
            d.pieslice([(102, 70), (155, 115)], start=220, end=380, fill="#66BB6A", outline="#1B5E20", width=2)
            d.ellipse([(82, 28), (118, 64)], fill="#8D6E63", outline="#5D4037", width=2)
            for ang in range(0, 360, 60):
                rad = math.radians(ang)
                px = 100 + int(20 * math.cos(rad))
                py = 46 + int(20 * math.sin(rad))
                d.ellipse([(px-6, py-6), (px+6, py+6)], fill="#FFCA28", outline="#FFA000")
        elif stg == 5:
            d.line([(100, 130), (100, 55)], fill="#2E7D32", width=8)
            d.pieslice([(40, 75), (98, 120)], start=160, end=320, fill="#388E3C", outline="#1B5E20", width=2)
            d.pieslice([(102, 75), (160, 120)], start=220, end=380, fill="#4CAF50", outline="#1B5E20", width=2)
            for ang in range(0, 360, 30):
                rad = math.radians(ang)
                px = 100 + int(30 * math.cos(rad))
                py = 45 + int(30 * math.sin(rad))
                d.ellipse([(px-9, py-9), (px+9, py+9)], fill="#FFCA28", outline="#F57C00", width=1)
            d.ellipse([(76, 21), (124, 69)], fill="#5D4037", outline="#3E2723", width=2)
        elif stg == 6:
            # Huge smiling golden sunflower with sparkling crown
            d.line([(100, 130), (100, 48)], fill="#1B5E20", width=9)
            d.pieslice([(35, 70), (98, 120)], start=160, end=320, fill="#2E7D32", outline="#1B5E20", width=2)
            d.pieslice([(102, 70), (165, 120)], start=220, end=380, fill="#388E3C", outline="#1B5E20", width=2)
            for ang in range(0, 360, 24):
                rad = math.radians(ang)
                px = 100 + int(36 * math.cos(rad))
                py = 42 + int(36 * math.sin(rad))
                d.ellipse([(px-10, py-10), (px+10, py+10)], fill="#FFD600", outline="#FF6F00", width=1)
            d.ellipse([(72, 14), (128, 70)], fill="#4E342E", outline="#3E2723", width=3)
            # Sunflower cute face
            d.ellipse([(88, 34), (94, 42)], fill="#FFF")
            d.ellipse([(106, 34), (112, 42)], fill="#FFF")
            d.arc([(93, 40), (107, 52)], start=0, end=180, fill="#FFD600", width=2)
            for sx, sy in [(40, 25), (160, 25), (100, 0)]:
                d.polygon([(sx, sy-5), (sx+3, sy), (sx+8, sy+1), (sx+4, sy+4), (sx+5, sy+9), (sx, sy+6), (sx-5, sy+9), (sx-4, sy+4), (sx-8, sy+1), (sx-3, sy)], fill="#FFD700")

        img.save(os.path.join(output_dir, f"stage_sunflower_{stg}.png"))

    # 3. Cactus (🌵 선인장, 1~6단계)
    for stg in range(1, 7):
        img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        draw_pot(d, 3 if stg >= 5 else (2 if stg >= 3 else 1))
        if stg == 1:
            d.rounded_rectangle([(90, 105), (110, 130)], radius=8, fill="#66BB6A", outline="#2E7D32", width=2)
        elif stg == 2:
            d.rounded_rectangle([(85, 95), (115, 130)], radius=12, fill="#4CAF50", outline="#2E7D32", width=2)
        elif stg == 3:
            d.rounded_rectangle([(80, 70), (120, 130)], radius=16, fill="#4CAF50", outline="#2E7D32", width=2)
            d.line([(88, 80), (88, 120)], fill="#81C784", width=2)
            d.line([(112, 80), (112, 120)], fill="#81C784", width=2)
        elif stg == 4:
            d.rounded_rectangle([(75, 55), (125, 130)], radius=18, fill="#43A047", outline="#1B5E20", width=2)
            d.rounded_rectangle([(55, 75), (80, 100)], radius=10, fill="#43A047", outline="#1B5E20", width=2)
            d.rounded_rectangle([(120, 68), (145, 93)], radius=10, fill="#43A047", outline="#1B5E20", width=2)
            d.ellipse([(92, 44), (108, 58)], fill="#F44336", outline="#B71C1C", width=2)
        elif stg == 5:
            d.rounded_rectangle([(72, 45), (128, 130)], radius=20, fill="#388E3C", outline="#1B5E20", width=3)
            d.rounded_rectangle([(45, 65), (76, 95)], radius=12, fill="#388E3C", outline="#1B5E20", width=2)
            d.rounded_rectangle([(124, 58), (155, 88)], radius=12, fill="#388E3C", outline="#1B5E20", width=2)
            for fx, fy in [(100, 35), (55, 55), (145, 50)]:
                d.ellipse([(fx-12, fy-12), (fx+12, fy+12)], fill="#FFEB3B", outline="#F57F17", width=2)
                d.ellipse([(fx-5, fy-5), (fx+5, fy+5)], fill="#FF5722")
        elif stg == 6:
            # Giant cactus with multiple flowering branches and majestic crown
            d.rounded_rectangle([(70, 38), (130, 130)], radius=22, fill="#2E7D32", outline="#1B5E20", width=3)
            d.rounded_rectangle([(40, 55), (75, 90)], radius=14, fill="#2E7D32", outline="#1B5E20", width=2)
            d.rounded_rectangle([(125, 48), (160, 83)], radius=14, fill="#2E7D32", outline="#1B5E20", width=2)
            d.rounded_rectangle([(45, 90), (70, 115)], radius=10, fill="#2E7D32", outline="#1B5E20", width=2)
            d.rounded_rectangle([(130, 85), (155, 110)], radius=10, fill="#2E7D32", outline="#1B5E20", width=2)
            # Golden and pink blossoms
            for fx, fy, col in [(100, 24, "#FFD700"), (50, 45, "#FF4081"), (150, 38, "#FF4081"), (100, 50, "#FFEB3B")]:
                d.ellipse([(fx-14, fy-14), (fx+14, fy+14)], fill=col, outline="#E65100", width=2)
                d.ellipse([(fx-6, fy-6), (fx+6, fy+6)], fill="#D50000")

        img.save(os.path.join(output_dir, f"stage_cactus_{stg}.png"))

    # 4. Clover (🍀 행운의 클로버, 1~6단계)
    for stg in range(1, 7):
        img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        draw_pot(d, 3 if stg >= 5 else (2 if stg >= 3 else 1))
        if stg == 1:
            d.line([(100, 130), (100, 105)], fill="#4CAF50", width=3)
            d.ellipse([(92, 95), (108, 108)], fill="#81C784", outline="#2E7D32", width=2)
        elif stg == 2:
            d.line([(100, 130), (100, 95)], fill="#4CAF50", width=4)
            d.ellipse([(85, 80), (102, 98)], fill="#66BB6A", outline="#2E7D32", width=2)
            d.ellipse([(98, 80), (115, 98)], fill="#66BB6A", outline="#2E7D32", width=2)
        elif stg == 3:
            d.line([(100, 130), (100, 75)], fill="#388E3C", width=5)
            d.ellipse([(80, 60), (100, 80)], fill="#4CAF50", outline="#1B5E20", width=2)
            d.ellipse([(100, 60), (120, 80)], fill="#4CAF50", outline="#1B5E20", width=2)
            d.ellipse([(90, 45), (110, 65)], fill="#66BB6A", outline="#1B5E20", width=2)
        elif stg == 4:
            d.line([(100, 130), (100, 65)], fill="#2E7D32", width=6)
            d.line([(100, 110), (75, 80)], fill="#2E7D32", width=4)
            d.line([(100, 105), (125, 78)], fill="#2E7D32", width=4)
            for cx, cy in [(100, 50), (70, 75), (130, 72)]:
                for ox, oy in [(-8, 0), (8, 0), (0, -8)]:
                    d.ellipse([(cx+ox-9, cy+oy-9), (cx+ox+9, cy+oy+9)], fill="#43A047", outline="#1B5E20", width=2)
        elif stg == 5:
            d.line([(100, 130), (100, 60)], fill="#1B5E20", width=6)
            cx, cy = 100, 48
            for ox, oy in [(-16, 0), (16, 0), (0, -16), (0, 16)]:
                d.ellipse([(cx+ox-14, cy+oy-14), (cx+ox+14, cy+oy+14)], fill="#00E676", outline="#007E33", width=2)
            d.ellipse([(cx-8, cy-8), (cx+8, cy+8)], fill="#FFD700")
        elif stg == 6:
            # Brilliant Golden-Blessed 4-Leaf Mega Clover with radiant aura
            d.line([(100, 130), (100, 52)], fill="#004D40", width=7)
            d.line([(100, 100), (60, 68)], fill="#004D40", width=5)
            d.line([(100, 95), (140, 65)], fill="#004D40", width=5)
            # Main clover
            for cx, cy, sz in [(100, 42, 18), (55, 62, 12), (145, 58, 12)]:
                for ox, oy in [(-sz, 0), (sz, 0), (0, -sz), (0, sz)]:
                    d.ellipse([(cx+ox-sz, cy+oy-sz), (cx+ox+sz, cy+oy+sz)], fill="#00E676", outline="#004D40", width=2)
                d.ellipse([(cx-sz//2, cy-sz//2), (cx+sz//2, cy+sz//2)], fill="#FFD700")
            for sx, sy in [(40, 20), (160, 20), (100, 8), (20, 50), (180, 50)]:
                d.polygon([(sx, sy-6), (sx+3, sy), (sx+8, sy+1), (sx+4, sy+4), (sx+5, sy+9), (sx, sy+6), (sx-5, sy+9), (sx-4, sy+4), (sx-8, sy+1), (sx-3, sy)], fill="#FFD700")

        img.save(os.path.join(output_dir, f"stage_clover_{stg}.png"))

    # 5. Cherry Blossom (🌸 벚꽃나무, 1~6단계)
    for stg in range(1, 7):
        img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        draw_pot(d, 3 if stg >= 5 else (2 if stg >= 3 else 1))
        if stg == 1:
            d.line([(100, 130), (100, 105)], fill="#795548", width=4)
            d.ellipse([(94, 95), (106, 107)], fill="#F8BBD0", outline="#C2185B", width=2)
        elif stg == 2:
            d.line([(100, 130), (100, 90)], fill="#795548", width=5)
            d.ellipse([(90, 75), (110, 95)], fill="#F8BBD0", outline="#C2185B", width=2)
        elif stg == 3:
            d.line([(100, 130), (100, 70)], fill="#5D4037", width=7)
            d.line([(100, 95), (75, 75)], fill="#5D4037", width=4)
            d.line([(100, 90), (125, 70)], fill="#5D4037", width=4)
            for bx, by in [(75, 70), (125, 65), (100, 60)]:
                d.ellipse([(bx-8, by-8), (bx+8, by+8)], fill="#F48FB1", outline="#AD1457", width=2)
        elif stg == 4:
            d.line([(100, 130), (100, 60)], fill="#4E342E", width=8)
            d.line([(100, 90), (65, 65)], fill="#4E342E", width=5)
            d.line([(100, 85), (135, 60)], fill="#4E342E", width=5)
            for bx, by in [(65, 60), (135, 55), (100, 45), (80, 40), (120, 35)]:
                d.ellipse([(bx-10, by-10), (bx+10, by+10)], fill="#F06292", outline="#880E4F", width=2)
        elif stg == 5:
            d.line([(100, 130), (100, 60)], fill="#3E2723", width=9)
            d.line([(100, 95), (60, 65)], fill="#3E2723", width=6)
            d.line([(100, 90), (140, 60)], fill="#3E2723", width=6)
            clusters = [(100, 35), (70, 50), (130, 45), (85, 25), (115, 22), (55, 65), (145, 60)]
            for cx, cy in clusters:
                d.ellipse([(cx-16, cy-16), (cx+16, cy+16)], fill="#FF80AB", outline="#C2185B", width=1)
                d.ellipse([(cx-6, cy-6), (cx+6, cy+6)], fill="#FFF")
            d.ellipse([(45, 90), (53, 98)], fill="#FF80AB")
            d.ellipse([(145, 95), (153, 103)], fill="#FF80AB")
        elif stg == 6:
            # Grand Cherry Blossom tree with falling petals and golden twilight glow
            d.line([(100, 130), (100, 55)], fill="#2E1C14", width=10)
            d.line([(100, 95), (55, 60)], fill="#2E1C14", width=7)
            d.line([(100, 90), (145, 55)], fill="#2E1C14", width=7)
            d.line([(100, 75), (80, 35)], fill="#2E1C14", width=5)
            d.line([(100, 75), (120, 32)], fill="#2E1C14", width=5)
            clusters = [
                (100, 30), (70, 42), (130, 38), (85, 18), (115, 16),
                (48, 55), (152, 50), (35, 75), (165, 70), (100, 52)
            ]
            for cx, cy in clusters:
                d.ellipse([(cx-18, cy-18), (cx+18, cy+18)], fill="#FF4081", outline="#AD1457", width=1)
                d.ellipse([(cx-8, cy-8), (cx+8, cy+8)], fill="#FFF")
            # Multiple drifting petals
            for px, py in [(30, 95), (170, 90), (45, 115), (155, 120), (80, 110), (120, 112)]:
                d.ellipse([(px-5, py-5), (px+5, py+5)], fill="#FF80AB")

        img.save(os.path.join(output_dir, f"stage_cherry_{stg}.png"))

    # Reaction particle icons
    img_heart = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dh = ImageDraw.Draw(img_heart)
    dh.ellipse([(8, 10), (34, 36)], fill="#FF4081")
    dh.ellipse([(30, 10), (56, 36)], fill="#FF4081")
    dh.polygon([(9, 24), (55, 24), (32, 54)], fill="#FF4081")
    img_heart.save(os.path.join(output_dir, "heart.png"))

    img_water = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dw = ImageDraw.Draw(img_water)
    dw.ellipse([(14, 22), (50, 58)], fill="#42A5F5", outline="#1E88E5", width=2)
    dw.polygon([(17, 32), (47, 32), (32, 6)], fill="#42A5F5")
    img_water.save(os.path.join(output_dir, "drop.png"))

    img_sun = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ds = ImageDraw.Draw(img_sun)
    ds.ellipse([(16, 16), (48, 48)], fill="#FFCA28", outline="#FFA000", width=2)
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        x1 = 32 + int(20 * math.cos(rad))
        y1 = 32 + int(20 * math.sin(rad))
        x2 = 32 + int(28 * math.cos(rad))
        y2 = 32 + int(28 * math.sin(rad))
        ds.line([(x1, y1), (x2, y2)], fill="#FFA000", width=3)
    img_sun.save(os.path.join(output_dir, "sun.png"))

    # App icon
    app_icon = Image.open(os.path.join(output_dir, "stage_cherry_6.png"))
    app_icon.save(os.path.join(output_dir, "app_icon.png"))
    app_icon.save(os.path.join(output_dir, "app_icon.ico"), format="ICO", sizes=[(64, 64), (128, 128), (200, 200)])

    print("All 6-stage multi-species assets generated successfully in:", output_dir)

if __name__ == "__main__":
    create_assets("assets")
