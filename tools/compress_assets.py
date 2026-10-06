# -*- coding: utf-8 -*-
"""把原始卡图压缩成小程序可用的小尺寸 JPG，输出到 assets/。
原图 1024x1536 (2:3)，统一缩到 360x540，质量 82。
文件名（不含扩展名）即卡牌 ID，保持不变。
"""
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS = [
    ("好人群友卡牌卡面", "face"),
    ("神人群友卡牌卡面", "trap"),
]
BACK_SRC = os.path.join(ROOT, "卡背", "cardback.png")
BACK_DST = os.path.join(ROOT, "assets", "back.jpg")
SIZE = (360, 540)
QUALITY = 82


def convert(src_dir, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)
    names = sorted(os.listdir(src_dir))
    out = []
    for name in names:
        if not name.lower().endswith(".png"):
            continue
        stem = os.path.splitext(name)[0]
        src = os.path.join(src_dir, name)
        dst = os.path.join(dst_dir, stem + ".jpg")
        im = Image.open(src).convert("RGB")
        if im.size != SIZE:
            im = im.resize(SIZE, Image.LANCZOS)
        im.save(dst, "JPEG", quality=QUALITY, optimize=True)
        out.append(stem)
    return out


def main():
    pool = {}
    for src_name, dst_name in JOBS:
        src_dir = os.path.join(ROOT, src_name)
        dst_dir = os.path.join(ROOT, "assets", dst_name)
        pool[dst_name] = convert(src_dir, dst_dir)

    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    im = Image.open(BACK_SRC).convert("RGB")
    if im.size != SIZE:
        im = im.resize(SIZE, Image.LANCZOS)
    im.save(BACK_DST, "JPEG", quality=QUALITY, optimize=True)

    total = sum(len(v) for v in pool.values())
    print("face:", len(pool["face"]), "trap:", len(pool["trap"]), "total cards:", total)

    # 生成 config/config.js 的卡池清单（保持文件名即 ID）
    lines = ["// 卡池配置：文件名（不含扩展名）即卡牌 ID，新增卡只需把图片放进对应目录并在下列数组加名字。", "// 原始大图在 好人群友卡牌卡面/ 神人群友卡牌卡面/ 卡背/，由 tools/compress_assets.py 压缩生成 assets/ 下的 jpg。", "const BACK_IMG = '/assets/back.jpg';", "", "const FACE_CARDS = ["]
    for s in pool["face"]:
        lines.append("  '%s'," % s)
    lines.append("];")
    lines.append("")
    lines.append("const TRAP_CARDS = [")
    for s in pool["trap"]:
        lines.append("  '%s'," % s)
    lines.append("];")
    lines.append("")
    lines.append("module.exports = {")
    lines.append("  BACK_IMG,")
    lines.append("  FACE_CARDS,")
    lines.append("  TRAP_CARDS,")
    lines.append("};")
    text = "\n".join(lines) + "\n"
    cfg_dir = os.path.join(ROOT, "config")
    os.makedirs(cfg_dir, exist_ok=True)
    with open(os.path.join(cfg_dir, "cards.js"), "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote config/cards.js")


if __name__ == "__main__":
    main()
