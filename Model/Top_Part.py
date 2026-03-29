"""
=============================================================
  3D PRINTABLE ROBOT ENCLOSURE — TOP SHELL GENERATOR
  Engine : trimesh (boolean backend: manifold / blender)
  Units  : mm  |  Origin: geometric centre of outer shell
=============================================================

COORDINATE CONVENTION (right-hand, Z-up):
  +X = right      -X = left
  +Y = rear       -Y = front   ← display is on -Y face
  +Z = top        -Z = bottom  ← open rim is on -Z face

HOW TO USE:
  pip install trimesh manifold3d numpy
  python Model/Top_Part.py
"""

import trimesh
import numpy as np
from trimesh import transformations as tf


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def rotate(mesh, angle_deg, axis):
    """Rotate mesh in-place by angle_deg around axis [x,y,z]."""
    angle_rad = np.radians(angle_deg)
    R = tf.rotation_matrix(angle_rad, np.array(axis, dtype=float))
    mesh.apply_transform(R)
    return mesh


def cylinder_z(radius, height, sections=32):
    """Cylinder aligned along Z (trimesh default)."""
    return trimesh.creation.cylinder(radius=radius, height=height, sections=sections)


def cylinder_y(radius, height, sections=32):
    """Cylinder aligned along Y (rotate Z-cylinder 90° around X)."""
    c = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    return rotate(c, 90, [1, 0, 0])


def box(w, d, h):
    """Box of width(X) × depth(Y) × height(Z), centred at origin."""
    return trimesh.creation.box(extents=[w, d, h])


# ──────────────────────────────────────────────
#  MAIN BUILD
# ──────────────────────────────────────────────

def create_enclosure():
    # ── MASTER DIMENSIONS ──────────────────────
    OW = 60.0    # outer width  (X)
    OD = 40.0    # outer depth  (Y)
    OH = 20.0    # outer height (Z)
    T  = 1.8     # wall thickness

    IW = OW - 2 * T
    ID = OD - 2 * T

    print("=" * 56)
    print("  ROBOT ENCLOSURE TOP SHELL — BUILD LOG")
    print("=" * 56)

    # ── STEP 1 : OUTER SHELL ───────────────────
    print("\n[1/9] Outer shell …")
    shell = box(OW, OD, OH)

    # ── STEP 2 : INNER CAVITY ─────────────────
    print("[2/9] Inner cavity (hollow) …")
    cavity = box(IW, ID, OH - T)
    cavity.apply_translation([0, 0, -T / 2])   # keeps top wall thickness T
    shell = shell.difference(cavity)

    # ── STEP 3 : FRONT FACE — DISPLAY CUTOUT ──
    print("[3/9] Display cutout (front face) …")
    DISP_W   = 38.0
    DISP_H   = 27.0
    DISP_REC = 1.0

    disp = box(DISP_W, DISP_REC + 0.5, DISP_H)
    disp.apply_translation([
        0,
        -(OD/2 - DISP_REC/2),
        0
    ])
    shell = shell.difference(disp)

    # ── STEP 4 : TOP FACE — MICROPHONE HOLE ───
    print("[4/9] Microphone hole (top face) …")
    MIC_D = 4.0
    mic = cylinder_z(radius=MIC_D/2, height=T + 2)
    mic.apply_translation([
        -OW/2 + 12,
        -OD/2 + 8,
        OH/2
    ])
    shell = shell.difference(mic)

    # ── STEP 5 : TOP FACE — M2 SCREW BOSSES ──
    print("[5/9] M2 screw bosses (top face, 4×) …")
    BOSS_OD    = 3.0
    BOSS_ID    = 1.5
    BOSS_DEPTH = 2.0

    inner_corners = [
        (-IW/2, -ID/2), (IW/2, -ID/2),
        (-IW/2,  ID/2), (IW/2,  ID/2),
    ]

    for bx, by in inner_corners:
        bz = OH/2 - T - BOSS_DEPTH/2

        outer_boss = cylinder_z(radius=BOSS_OD/2, height=BOSS_DEPTH, sections=32)
        outer_boss.apply_translation([bx, by, bz])
        shell = shell.union(outer_boss)

        inner_boss = cylinder_z(radius=BOSS_ID/2, height=BOSS_DEPTH + 1, sections=16)
        inner_boss.apply_translation([bx, by, bz])
        shell = shell.difference(inner_boss)

    # ── STEP 6 : LEFT FACE — SPEAKER GRILLE ───
    print("[6/9] Speaker grille (left face, 5 slots) …")
    N_SLOTS = 5
    SLOT_W  = 2.0
    SLOT_H  = 10.0
    spacing = ID / (N_SLOTS + 1)

    for i in range(N_SLOTS):
        sy = -ID/2 + spacing * (i + 1)
        slot = box(T + 2, SLOT_W, SLOT_H)
        slot.apply_translation([-OW/2, sy, 0])
        shell = shell.difference(slot)

    # ── STEP 7 : REAR FACE — CABLE PASS-THROUGHS ──
    print("[7/9] Cable pass-through holes (rear face, 2×) …")
    CABLE_D = 4.0
    CABLE_Z = OH/2 - 8

    for cx in [-OW/2 + 10, OW/2 - 10]:
        hole = cylinder_y(radius=CABLE_D/2, height=T + 2, sections=32)
        hole.apply_translation([cx, OD/2, CABLE_Z])
        shell = shell.difference(hole)

    # ── STEP 8 : BOTTOM RIM — SNAP-FIT TABS ───
    print("[8/9] Snap-fit tabs (bottom rim, 4×) …")
    TW, TD, TH = 4.0, 3.0, 1.5
    tab_xs = [-IW/4, IW/4]

    # Front tabs
    for tx in tab_xs:
        tab = box(TW, TD, TH)
        tab.apply_translation([tx, -OD/2 - TD/2, -OH/2 - TH/2])
        shell = shell.union(tab)

    # Rear tabs
    for tx in tab_xs:
        tab = box(TW, TD, TH)
        tab.apply_translation([tx, OD/2 + TD/2, -OH/2 - TH/2])
        shell = shell.union(tab)

    # ── STEP 9 : BOTTOM RIM — ALIGNMENT PIN HOLES ──
    print("[9/9] Alignment pin holes (bottom rim, 4×) …")
    PIN_D     = 2.0
    PIN_DEPTH = 2.0

    for px, py in inner_corners:
        pin = cylinder_z(radius=PIN_D/2, height=PIN_DEPTH + 1, sections=16)
        pin.apply_translation([px, py, -OH/2 + PIN_DEPTH/2])
        shell = shell.difference(pin)

    # ── FINALIZE ───────────────────────────────
    print("\n[✓] Cleaning mesh …")
    shell.merge_vertices()

    # Safe degenerate face removal (works on all recent trimesh versions)
    try:
        # Preferred modern way
        mask = shell.nondegenerate_faces()
        shell.update_faces(mask)
    except Exception:
        # Fallback: use process() which also removes duplicates/degenerates
        shell = shell.process()

    shell.remove_unreferenced_vertices()
    shell.fix_normals()

    return shell


