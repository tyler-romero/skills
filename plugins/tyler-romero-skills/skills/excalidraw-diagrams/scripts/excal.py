"""Helper library for authoring Excalidraw scenes programmatically from Python."""

import copy
import json
import random

# Core ink and neutral palette
INK = "#1e1e1e"
DARK = "#495057"
GRAY = "#868e96"
LIGHT_GRAY = "#adb5bd"
RULE = "#ced4da"
FAINT = "#e9ecef"
TOKEN_FILL = "#f1f3f5"
CREAM_BG = "#fef9ed"
WHITE_BG = "#ffffff"

# Accent strokes and fills
BLUE = "#a5d8ff"
BLUE_INK = "#1971c2"
BLUE_FILL = "#a5d8ff"
BLUE_SOFT = "#e7f5ff"

GREEN = "#b2f2bb"
DARK_GREEN = "#2f9e44"
GREEN_INK = "#2f9e44"
GREEN_FILL = "#b2f2bb"

ORANGE = "#e8590c"
ORANGE_FILL = "#ffd8a8"
ORANGE_SOFT = "#fff4e6"

YELLOW = "#ffec99"
AMBER = "#f08c00"

RED = "#e03131"
RED_FILL = "#ffc9c9"
SALMON = "#ff8787"

VIOLET = "#7048e8"
VIOLET_FILL = "#e5dbff"

TEAL = "#0c8599"


class Scene:
    """Coordinates and font sizes are authored in output pixels.

    Geometry is divided by `unit` on save, so stroke widths (which stay in Excalidraw's standard
    1/2/4 steps) look heavier relative to text. `exportScale` restores the output size when rendering.

    Text widths use `0.49 * size` per character for Virgil (`fontFamily: 5`) so `@excalidraw/excalidraw`'s
    `exportToBlob` (which trusts stored `element.width`) does not pad left-aligned text with phantom
    right-edge whitespace.
    """

    def __init__(self, seed=7, unit=1.5, rough=1):
        self.rng = random.Random(seed)
        self.rough = rough
        self.unit = unit
        self.elements = []

    def _base(self, kind, x, y, w, h, **kw):
        el = {
            "id": f"{kind}-{len(self.elements)}",
            "type": kind,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "angle": 0,
            "strokeColor": kw.pop("stroke", INK),
            "backgroundColor": kw.pop("bg", "transparent"),
            "fillStyle": kw.pop("fill", "hachure"),
            "strokeWidth": kw.pop("sw", 1),
            "strokeStyle": kw.pop("style", "solid"),
            "roughness": kw.pop("rough", self.rough),
            "opacity": 100,
            "groupIds": [],
            "frameId": None,
            "index": f"a{len(self.elements):04d}",
            "roundness": kw.pop("roundness", None),
            "seed": self.rng.randint(1, 2**31 - 1),
            "version": 1,
            "versionNonce": self.rng.randint(1, 2**31 - 1),
            "isDeleted": False,
            "boundElements": None,
            "updated": 1790380000000,
            "link": None,
            "locked": False,
        }
        el.update(kw)
        self.elements.append(el)
        return el

    def text(self, x, y, s, size=28, color=INK, align="left", valign="top", container=None, **kw):
        """Place text in Virgil (`fontFamily: 5`). For align="center" or "right", x is the center or right edge."""
        lines = s.split("\n")
        w = max(len(line) for line in lines) * size * 0.49
        h = len(lines) * size * 1.25
        if align == "center":
            x -= w / 2
        elif align == "right":
            x -= w
        el = self._base(
            "text", x, y, w, h,
            stroke=color,
            fill="solid",
            text=s,
            originalText=s,
            fontSize=size,
            fontFamily=5,
            textAlign=align,
            verticalAlign=valign,
            containerId=container["id"] if container else None,
            autoResize=True,
            lineHeight=1.25,
            **kw,
        )
        if container:
            container["boundElements"] = (container["boundElements"] or []) + [
                {"type": "text", "id": el["id"]}
            ]
        return el

    def shape(self, kind, x, y, w, h, label=None, size=30, **kw):
        """Rectangle, diamond, or ellipse with an optional centered, bound label."""
        el = self._base(kind, x, y, w, h, **kw)
        if label:
            lines = label.count("\n") + 1
            th = lines * size * 1.25
            self.text(x + w / 2, y + (h - th) / 2, label, size=size, align="center",
                      valign="middle", container=el)
        return el

    def rect(self, x, y, w, h, label=None, **kw):
        kw.setdefault("roundness", {"type": 3})
        return self.shape("rectangle", x, y, w, h, label, **kw)

    def diamond(self, x, y, w, h, label=None, **kw):
        kw.setdefault("roundness", {"type": 2})
        return self.shape("diamond", x, y, w, h, label, **kw)

    def ellipse(self, x, y, w, h, label=None, **kw):
        kw.setdefault("roundness", {"type": 2})
        return self.shape("ellipse", x, y, w, h, label, **kw)

    def line(self, x1, y1, x2, y2, **kw):
        return self._base(
            "line", x1, y1, x2 - x1, y2 - y1,
            points=[[0, 0], [x2 - x1, y2 - y1]],
            lastCommittedPoint=None, startBinding=None, endBinding=None,
            startArrowhead=None, endArrowhead=None, **kw,
        )

    def poly(self, pts, **kw):
        """Open polyline through absolute (x, y) points."""
        x0, y0 = pts[0]
        rel = [[x - x0, y - y0] for x, y in pts]
        xs = [p[0] for p in rel]
        ys = [p[1] for p in rel]
        return self._base(
            "line", x0 + min(xs), y0 + min(ys), max(xs) - min(xs), max(ys) - min(ys),
            points=[[px - min(xs), py - min(ys)] for px, py in rel],
            lastCommittedPoint=None, startBinding=None, endBinding=None,
            startArrowhead=None, endArrowhead=None, **kw,
        )

    def arrow(self, *pts, sw=1, **kw):
        """Arrow through (x, y) points. Three or more points render as a smooth curve."""
        x0, y0 = pts[0]
        rel = [[x - x0, y - y0] for x, y in pts]
        xs = [p[0] for p in rel]
        ys = [p[1] for p in rel]
        if len(pts) > 2:
            kw.setdefault("roundness", {"type": 2})
        return self._base(
            "arrow", x0, y0, max(xs) - min(xs), max(ys) - min(ys),
            sw=sw, points=rel,
            lastCommittedPoint=None, startBinding=None, endBinding=None,
            startArrowhead=None, endArrowhead="arrow", elbowed=False, **kw,
        )

    def save(self, path, bg=WHITE_BG, quiet=False):
        u = self.unit
        scaled_elements = copy.deepcopy(self.elements)
        for el in scaled_elements:
            for k in ("x", "y", "width", "height"):
                el[k] = round(el[k] / u, 2)
            if "points" in el:
                el["points"] = [[round(px / u, 2), round(py / u, 2)] for px, py in el["points"]]
            if "fontSize" in el:
                el["fontSize"] = round(el["fontSize"] / u, 2)
        scene = {
            "type": "excalidraw",
            "version": 2,
            "source": "https://excalidraw.com",
            "elements": scaled_elements,
            "appState": {"viewBackgroundColor": bg, "gridSize": 20, "exportScale": u},
            "files": {},
        }
        with open(path, "w") as f:
            json.dump(scene, f, indent=2, ensure_ascii=False)
            f.write("\n")
        if not quiet:
            print(f"{path}: {len(scaled_elements)} elements")


TightScene = Scene
