"""Assemble rendered transparent frame PNGs into an animated GIF.

Composites each `frame_NNN.png` onto a solid background color (default `#fef9ed` warm cream, any
`#rrggbb` passed via `--bg` / `BG`, or `transparent` for 1-bit GIF transparency), crops to the union
content bounding box across all frames (+ 10px padding), quantizes with a shared 48-color palette
that reserves exact RGB entries for the background and diagram palette, and maps pixels with exact
nearest-neighbor lookup in RGB space (avoiding PIL's default LUT shifting the background color).

Usage:
  python3 make_gif.py <frames_dir> <out.gif> [--bg #fef9ed | --bg #ffffff | --bg transparent] [--width 540]
  BG=transparent WIDTH=540 python3 make_gif.py <frames_dir> <out.gif>
"""

import argparse
import json
import os

import numpy as np
from PIL import Image, ImageChops


def parse_hex_color(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"Expected #RRGGBB hex color or 'transparent', got {hex_str!r}")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble rendered Excalidraw PNG frames into a GIF.")
    parser.add_argument("frames_dir", help="Directory containing frame_NNN.png and frames.json")
    parser.add_argument("out_gif", help="Output .gif path")
    parser.add_argument(
        "--bg",
        default=os.environ.get("BG", "#fef9ed"),
        help="Background hex color (#rrggbb) or 'transparent' (default: BG env or #fef9ed)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=int(os.environ.get("WIDTH", "0")),
        help="Optional maximum output width in pixels (default: WIDTH env or 0 for unscaled)",
    )
    args = parser.parse_args()

    d, out = args.frames_dir, args.out_gif
    bg_arg = args.bg.strip().lower()
    transparent = bg_arg in ("transparent", "none")
    bg = (255, 255, 255) if transparent else parse_hex_color(args.bg)

    with open(os.path.join(d, "frames.json")) as f:
        ms = json.load(f)

    rgba_frames = [
        Image.open(os.path.join(d, f"frame_{i:03d}.png")).convert("RGBA")
        for i in range(len(ms))
    ]

    # Crop to the union bounding box of visible content across all frames
    box = None
    for im in rgba_frames:
        if transparent:
            b = im.getchannel("A").getbbox()
        else:
            c = Image.new("RGBA", im.size, bg + (255,))
            c.alpha_composite(im)
            b = ImageChops.difference(c.convert("RGB"), Image.new("RGB", im.size, bg)).getbbox()
        if b is not None:
            box = b if box is None else (
                min(box[0], b[0]),
                min(box[1], b[1]),
                max(box[2], b[2]),
                max(box[3], b[3]),
            )
    if box is not None:
        pad = 10
        box = (
            max(box[0] - pad, 0),
            max(box[1] - pad, 0),
            min(box[2] + pad, rgba_frames[0].width),
            min(box[3] + pad, rgba_frames[0].height),
        )
        rgba_frames = [im.crop(box) for im in rgba_frames]

    if args.width and rgba_frames[0].width > args.width:
        h = round(rgba_frames[0].height * args.width / rgba_frames[0].width)
        rgba_frames = [im.resize((args.width, h), Image.LANCZOS) for im in rgba_frames]

    frames = []
    alphas = []
    for im in rgba_frames:
        c = Image.new("RGBA", im.size, bg + (255,))
        c.alpha_composite(im)
        frames.append(c.convert("RGB"))
        if transparent:
            alphas.append(np.asarray(im.getchannel("A"), dtype=np.uint8))

    # Build a mosaic of sampled frames so colors that appear only mid-animation survive quantization
    picks = frames[:: max(1, len(frames) // 8)] + [frames[-1]]
    mos = Image.new("RGB", (frames[0].width, frames[0].height * len(picks)))
    for i, f in enumerate(picks):
        mos.paste(f, (0, i * f.height))

    # Reserve exact RGB entries for the background and key diagram colors; median-cut fills the rest
    fixed = [
        bg,               # Exact page background (#fef9ed, #ffffff, etc.)
        (232, 89, 12),    # #e8590c orange
        (255, 216, 168),  # #ffd8a8 orange fill
        (25, 113, 194),   # #1971c2 blue
        (165, 216, 255),  # #a5d8ff blue fill
        (47, 158, 68),    # #2f9e44 green
        (12, 133, 153),   # #0c8599 teal
        (112, 72, 232),   # #7048e8 violet
        (30, 30, 30),     # #1e1e1e ink
        (134, 142, 150),  # #868e96 gray
        (173, 181, 189),  # #adb5bd light gray
        (222, 226, 230),  # #dee2e6 faint line
    ]
    n_Opaque = (47 if transparent else 48) - len(fixed)
    pal = mos.quantize(colors=n_Opaque, method=Image.Quantize.MEDIANCUT)
    opaque_pl = pal.getpalette()[: n_Opaque * 3] + [c for col in fixed for c in col]
    palette_rgb = np.array(opaque_pl, dtype=np.int32).reshape(-1, 3)

    if transparent:
        # Reserve palette index 0 for transparency; shift opaque colors to 1..47
        pl = [0, 0, 0] + opaque_pl

        def to_pal(frame: Image.Image, alpha: np.ndarray) -> Image.Image:
            a = np.asarray(frame, dtype=np.int32).reshape(-1, 3)
            cols, inv = np.unique(a, axis=0, return_inverse=True)
            idx = (((cols[:, None, :] - palette_rgb[None, :, :]) ** 2).sum(-1).argmin(1) + 1).astype(np.uint8)
            mapped = idx[inv.ravel()].reshape(frame.size[1], frame.size[0])
            mapped[alpha < 128] = 0
            im = Image.fromarray(mapped)
            im.putpalette(pl)
            return im

        q = [to_pal(f, a) for f, a in zip(frames, alphas)]
        q[0].save(
            out,
            save_all=True,
            append_images=q[1:],
            duration=ms,
            loop=0,
            transparency=0,
            disposal=2,
            optimize=True,
        )
    else:
        pl = opaque_pl

        def to_pal(frame: Image.Image) -> Image.Image:
            """Exact nearest-palette mapping (PIL's default LUT is approximate and shifts the background)."""
            a = np.asarray(frame, dtype=np.int32).reshape(-1, 3)
            cols, inv = np.unique(a, axis=0, return_inverse=True)
            idx = ((cols[:, None, :] - palette_rgb[None, :, :]) ** 2).sum(-1).argmin(1).astype(np.uint8)
            im = Image.fromarray(idx[inv.ravel()].reshape(frame.size[1], frame.size[0]))
            im.putpalette(pl)
            return im

        q = [to_pal(f) for f in frames]
        q[0].save(out, save_all=True, append_images=q[1:], duration=ms, loop=0, optimize=True)

    print(out, q[0].size, len(q), "frames", round(os.path.getsize(out) / 1024), "KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
