"""
=============================================================
  3D PRINTABLE ROBOT ENCLOSURE — BOTTOM SHELL GENERATOR
  Engine : trimesh (boolean backend: manifold)
  Units  : mm  |  Origin: geometric centre of outer shell
=============================================================

COORDINATE CONVENTION (right-hand, Z-up):
  +X = right      -X = left
  +Y = rear       -Y = front
  +Z = top        ← open top rim for mating with top shell
  -Z = bottom     ← solid floor / exterior base
"""

import sys
import subprocess
import numpy as np
import trimesh
from trimesh import transformations as tf

# ── Optional imports for text pipeline ──────────────────────
try:
    from PIL import Image, ImageFont, ImageDraw
    from skimage import measure
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from shapely import affinity as shaff
    _TEXT_AVAILABLE = True
except ImportError as e:
    _TEXT_AVAILABLE = False
    print(f"⚠  Text pipeline unavailable: {e}")
    print("   Install with: pip install Pillow scikit-image shapely")


# ──────────────────────────────────────────────────────────────
#  GEOMETRY HELPERS
# ──────────────────────────────────────────────────────────────

def rotate(mesh, angle_deg, axis):
    """Rotate mesh around axis by angle_deg (degrees)."""
    R = tf.rotation_matrix(np.radians(angle_deg), np.array(axis, dtype=float))
    mesh.apply_transform(R)
    return mesh


def box(w, d, h):
    """Axis-aligned box W(X) × D(Y) × H(Z), centred at origin."""
    return trimesh.creation.box(extents=[w, d, h])


def cylinder_z(radius, height, sections=32):
    """Cylinder along Z-axis, centred at origin."""
    return trimesh.creation.cylinder(radius=radius, height=height, sections=sections)


def cylinder_x(radius, height, sections=32):
    """Cylinder along X-axis."""
    c = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    return rotate(c, 90, [0, 1, 0])


def cylinder_y(radius, height, sections=32):
    """Cylinder along Y-axis."""
    c = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    return rotate(c, 90, [1, 0, 0])


# ──────────────────────────────────────────────────────────────
#  TEXT → 3D EMBOSS HELPER (improved robustness)
# ──────────────────────────────────────────────────────────────

