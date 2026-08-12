# -*- coding: utf-8 -*-
"""
generate_icon.py — Tạo file app.ico (icon cho Deep System Cleaner).

Icon vẽ bằng Pillow: chổi quét (broom) trên nền gradient xanh.
Output: app.ico (256x256, multi-size).

Chạy:  python generate_icon.py
"""

from PIL import Image, ImageDraw, ImageFont
import math

def create_icon():
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    for sz in sizes:
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Nền tròn gradient xanh
        margin = max(1, sz // 20)
        for y in range(sz):
            for x in range(sz):
                cx, cy = sz / 2, sz / 2
                r = sz / 2 - margin
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    # Gradient: xanh đậm trên → xanh dương dưới
                    t = y / sz
                    red = int(20 + t * 30)
                    green = int(100 + t * 80)
                    blue = int(200 - t * 40)
                    alpha = 255
                    img.putpixel((x, y), (red, green, blue, alpha))

        # Vẽ chổi: cán (trắng) + đầu (vàng)
        cx, cy = sz // 2, sz // 2

        # Cán chổi (nghiêng 30 độ)
        angle = math.radians(30)
        stick_len = sz * 0.35
        stick_w = max(2, sz // 16)
        x1 = cx - stick_len * math.cos(angle) * 0.5
        y1 = cy + stick_len * math.sin(angle) * 0.5
        x2 = cx + stick_len * math.cos(angle) * 0.5
        y2 = cy - stick_len * math.sin(angle) * 0.5
        draw.line([(x1, y1), (x2, y2)], fill="white", width=stick_w)

        # Đầu chổi (3 sợi vàng)
        brush_len = sz * 0.22
        brush_w = max(2, sz // 12)
        bx, by = x1, y1  # gốc đầu chổi (dưới)
        for offset in [-1, 0, 1]:
            ox = offset * brush_w * 0.7
            ex = bx - ox + brush_len * math.cos(angle + math.radians(45)) * 0.3
            ey = by + ox * 0.5 + brush_len * 0.5
            draw.line([(bx + ox, by), (ex, ey)],
                      fill="#FFD700", width=max(1, brush_w // 2))

        # Vẽ "shield" nhỏ (khiên) ở góc dưới phải
        if sz >= 48:
            shield_x = sz * 0.7
            shield_y = sz * 0.7
            shield_r = sz * 0.15
            # Khiên: tam giác bo tròn
            pts = [
                (shield_x, shield_y - shield_r),
                (shield_x + shield_r, shield_y - shield_r * 0.3),
                (shield_x + shield_r * 0.8, shield_y + shield_r * 0.7),
                (shield_x, shield_y + shield_r),
                (shield_x - shield_r * 0.8, shield_y + shield_r * 0.7),
                (shield_x - shield_r, shield_y - shield_r * 0.3),
            ]
            draw.polygon(pts, fill="#27ae60", outline="white")
            # Dấu check trong khiên
            check_size = shield_r * 0.5
            draw.line([
                (shield_x - check_size * 0.4, shield_y),
                (shield_x - check_size * 0.1, shield_y + check_size * 0.3),
                (shield_x + check_size * 0.5, shield_y - check_size * 0.3),
            ], fill="white", width=max(1, sz // 30))

        images.append(img)

    # Lưu ICO đa kích thước. Lưu ảnh lớn nhất (256) làm base để trình duyệt/explorer
    # hiển thị icon chất lượng cao, dùng append_images cho các size còn lại.
    # Sắp xếp lớn → nhỏ để ICO header đúng chuẩn.
    ordered = sorted(images, key=lambda im: -im.width)
    import os
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _ico = os.path.join(_root, "assets", "app.ico")
    os.makedirs(os.path.dirname(_ico), exist_ok=True)
    ordered[0].save(_ico, format="ICO",
                    sizes=[(s, s) for s in sizes],
                    append_images=ordered[1:])
    print(f"Đã tạo {_ico} ({os.path.getsize(_ico)} bytes, {len(sizes)} kích thước)")


if __name__ == "__main__":
    create_icon()
