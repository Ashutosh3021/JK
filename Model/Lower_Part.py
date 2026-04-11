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

FIXES vs original:
  1. Snap-fit receiver slots were cut INWARD from the inner wall face.
     The top shell tabs are on the OUTSIDE of the body. Opposite
     directions → they never engaged. Receivers now cut from the
     OUTSIDE face to match the cantilevered tab nub on the top shell.
     Pocket depth/width/height tuned for 0.3–0.4 mm FDM clearance.
  2. Alignment pins were at exactly IW/2 corners but Top shell M2 bosses
     were inset 3 mm. Pins moved to same inset corners so they don't
     clash with the boss cylinders.
  3. Alignment pin diameter had zero tolerance with top shell holes.
     Pins kept at 2.0 mm dia, top shell holes expanded (see Top_Part.py).
  4. USB-C cutout depth was T+2 which is correct, but Z centre was
     slightly low. Recalculated to proper centre above floor.
  5. PCB standoff holes were 1.5 mm radius (too large for M2 self-tap).
     Corrected to 1.1 mm radius (2.2 mm dia) for M2 thread-forming.
  6. Battery tray inner clearance was T on all sides but tray was
     union'd then inner carved — order was correct but inner height
     was OH-T leaving the tray base merged with shell floor. Fixed
     by computing tray_cz properly from floor level up.
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


def safe_boolean(mesh_a, mesh_b, operation):
    """Wrapper with manifold engine fallback."""
    try:
        if operation == 'difference':
            return mesh_a.difference(mesh_b, engine='manifold')
        elif operation == 'union':
            return mesh_a.union(mesh_b, engine='manifold')
    except Exception:
        pass
    if operation == 'difference':
        return mesh_a.difference(mesh_b)
    return mesh_a.union(mesh_b)


# ──────────────────────────────────────────────────────────────
#  TEXT → 3D EMBOSS HELPER (unchanged from original)
# ──────────────────────────────────────────────────────────────