def make_embossed_text(text, text_height_mm=3.0, raise_mm=0.4, render_scale=20):
    if not _TEXT_AVAILABLE:
        return None

    # Find a bold font
    try:
        out = subprocess.run(['fc-list', '--format=%{file}\n'], 
                           capture_output=True, text=True, timeout=5).stdout.split('\n')
    except Exception:
        out = []

    priority = ['Poppins-Bold.ttf', 'LiberationSans-Bold.ttf', 
                'DejaVuSans-Bold.ttf', 'Arial-Bold.ttf']
    font_path = None
    for p in priority:
        for f in out:
            if p.lower() in f.lower():
                font_path = f.strip()
                break
        if font_path:
            break
    if not font_path:
        print("  ⚠  No suitable TTF font found — skipping embossed text.")
        return None

    # Rasterise text
    px_font = int(text_height_mm * render_scale * 3.5)
    img_w = max(800, px_font * len(text) + 100)
    img_h = px_font * 4
    img = Image.new('L', (img_w, img_h), 0)
    draw = ImageDraw.Draw(img)

    try:
        fnt = ImageFont.truetype(font_path, size=px_font)
    except Exception:
        fnt = ImageFont.load_default()

    draw.text((20, img_h // 4), text, font=fnt, fill=255)
    arr = np.array(img)

    # Crop to content
    rows = np.any(arr > 100, axis=1)
    cols = np.any(arr > 100, axis=0)
    if not rows.any():
        return None
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    arr_crop = arr[r0:r1+1, c0:c1+1]

    # Contours → polygons
    contours = measure.find_contours(arr_crop, level=128)
    polys = []
    for c in contours:
        if len(c) < 6:
            continue
        pts = c[:, ::-1]  # (row, col) → (x, y)
        try:
            p = Polygon(pts).buffer(0)
            if p.is_valid and p.area > 10:
                polys.append(p)
        except Exception:
            pass

    if not polys:
        return None

    combined = unary_union(polys)
    # Scale to mm and centre (flip Y for image → 3D)
    mm_per_px = text_height_mm / (r1 - r0)
    scaled = shaff.scale(combined, xfact=mm_per_px, yfact=-mm_per_px, origin=(0, 0))
    cx, cy = scaled.centroid.coords[0]
    centred = shaff.translate(scaled, -cx, -cy)

    # Extrude
    geom_list = [centred] if isinstance(centred, Polygon) else list(centred.geoms)
    meshes = []
    for g in geom_list:
        if g.is_valid and g.area > 1e-4:
            try:
                m = trimesh.creation.extrude_polygon(g, height=raise_mm)
                meshes.append(m)
            except Exception:
                pass

    if not meshes:
        return None
    return trimesh.util.concatenate(meshes)


# ──────────────────────────────────────────────────────────────
#  MAIN BUILD
# ──────────────────────────────────────────────────────────────

def create_bottom_shell():
    OW = 60.0    # outer width  (X)
    OD = 40.0    # outer depth  (Y)
    OH = 20.0    # outer height (Z)
    T  = 1.8     # wall / floor thickness

    IW = OW - 2 * T
    ID = OD - 2 * T

    print("=" * 56)
    print("  ROBOT ENCLOSURE BOTTOM SHELL — BUILD LOG")
    print("=" * 56)

    # [1] Outer shell
    print("\n[1/9] Outer shell …")
    shell = box(OW, OD, OH)

    # [2] Inner cavity (preserves floor thickness T)
    print("[2/9] Inner cavity (hollow) …")
    cavity = box(IW, ID, OH - T)
    cavity.apply_translation([0, 0, T / 2])
    shell = shell.difference(cavity)

    # [3] USB-C cutout (right face)
    print("[3/9] USB-C cutout (right face) …")
    USBC_W = 10.0
    USBC_H = 4.0
    USBC_Z = -OH/2 + 7.0   # centre Z (5 mm from bottom + half height)

    usbc = box(T + 2, USBC_W, USBC_H)
    usbc.apply_translation([OW/2, 0, USBC_Z])
    shell = shell.difference(usbc)

    # [4] Battery tray
    print("[4/9] Battery tray (interior floor) …")
    TRAY_W = 50.0
    TRAY_D = 30.0
    TRAY_WALL_H = 8.0
    tray_cy = ID/2 - 4 - TRAY_D/2
    tray_cz = -OH/2 + T + TRAY_WALL_H/2

    tray_outer = box(TRAY_W, TRAY_D, TRAY_WALL_H)
    tray_outer.apply_translation([0, tray_cy, tray_cz])

    tray_inner = box(TRAY_W - 2*T, TRAY_D - 2*T, TRAY_WALL_H + 2)
    tray_inner.apply_translation([0, tray_cy, tray_cz + 1])

    tray_hollow = tray_outer.difference(tray_inner)
    shell = shell.union(tray_hollow)

    # [5] PCB standoffs
    print("[5/9] PCB standoffs (2×) …")
    SO_OD = 4.0
    SO_H = 5.0
    SO_HOLE = 1.5
    so_cz = -OH/2 + T + SO_H/2

    so_positions = [
        (-IW/2 + 12, -ID/2 + 12),
        ( IW/2 - 12, -ID/2 + 12),
    ]

    for sx, sy in so_positions:
        post = cylinder_z(radius=SO_OD/2, height=SO_H)
        post.apply_translation([sx, sy, so_cz])
        shell = shell.union(post)

        hole = cylinder_z(radius=SO_HOLE, height=SO_H + 1)
        hole.apply_translation([sx, sy, so_cz])
        shell = shell.difference(hole)

    # [6] Snap-fit receiver slots (top rim)
    print("[6/9] Snap-fit receiver slots (top rim, 4×) …")
    REC_W = 4.2
    REC_D = 3.2
    REC_H = 1.8

    for rx in [-IW/4, IW/4]:
        # Front
        slot = box(REC_W, REC_D + 2, REC_H)
        slot.apply_translation([rx, -OD/2 + REC_D/2, OH/2 - REC_H/2])
        shell = shell.difference(slot)

        # Rear
        slot = box(REC_W, REC_D + 2, REC_H)
        slot.apply_translation([rx, OD/2 - REC_D/2, OH/2 - REC_H/2])
        shell = shell.difference(slot)

    # [7] Alignment pins (top rim)
    print("[7/9] Alignment pins (top rim, 4×) …")
    PIN_D = 2.0
    PIN_H = 2.5
    pin_cz = OH/2 + PIN_H/2

    inner_corners = [
        (-IW/2, -ID/2), (IW/2, -ID/2),
        (-IW/2,  ID/2), (IW/2,  ID/2),
    ]

    for px, py in inner_corners:
        pin = cylinder_z(radius=PIN_D/2, height=PIN_H)
        pin.apply_translation([px, py, pin_cz])
        shell = shell.union(pin)

    # [8] Rubber pad recesses (bottom exterior)
    print("[8/9] Rubber pad recesses (bottom exterior, 4×) …")
    PAD_D = 8.0
    PAD_DEPTH = 0.8
    PAD_INSET = 6.0

    pad_positions = [
        (-OW/2 + PAD_INSET, -OD/2 + PAD_INSET),
        ( OW/2 - PAD_INSET, -OD/2 + PAD_INSET),
        (-OW/2 + PAD_INSET,  OD/2 - PAD_INSET),
        ( OW/2 - PAD_INSET,  OD/2 - PAD_INSET),
    ]

    for ppx, ppy in pad_positions:
        pad = cylinder_z(radius=PAD_D/2, height=PAD_DEPTH + 0.5)
        pad.apply_translation([ppx, ppy, -OH/2 + PAD_DEPTH/2])
        shell = shell.difference(pad)

    # [9] Embossed text
    print("[9/9] Embossed text 'JK v1' (bottom exterior) …")
    if _TEXT_AVAILABLE:
        text_mesh = make_embossed_text('JK v1', text_height_mm=3.0, raise_mm=0.4)
        if text_mesh is not None:
            text_mesh.apply_translation([0, 0, -OH/2])
            shell = shell.union(text_mesh)
            print("    ✓ Embossed text added.")
        else:
            print("    ⚠  Text generation failed — skipped.")
    else:
        print("    ⚠  Text dependencies missing — skipped.")

    # ── FINALIZE ──────────────────────────────────────────────
    print("\n[✓] Cleaning mesh …")
    shell.merge_vertices()

    # Robust degenerate face removal
    try:
        mask = shell.nondegenerate_faces()
        shell.update_faces(mask)
    except Exception:
        print("    → Using process() fallback for cleanup")
        shell = shell.process()

    shell.remove_unreferenced_vertices()
    shell.fix_normals()

    return shell


# ──────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────

def main():
    shell = create_bottom_shell()

    bounds = shell.bounds
    dims = bounds[1] - bounds[0]

    print()
    print("─" * 48)
    print("  MODEL STATISTICS")
    print("─" * 48)
    print(f"  Vertices   : {len(shell.vertices):,}")
    print(f"  Faces      : {len(shell.faces):,}")
    print(f"  Volume     : {shell.volume:.2f} mm³")
    print(f"  Bounding   : {dims[0]:.1f} × {dims[1]:.1f} × {dims[2]:.1f} mm")
    print(f"  Watertight : {shell.is_watertight}")

    outfile = "robot_enclosure_bottom_shell.stl"
    shell.export(outfile)
    print()
    print(f"  ✅ Saved → {outfile}")
    print("─" * 48)

    print("\n  FEATURES INCLUDED")
    print("  ✔ Solid floor, open top rim")
    print("  ✔ USB-C slot 10×4 mm (right face)")
    print("  ✔ Battery tray 50×30 mm with 8 mm walls")
    print("  ✔ 2× M2 PCB standoffs")
    print("  ✔ 4× snap-fit receiver slots")
    print("  ✔ 4× alignment pins")
    print("  ✔ 4× rubber pad recesses")
    print("  ✔ Embossed 'JK v1' text (if dependencies met)")

    print("\n  🖨  Recommended: Print UPSIDE DOWN (open rim on build plate)")
    print("     0.2 mm layers, 20% infill, no supports needed")

    try:
        shell.show()
    except Exception as e:
        print(f"  ⚠  Preview unavailable: {e}")


if __name__ == "__main__":
    main()