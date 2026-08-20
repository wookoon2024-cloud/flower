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
            d.line([(100, 142), (100, 100)], fill="#4CAF50", width=4)
            d.ellipse([(80, 85), (104, 105)], fill="#81C784", outline="#2E7D32", width=2)
        elif stg == 2:
            # Two healthy sprout leaves
            d.line([(100, 142), (100, 92)], fill="#4CAF50", width=5)
            d.pieslice([(72, 75), (102, 105)], start=180, end=300, fill="#81C784", outline="#2E7D32", width=2)
            d.pieslice([(98, 70), (128, 100)], start=240, end=360, fill="#A5D6A7", outline="#2E7D32", width=2)
        elif stg == 3:
            # Multi-leaf growing shoot
            d.line([(100, 142), (100, 70)], fill="#388E3C", width=6)
            d.pieslice([(55, 80), (100, 115)], start=160, end=320, fill="#66BB6A", outline="#2E7D32", width=2)
            d.pieslice([(100, 65), (145, 100)], start=220, end=380, fill="#81C784", outline="#2E7D32", width=2)
            d.pieslice([(65, 55), (100, 85)], start=140, end=290, fill="#A5D6A7", outline="#2E7D32", width=2)
        elif stg == 4:
            # First delicate flower bud
            d.line([(100, 142), (100, 60)], fill="#2E7D32", width=6)
            d.pieslice([(50, 70), (100, 110)], start=160, end=320, fill="#4CAF50", outline="#1B5E20", width=2)
            d.pieslice([(100, 70), (150, 110)], start=220, end=380, fill="#66BB6A", outline="#1B5E20", width=2)
            d.ellipse([(86, 36), (114, 64)], fill="#F48FB1", outline="#C2185B", width=2)
            d.ellipse([(92, 42), (108, 58)], fill="#F06292")
        elif stg == 5:
            # Blooming flower
            d.line([(100, 142), (100, 55)], fill="#2E7D32", width=7)
            d.pieslice([(50, 75), (98, 115)], start=160, end=320, fill="#4CAF50", outline="#1B5E20", width=2)
            d.pieslice([(102, 75), (150, 115)], start=220, end=380, fill="#66BB6A", outline="#1B5E20", width=2)
            for p in [(75, 20, 105, 50), (95, 20, 125, 50), (65, 40, 95, 70), (105, 40, 135, 70), (75, 55, 105, 85), (95, 55, 125, 85)]:
                d.ellipse(p, fill="#FF80AB", outline="#C2185B", width=2)
            d.ellipse([(85, 38), (115, 68)], fill="#FFEE58", outline="#F57F17", width=2)
        elif stg == 6:
            # Legendary Full Bloom with sparkling aura & golden crown flower
            d.line([(100, 142), (100, 50)], fill="#1B5E20", width=8)
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
            d.line([(100, 142), (100, 98)], fill="#4CAF50", width=4)
            d.ellipse([(85, 82), (115, 102)], fill="#FFD54F", outline="#F57F17", width=2)
        elif stg == 2:
            d.line([(100, 142), (100, 90)], fill="#4CAF50", width=5)
            d.ellipse([(70, 75), (96, 95)], fill="#FFD54F", outline="#F57F17", width=2)
            d.ellipse([(104, 75), (130, 95)], fill="#FFD54F", outline="#F57F17", width=2)
        elif stg == 3:
            d.line([(100, 142), (100, 65)], fill="#2E7D32", width=7)
            d.pieslice([(50, 75), (98, 115)], start=160, end=320, fill="#4CAF50", outline="#1B5E20", width=2)
            d.pieslice([(102, 75), (150, 115)], start=220, end=380, fill="#66BB6A", outline="#1B5E20", width=2)
        elif stg == 4:
            d.line([(100, 142), (100, 55)], fill="#2E7D32", width=7)
            d.pieslice([(45, 70), (98, 115)], start=160, end=320, fill="#4CAF50", outline="#1B5E20", width=2)
            d.pieslice([(102, 70), (155, 115)], start=220, end=380, fill="#66BB6A", outline="#1B5E20", width=2)
            d.ellipse([(82, 28), (118, 64)], fill="#8D6E63", outline="#5D4037", width=2)
            for ang in range(0, 360, 60):
                rad = math.radians(ang)
                px = 100 + int(20 * math.cos(rad))
                py = 46 + int(20 * math.sin(rad))
                d.ellipse([(px-6, py-6), (px+6, py+6)], fill="#FFCA28", outline="#FFA000")
        elif stg == 5:
            d.line([(100, 142), (100, 55)], fill="#2E7D32", width=8)
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
            d.line([(100, 142), (100, 48)], fill="#1B5E20", width=9)
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
            d.rounded_rectangle([(90, 105), (110, 142)], radius=8, fill="#66BB6A", outline="#2E7D32", width=2)
        elif stg == 2:
            d.rounded_rectangle([(85, 95), (115, 142)], radius=12, fill="#4CAF50", outline="#2E7D32", width=2)
        elif stg == 3:
            d.rounded_rectangle([(80, 70), (120, 142)], radius=16, fill="#4CAF50", outline="#2E7D32", width=2)
            d.line([(88, 80), (88, 120)], fill="#81C784", width=2)
            d.line([(112, 80), (112, 120)], fill="#81C784", width=2)
        elif stg == 4:
            d.rounded_rectangle([(75, 55), (125, 142)], radius=18, fill="#43A047", outline="#1B5E20", width=2)
            d.rounded_rectangle([(55, 75), (80, 100)], radius=10, fill="#43A047", outline="#1B5E20", width=2)
            d.rounded_rectangle([(120, 68), (145, 93)], radius=10, fill="#43A047", outline="#1B5E20", width=2)
            d.ellipse([(92, 44), (108, 58)], fill="#F44336", outline="#B71C1C", width=2)
        elif stg == 5:
            d.rounded_rectangle([(72, 45), (128, 142)], radius=20, fill="#388E3C", outline="#1B5E20", width=3)
            d.rounded_rectangle([(45, 65), (76, 95)], radius=12, fill="#388E3C", outline="#1B5E20", width=2)
            d.rounded_rectangle([(124, 58), (155, 88)], radius=12, fill="#388E3C", outline="#1B5E20", width=2)
            for fx, fy in [(100, 35), (55, 55), (145, 50)]:
                d.ellipse([(fx-12, fy-12), (fx+12, fy+12)], fill="#FFEB3B", outline="#F57F17", width=2)
                d.ellipse([(fx-5, fy-5), (fx+5, fy+5)], fill="#FF5722")
        elif stg == 6:
            # Giant cactus with multiple flowering branches and majestic crown
            d.rounded_rectangle([(70, 38), (130, 142)], radius=22, fill="#2E7D32", outline="#1B5E20", width=3)
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
            d.line([(100, 142), (100, 105)], fill="#4CAF50", width=3)
            d.ellipse([(92, 95), (108, 108)], fill="#81C784", outline="#2E7D32", width=2)
        elif stg == 2:
            d.line([(100, 142), (100, 95)], fill="#4CAF50", width=4)
            d.ellipse([(85, 80), (102, 98)], fill="#66BB6A", outline="#2E7D32", width=2)
            d.ellipse([(98, 80), (115, 98)], fill="#66BB6A", outline="#2E7D32", width=2)
        elif stg == 3:
            d.line([(100, 142), (100, 75)], fill="#388E3C", width=5)
            d.ellipse([(80, 60), (100, 80)], fill="#4CAF50", outline="#1B5E20", width=2)
            d.ellipse([(100, 60), (120, 80)], fill="#4CAF50", outline="#1B5E20", width=2)
            d.ellipse([(90, 45), (110, 65)], fill="#66BB6A", outline="#1B5E20", width=2)
        elif stg == 4:
            d.line([(100, 142), (100, 65)], fill="#2E7D32", width=6)
            d.line([(100, 110), (75, 80)], fill="#2E7D32", width=4)
            d.line([(100, 105), (125, 78)], fill="#2E7D32", width=4)
            for cx, cy in [(100, 50), (70, 75), (130, 72)]:
                for ox, oy in [(-8, 0), (8, 0), (0, -8)]:
                    d.ellipse([(cx+ox-9, cy+oy-9), (cx+ox+9, cy+oy+9)], fill="#43A047", outline="#1B5E20", width=2)
        elif stg == 5:
            d.line([(100, 142), (100, 60)], fill="#1B5E20", width=6)
            cx, cy = 100, 48
            for ox, oy in [(-16, 0), (16, 0), (0, -16), (0, 16)]:
                d.ellipse([(cx+ox-14, cy+oy-14), (cx+ox+14, cy+oy+14)], fill="#00E676", outline="#007E33", width=2)
            d.ellipse([(cx-8, cy-8), (cx+8, cy+8)], fill="#FFD700")
        elif stg == 6:
            # Brilliant Golden-Blessed 4-Leaf Mega Clover with radiant aura
            d.line([(100, 142), (100, 52)], fill="#004D40", width=7)
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
            d.line([(100, 142), (100, 105)], fill="#795548", width=4)
            d.ellipse([(94, 95), (106, 107)], fill="#F8BBD0", outline="#C2185B", width=2)
        elif stg == 2:
            d.line([(100, 142), (100, 90)], fill="#795548", width=5)
            d.ellipse([(90, 75), (110, 95)], fill="#F8BBD0", outline="#C2185B", width=2)
        elif stg == 3:
            d.line([(100, 142), (100, 70)], fill="#5D4037", width=7)
            d.line([(100, 95), (75, 75)], fill="#5D4037", width=4)
            d.line([(100, 90), (125, 70)], fill="#5D4037", width=4)
            for bx, by in [(75, 70), (125, 65), (100, 60)]:
                d.ellipse([(bx-8, by-8), (bx+8, by+8)], fill="#F48FB1", outline="#AD1457", width=2)
        elif stg == 4:
            d.line([(100, 142), (100, 60)], fill="#4E342E", width=8)
            d.line([(100, 90), (65, 65)], fill="#4E342E", width=5)
            d.line([(100, 85), (135, 60)], fill="#4E342E", width=5)
            for bx, by in [(65, 60), (135, 55), (100, 45), (80, 40), (120, 35)]:
                d.ellipse([(bx-10, by-10), (bx+10, by+10)], fill="#F06292", outline="#880E4F", width=2)
        elif stg == 5:
            d.line([(100, 142), (100, 60)], fill="#3E2723", width=9)
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
            d.line([(100, 142), (100, 55)], fill="#2E1C14", width=10)
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

    def draw_royal_pot(draw: ImageDraw.ImageDraw, face_type: int = 3):
        # Royal Amethyst & Gold Celestial Pot
        draw.polygon([(50, 143), (150, 143), (135, 198), (65, 198)], fill="#4C1D95", outline="#FFD700", width=3)
        draw.rounded_rectangle([(42, 133), (158, 145)], radius=5, fill="#5B21B6", outline="#FFD700", width=3)
        # Cosmic Star Soil
        draw.ellipse([(55, 138), (145, 148)], fill="#1E1B4B")
        # Gold Star Emblem on Pot
        draw.polygon([(100, 148), (103, 154), (110, 155), (105, 159), (106, 166), (100, 162), (94, 166), (95, 159), (90, 155), (97, 154)], fill="#FDE047")
        # Cute sparkling Face
        draw.ellipse([(84, 170), (92, 178)], fill="#FEF08A")
        draw.ellipse([(108, 170), (116, 178)], fill="#FEF08A")
        draw.ellipse([(86, 172), (89, 175)], fill="#1E1B4B")
        draw.ellipse([(110, 172), (113, 175)], fill="#1E1B4B")
        # Cheerful mouth & glowing blush
        draw.arc([(93, 174), (107, 186)], start=0, end=180, fill="#F472B6", width=2)
        draw.ellipse([(74, 173), (82, 179)], fill="#E879F9")
        draw.ellipse([(118, 173), (126, 179)], fill="#E879F9")

    # 6. Secret Legendary Starlight Galaxy Rose (🌟 은하수 별빛 장미, 1~6단계)
    for stg in range(1, 7):
        img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        draw_royal_pot(d, 3)

        if stg == 1:
            # 1. Luminous celestial sprout
            d.line([(100, 142), (100, 90)], fill="#10B981", width=5)
            d.ellipse([(78, 80), (102, 102)], fill="#38BDF8", outline="#818CF8", width=2)
            d.polygon([(90, 75), (93, 81), (99, 82), (95, 86), (96, 92), (90, 88), (84, 92), (85, 86), (81, 82), (87, 81)], fill="#FDE047")
        elif stg == 2:
            # 2. Dual crystalline aurora leaves
            d.line([(100, 142), (100, 85)], fill="#10B981", width=6)
            d.pieslice([(70, 70), (105, 105)], start=170, end=310, fill="#38BDF8", outline="#6366F1", width=2)
            d.pieslice([(95, 65), (130, 100)], start=230, end=370, fill="#A78BFA", outline="#6366F1", width=2)
            # Floating stars
            for sx, sy in [(65, 60), (135, 55)]:
                d.polygon([(sx, sy-4), (sx+2, sy), (sx+6, sy+1), (sx+3, sy+3), (sx+4, sy+7), (sx, sy+4), (sx-4, sy+7), (sx-3, sy+3), (sx-6, sy+1), (sx-2, sy)], fill="#FDE047")
        elif stg == 3:
            # 3. Celestial triple-stem & shimmering foliage
            d.line([(100, 142), (100, 65)], fill="#059669", width=7)
            d.pieslice([(50, 75), (98, 115)], start=150, end=310, fill="#38BDF8", outline="#4338CA", width=2)
            d.pieslice([(102, 70), (150, 110)], start=230, end=390, fill="#C084FC", outline="#4338CA", width=2)
            d.pieslice([(65, 50), (105, 85)], start=130, end=290, fill="#E879F9", outline="#4338CA", width=2)
            # Radiant aura particles
            for sx, sy in [(50, 45), (145, 40), (100, 35)]:
                d.polygon([(sx, sy-5), (sx+3, sy), (sx+8, sy+1), (sx+4, sy+4), (sx+5, sy+9), (sx, sy+5), (sx-5, sy+9), (sx-4, sy+4), (sx-8, sy+1), (sx-3, sy)], fill="#FDE047")
        elif stg == 4:
            # 4. Delicate glowing galaxy rose bud
            d.line([(100, 142), (100, 55)], fill="#047857", width=8)
            d.pieslice([(45, 65), (98, 108)], start=150, end=310, fill="#38BDF8", outline="#4338CA", width=2)
            d.pieslice([(102, 65), (155, 108)], start=230, end=390, fill="#818CF8", outline="#4338CA", width=2)
            # Rose bud layers
            d.ellipse([(80, 26), (120, 66)], fill="#7C3AED", outline="#4C1D95", width=2)
            d.ellipse([(86, 32), (114, 60)], fill="#C084FC", outline="#6D28D9", width=2)
            d.ellipse([(92, 38), (108, 54)], fill="#F472B6")
            # Sepals
            d.polygon([(82, 60), (100, 72), (118, 60)], fill="#10B981")
            for sx, sy in [(40, 30), (160, 25)]:
                d.polygon([(sx, sy-6), (sx+4, sy), (sx+9, sy+1), (sx+5, sy+5), (sx+6, sy+10), (sx, sy+6), (sx-6, sy+10), (sx-5, sy+5), (sx-9, sy+1), (sx-4, sy)], fill="#FDE047")
        elif stg == 5:
            # 5. Blooming Galaxy Rose
            d.line([(100, 142), (100, 52)], fill="#047857", width=8)
            d.pieslice([(42, 70), (96, 112)], start=150, end=310, fill="#38BDF8", outline="#4338CA", width=2)
            d.pieslice([(104, 70), (158, 112)], start=230, end=390, fill="#818CF8", outline="#4338CA", width=2)
            # Outer rose petals (6 directions)
            for ang in range(0, 360, 60):
                rad = math.radians(ang)
                px = 100 + int(24 * math.cos(rad))
                py = 42 + int(24 * math.sin(rad))
                d.ellipse([(px-16, py-16), (px+16, py+16)], fill="#A855F7", outline="#581C87", width=2)
            # Inner layered rose spiral
            for ang in range(30, 390, 60):
                rad = math.radians(ang)
                px = 100 + int(14 * math.cos(rad))
                py = 42 + int(14 * math.sin(rad))
                d.ellipse([(px-12, py-12), (px+12, py+12)], fill="#EC4899", outline="#831843", width=2)
            # Glowing core
            d.ellipse([(88, 30), (112, 54)], fill="#FDE047", outline="#D97706", width=2)
            d.ellipse([(94, 36), (106, 48)], fill="#FFFFFF")
            # Stardust aura
            for sx, sy in [(30, 35), (170, 30), (35, 75), (165, 70)]:
                d.polygon([(sx, sy-6), (sx+4, sy), (sx+9, sy+1), (sx+5, sy+5), (sx+6, sy+10), (sx, sy+6), (sx-6, sy+10), (sx-5, sy+5), (sx-9, sy+1), (sx-4, sy)], fill="#FDE047")
        elif stg == 6:
            # 6. 🌟 Legendary Starlight Galaxy Rose Master Bloom with Constellation Halo
            d.line([(100, 142), (100, 48)], fill="#064E3B", width=9)
            d.pieslice([(38, 68), (96, 115)], start=150, end=310, fill="#06B6D4", outline="#1E1B4B", width=2)
            d.pieslice([(104, 68), (162, 115)], start=230, end=390, fill="#8B5CF6", outline="#1E1B4B", width=2)
            d.pieslice([(60, 45), (105, 80)], start=130, end=290, fill="#EC4899", outline="#1E1B4B", width=2)
            d.pieslice([(95, 45), (140, 80)], start=250, end=410, fill="#38BDF8", outline="#1E1B4B", width=2)

            # Radiating Celestial Outer Rose Petals (8 directions)
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                px = 100 + int(32 * math.cos(rad))
                py = 40 + int(32 * math.sin(rad))
                d.ellipse([(px-18, py-18), (px+18, py+18)], fill="#8B5CF6", outline="#4C1D95", width=2)
                d.ellipse([(px-12, py-12), (px+12, py+12)], fill="#C084FC")

            # Mid Petals
            for ang in range(22, 382, 45):
                rad = math.radians(ang)
                px = 100 + int(20 * math.cos(rad))
                py = 40 + int(20 * math.sin(rad))
                d.ellipse([(px-14, py-14), (px+14, py+14)], fill="#F43F5E", outline="#9F1239", width=2)
                d.ellipse([(px-8, py-8), (px+8, py+8)], fill="#FB7185")

            # Core Cosmic Crystal
            d.ellipse([(82, 22), (118, 58)], fill="#FEF08A", outline="#D97706", width=3)
            d.ellipse([(88, 28), (112, 52)], fill="#FFFFFF")
            # Star twinkle in center
            d.polygon([(100, 30), (103, 37), (110, 40), (103, 43), (100, 50), (97, 43), (90, 40), (97, 37)], fill="#F59E0B")

            # Constellation Crown Halo (8 Golden Stars orbiting)
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                sx = 100 + int(56 * math.cos(rad))
                sy = 40 + int(48 * math.sin(rad))
                d.polygon([(sx, sy-7), (sx+4, sy), (sx+10, sy+1), (sx+5, sy+5), (sx+6, sy+11), (sx, sy+7), (sx-6, sy+11), (sx-5, sy+5), (sx-10, sy+1), (sx-4, sy)], fill="#FFD700")

            # Stardust drifting particles
            for px, py in [(25, 95), (175, 90), (35, 120), (165, 115), (70, 110), (130, 108)]:
                d.ellipse([(px-4, py-4), (px+4, py+4)], fill="#FDE047")

        img.save(os.path.join(output_dir, f"stage_starlight_rose_{stg}.png"))

    # Reaction particle icons (10종 감정 파티클 에셋)
    # 1. 💖 Heart
    img_heart = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dh = ImageDraw.Draw(img_heart)
    dh.ellipse([(8, 10), (34, 36)], fill="#FF4081")
    dh.ellipse([(30, 10), (56, 36)], fill="#FF4081")
    dh.polygon([(9, 24), (55, 24), (32, 54)], fill="#FF4081")
    img_heart.save(os.path.join(output_dir, "heart.png"))

    # 2. 💧 Water Drop
    img_water = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dw = ImageDraw.Draw(img_water)
    dw.ellipse([(14, 22), (50, 58)], fill="#42A5F5", outline="#1E88E5", width=2)
    dw.polygon([(17, 32), (47, 32), (32, 6)], fill="#42A5F5")
    img_water.save(os.path.join(output_dir, "drop.png"))

    # 3. ☀️ Sun
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

    # 4. 🌟 Golden Star
    img_star = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dstar = ImageDraw.Draw(img_star)
    star_pts = []
    for i in range(10):
        r = 26 if i % 2 == 0 else 11
        angle = i * math.pi / 5.0 - math.pi / 2.0
        star_pts.append((32 + int(r * math.cos(angle)), 32 + int(r * math.sin(angle))))
    dstar.polygon(star_pts, fill="#FFD700", outline="#F59E0B")
    img_star.save(os.path.join(output_dir, "star.png"))

    # 5. 🎵 Music Note
    img_note = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dn = ImageDraw.Draw(img_note)
    dn.ellipse([(12, 36), (28, 52)], fill="#8B5CF6")
    dn.ellipse([(34, 30), (50, 46)], fill="#8B5CF6")
    dn.rectangle([(24, 14), (28, 44)], fill="#8B5CF6")
    dn.rectangle([(46, 8), (50, 38)], fill="#8B5CF6")
    dn.polygon([(24, 14), (50, 8), (50, 16), (24, 22)], fill="#8B5CF6")
    img_note.save(os.path.join(output_dir, "note.png"))

    # 6. 🍀 Four-leaf Clover
    img_clover = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dclv = ImageDraw.Draw(img_clover)
    for cx, cy in [(24, 24), (40, 24), (24, 40), (40, 40)]:
        dclv.ellipse([(cx-9, cy-9), (cx+9, cy+9)], fill="#10B981", outline="#047857", width=1)
    dclv.line([(32, 34), (32, 54)], fill="#047857", width=3)
    img_clover.save(os.path.join(output_dir, "clover.png"))

    # 7. 🌸 Cherry Petal
    img_petal = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dpet = ImageDraw.Draw(img_petal)
    dpet.pieslice([(12, 10), (52, 54)], start=135, end=315, fill="#F472B6", outline="#DB2777", width=2)
    dpet.ellipse([(22, 14), (42, 34)], fill="#FBCFE8")
    img_petal.save(os.path.join(output_dir, "petal.png"))

    # 8. 💦 Sweat drop (Phew / Comfort)
    img_sweat = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dsw = ImageDraw.Draw(img_sweat)
    dsw.ellipse([(18, 22), (46, 52)], fill="#38BDF8", outline="#0284C7", width=2)
    dsw.polygon([(20, 30), (44, 30), (32, 10)], fill="#38BDF8")
    img_sweat.save(os.path.join(output_dir, "sweat.png"))

    # 9. ✨ Sparkle / Glitter
    img_sparkle = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dspk = ImageDraw.Draw(img_sparkle)
    dspk.polygon([(32, 6), (36, 26), (56, 32), (36, 38), (32, 58), (28, 38), (8, 32), (28, 26)], fill="#38BDF8", outline="#818CF8")
    dspk.ellipse([(27, 27), (37, 37)], fill="#FFFFFF")
    img_sparkle.save(os.path.join(output_dir, "sparkle.png"))

    # 10. ☕ Coffee Bean / Mug
    img_coffee = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img_coffee)
    dc.rounded_rectangle([(14, 20), (46, 52)], radius=6, fill="#78350F", outline="#451A03", width=2)
    dc.arc([(40, 26), (54, 46)], start=270, end=90, fill="#78350F", width=3)
    # Steam waves
    dc.arc([(20, 6), (28, 18)], start=0, end=180, fill="#D97706", width=2)
    dc.arc([(32, 6), (40, 18)], start=0, end=180, fill="#D97706", width=2)
    img_coffee.save(os.path.join(output_dir, "coffee.png"))

    # App icon
    app_icon = Image.open(os.path.join(output_dir, "stage_cherry_6.png"))
    app_icon.save(os.path.join(output_dir, "app_icon.png"))
    app_icon.save(os.path.join(output_dir, "app_icon.ico"), format="ICO", sizes=[(64, 64), (128, 128), (200, 200)])

    print("All 6-stage multi-species assets generated successfully in:", output_dir)

if __name__ == "__main__":
    create_assets("assets")
