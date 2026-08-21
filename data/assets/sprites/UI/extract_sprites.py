"""
Extracteur automatique de sprites depuis une spritesheet.
Fonctionne par detection de zones connectees (via le canal alpha),
donc pas besoin d'une grille reguliere : marche meme si les sprites
ont des tailles differentes (boutons, panneaux, icones, armes...).
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from scipy import ndimage
import json
import os

def extract_sprites(sheet_path, out_dir, prefix, min_size=6, pad=1):
    os.makedirs(out_dir, exist_ok=True)
    im = Image.open(sheet_path).convert('RGBA')
    arr = np.array(im)
    mask = arr[:, :, 3] > 10
    structure = np.ones((3, 3))  # connectivite 8 directions
    labeled, n = ndimage.label(mask, structure=structure)
    objs = ndimage.find_objects(labeled)

    # tri par position (haut->bas, gauche->droite) pour un ordre logique
    boxes = []
    for sl in objs:
        if sl is None:
            continue
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        w, h = x1 - x0, y1 - y0
        if w < min_size or h < min_size:
            continue
        boxes.append((x0, y0, x1, y1, w, h))
    boxes.sort(key=lambda b: (round(b[1] / 20), b[0]))  # groupe par bandes de ~20px puis x

    manifest = []
    for i, (x0, y0, x1, y1, w, h) in enumerate(boxes):
        # petit padding pour ne pas rogner l'anti-aliasing des bords
        px0, py0 = max(0, x0 - pad), max(0, y0 - pad)
        px1, py1 = min(im.width, x1 + pad), min(im.height, y1 + pad)
        sprite = im.crop((px0, py0, px1, py1))
        filename = f"{prefix}_{i:03d}.png"
        sprite.save(os.path.join(out_dir, filename))
        manifest.append({
            "id": f"{prefix}_{i:03d}",
            "file": filename,
            "x": x0, "y": y0, "w": w, "h": h
        })

    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"{sheet_path} -> {len(manifest)} sprites extraits dans {out_dir}")
    return manifest, im

def make_index_sheet(im, manifest, out_path, scale=4):
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST).convert('RGB')
    draw = ImageDraw.Draw(big)
    for i, m in enumerate(manifest):
        x0, y0 = m["x"] * scale, m["y"] * scale
        x1, y1 = x0 + m["w"] * scale, y0 + m["h"] * scale
        draw.rectangle([x0, y0, x1, y1], outline=(0, 255, 0), width=1)
        draw.text((x0 + 2, y0 + 2), str(i), fill=(255, 255, 0))
    big.save(out_path)

m1, im1 = extract_sprites("/mnt/user-data/uploads/freefantasy.png", "/home/claude/output/sprites/freefantasy", "ff")
m2, im2 = extract_sprites("/mnt/user-data/uploads/MediavelFree.png", "/home/claude/output/sprites/MediavelFree", "mf")

make_index_sheet(im1, m1, "/home/claude/output/sprites/freefantasy/index.png")
make_index_sheet(im2, m2, "/home/claude/output/sprites/MediavelFree/index.png")