def make_embossed_text(text, text_height_mm=3.0, raise_mm=0.4, render_scale=20):
    if not _TEXT_AVAILABLE:
        return None

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

    rows = np.any(arr > 100, axis=1)
    cols = np.any(arr > 100, axis=0)
    if not rows.any():
        return None
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    arr_crop = arr[r0:r1+1, c0:c1+1]

    contours = measure.find_contours(arr_crop, level=128)
    polys = []
    for c in contours:
        if len(c) < 6:
            continue
        pts = c[:, ::-1]
        try:
            p = Polygon(pts).buffer(0)
            if p.is_valid and p.area > 10:
                polys.append(p)
        except Exception:
            pass

    if not polys:
        return None

    combined = unary_union(polys)
    mm_per_px = text_height_mm / (r1 - r0)
    scaled = shaff.scale(combined, xfact=mm_per_px, yfact=-mm_per_px, origin=(0, 0))
    cx, cy = scaled.centroid.coords[0]
    centred = shaff.translate(scaled, -cx, -cy)

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

    # Inner corners — used for alignment pins & standoffs
    # FIX: inset 3 mm to match Top_Part boss positions
    INSET = 3.0
    inner_corners = [
        (-IW / 2 + INSET, -ID / 2 + INSET),
        ( IW / 2 - INSET, -ID / 2 + INSET),
        (-IW / 2 + INSET,  ID / 2 - INSET),
        ( IW / 2 - INSET,  ID / 2 - INSET),
    ]

    print("=" * 60)
    print("  ROBOT ENCLOSURE BOTTOM SHELL — BUILD LOG (FIXED)")
    print("=" * 60)

    # [1] Outer shell
    print("\n[1/9] Outer shell …")
    shell = box(OW, OD, OH)

    # [2] Inner cavity (preserves floor thickness T)
    print("[2/9] Inner cavity (hollow) …")
    cavity = box(IW, ID, OH - T)
    cavity.apply_translation([0, 0, T / 2])
    shell = safe_boolean(shell, cavity, 'difference')

    # [3] USB-C cutout (right face, +X)
    # FIX: Z centre recalculated from actual floor position
    print("[3/9] USB-C cutout (right face) …  [FIXED Z centre]")
    USBC_W  = 10.0   # opening width  (Y)
    USBC_H  =  4.0   # opening height (Z)
    FLOOR_Z = -OH / 2 + T         # actual inner floor Z
    USBC_Z  = FLOOR_Z + 7.0 + USBC_H / 2   # FIX: 7 mm from floor to bottom of cutout

    usbc = box(T + 2, USBC_W, USBC_H)
    usbc.apply_translation([OW / 2, 0, USBC_Z])
    shell = safe_boolean(shell, usbc, 'difference')

    # [4] Battery tray
    # FIX: tray_cz now measured from floor up so tray doesn't merge into floor
    print("[4/9] Battery tray (interior floor) …  [FIXED Z position]")
    TRAY_W      = 50.0
    TRAY_D      = 30.0
    TRAY_WALL_H =  8.0
    TRAY_T      =  1.2   # tray wall thickness

    tray_cy = ID / 2 - 4 - TRAY_D / 2
    # FIX: sit tray base ON the inner floor, not floating
    tray_cz = FLOOR_Z + TRAY_WALL_H / 2

    tray_outer = box(TRAY_W, TRAY_D, TRAY_WALL_H)
    tray_outer.apply_translation([0, tray_cy, tray_cz])

    tray_inner = box(TRAY_W - 2 * TRAY_T, TRAY_D - 2 * TRAY_T, TRAY_WALL_H + 2)
    tray_inner.apply_translation([0, tray_cy, tray_cz + TRAY_T])

    tray_hollow = safe_boolean(tray_outer, tray_inner, 'difference')
    shell = safe_boolean(shell, tray_hollow, 'union')

    # [5] PCB standoffs
    # FIX: hole radius corrected to 1.1 mm (M2 self-tap, was 1.5 = too big)
    print("[5/9] PCB standoffs (2×) …  [FIXED M2 hole dia]")
    SO_OD   = 4.0
    SO_H    = 5.0
    SO_HOLE = 1.1    # FIX: was 1.5 (M3), now 1.1 (M2 self-tap)
    so_cz   = FLOOR_Z + SO_H / 2

    so_positions = [
        (-IW / 2 + 12, -ID / 2 + 12),
        ( IW / 2 - 12, -ID / 2 + 12),
    ]

    for sx, sy in so_positions:
        post = cylinder_z(radius=SO_OD / 2, height=SO_H)
        post.apply_translation([sx, sy, so_cz])
        shell = safe_boolean(shell, post, 'union')

        hole = cylinder_z(radius=SO_HOLE, height=SO_H + 1)
        hole.apply_translation([sx, sy, so_cz])
        shell = safe_boolean(shell, hole, 'difference')

    # [6] Snap-fit receiver pockets (top rim)
    # FIX: original slots cut INWARD from inner face — opposite to top shell's
    #      outward-pointing tabs. Receivers now cut from OUTSIDE of front/rear
    #      walls to match the cantilevered nub tabs on the top shell.
    #
    # Pocket geometry to match top shell nub:
    #   NUB_H = 0.7 mm, NUB_Z = 1.0 mm → pocket adds 0.3 mm clearance each side
    print("[6/9] Snap-fit receiver pockets (top rim, 4×) …  [FIXED direction]")

    POC_W   = 5.4    # tab width 5.0 + 0.4 clearance (X)
    POC_H   = 1.3    # nub height 0.7 + 0.6 mm pocket height (Z)
    POC_D   = 1.1    # nub proud 0.7 + 0.4 clearance (Y depth into wall)
    POC_ZOF = 0.5    # match nub Z offset from rim

    tab_xs = [-IW / 4, IW / 4]

    for tx in tab_xs:
        # Front pocket — cut from -Y outer face inward
        poc = box(POC_W, POC_D + 1, POC_H)
        poc.apply_translation([tx, -(OD / 2 - POC_D / 2), OH / 2 - POC_ZOF - POC_H / 2])
        shell = safe_boolean(shell, poc, 'difference')

        # Rear pocket — cut from +Y outer face inward
        poc = box(POC_W, POC_D + 1, POC_H)
        poc.apply_translation([tx, OD / 2 - POC_D / 2, OH / 2 - POC_ZOF - POC_H / 2])
        shell = safe_boolean(shell, poc, 'difference')

    # [7] Alignment pins (top rim)
    # FIX: moved to same INSET corners as top shell bosses so pins don't
    #      conflict with the boss cylinders when shells mate.
    print("[7/9] Alignment pins (top rim, 4×) …  [FIXED position]")
    PIN_D  = 2.0
    PIN_H  = 2.5
    pin_cz = OH / 2 + PIN_H / 2

    for px, py in inner_corners:
        pin = cylinder_z(radius=PIN_D / 2, height=PIN_H)
        pin.apply_translation([px, py, pin_cz])
        shell = safe_boolean(shell, pin, 'union')

    # [8] Rubber pad recesses (bottom exterior)
    print("[8/9] Rubber pad recesses (bottom exterior, 4×) …")
    PAD_D     = 8.0
    PAD_DEPTH = 0.8
    PAD_INSET = 6.0

    pad_positions = [
        (-OW / 2 + PAD_INSET, -OD / 2 + PAD_INSET),
        ( OW / 2 - PAD_INSET, -OD / 2 + PAD_INSET),
        (-OW / 2 + PAD_INSET,  OD / 2 - PAD_INSET),
        ( OW / 2 - PAD_INSET,  OD / 2 - PAD_INSET),
    ]

    for ppx, ppy in pad_positions:
        pad = cylinder_z(radius=PAD_D / 2, height=PAD_DEPTH + 0.5)
        pad.apply_translation([ppx, ppy, -OH / 2 + PAD_DEPTH / 2])
        shell = safe_boolean(shell, pad, 'difference')

    # [9] Embossed text
    print("[9/9] Embossed text 'JK v1' (bottom exterior) …")
    if _TEXT_AVAILABLE:
        text_mesh = make_embossed_text('JK v1', text_height_mm=3.0, raise_mm=0.4)
        if text_mesh is not None:
            text_mesh.apply_translation([0, 0, -OH / 2])
            shell = safe_boolean(shell, text_mesh, 'union')
            print("    ✓ Embossed text added.")
        else:
            print("    ⚠  Text generation failed — skipped.")
    else:
        print("    ⚠  Text dependencies missing — skipped.")

    # ── FINALIZE ──────────────────────────────────────────────
    print("\n[✓] Cleaning mesh …")
    shell.merge_vertices()
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
    dims   = bounds[1] - bounds[0]

    print()
    print("─" * 50)
    print("  MODEL STATISTICS")
    print("─" * 50)
    print(f"  Vertices   : {len(shell.vertices):,}")
    print(f"  Faces      : {len(shell.faces):,}")
    print(f"  Volume     : {shell.volume:.2f} mm³")
    print(f"  Bounding   : {dims[0]:.1f} × {dims[1]:.1f} × {dims[2]:.1f} mm")
    print(f"  Watertight : {shell.is_watertight}")

    outfile = "robot_enclosure_bottom_shell.stl"
    shell.export(outfile)
    print()
    print(f"  ✅ Saved → {outfile}")
    print("─" * 50)

    print("\n  FEATURES (all fixed)")
    print("  ✔ Solid floor, open top rim")
    print("  ✔ USB-C slot 10×4 mm (right face), Z-centre fixed        [FIXED]")
    print("  ✔ Battery tray 50×30 mm, tray base on floor              [FIXED]")
    print("  ✔ 2× M2 PCB standoffs, hole dia 2.2 mm                   [FIXED]")
    print("  ✔ 4× snap-fit pockets cut from OUTSIDE (match top tabs)  [FIXED]")
    print("  ✔ 4× alignment pins at inset corners (match top bosses)  [FIXED]")
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