# ──────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────

def main():
    enclosure = create_enclosure()

    # ── STATS ──────────────────────────────────
    bounds = enclosure.bounds
    dims   = bounds[1] - bounds[0]
    print()
    print("─" * 40)
    print("  MODEL STATISTICS")
    print("─" * 40)
    print(f"  Vertices   : {len(enclosure.vertices):,}")
    print(f"  Faces      : {len(enclosure.faces):,}")
    print(f"  Volume     : {enclosure.volume:.2f} mm³")
    print(f"  Bounding   : {dims[0]:.1f} × {dims[1]:.1f} × {dims[2]:.1f} mm")
    print(f"  Watertight : {enclosure.is_watertight}")

    # ── EXPORT ─────────────────────────────────
    outfile = "robot_enclosure_top_shell.stl"
    enclosure.export(outfile)
    print()
    print(f"  ✅ Saved → {outfile}")
    print("─" * 40)

    print("\n  FEATURES INCLUDED")
    print("  ✔ 60 × 40 × 20 mm outer shell, T=1.8 mm")
    print("  ✔ Top wall solid, bottom rim open")
    print("  ✔ Display cutout 38 × 27 mm (front face, 1 mm recessed)")
    print("  ✔ Mic hole 4 mm dia (top face)")
    print("  ✔ 4× M2 screw bosses")
    print("  ✔ 5-slot speaker grille (left face)")
    print("  ✔ 2× cable holes (rear face)")
    print("  ✔ 4× snap-fit tabs")
    print("  ✔ 4× alignment pin holes")
    print()
    print("  🖨  Slice at 0.2 mm layers, 20 % infill, no supports needed")

    # ── OPTIONAL PREVIEW ───────────────────────
    try:
        enclosure.show()
    except Exception as e:
        print(f"  ⚠  Preview unavailable: {e}")


if __name__ == "__main__":
    main()