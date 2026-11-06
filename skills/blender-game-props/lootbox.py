# Loot box (gab, 2026-11-01) from Dante's reference (v2, closer to it): a chunky cream box. The lid
# has two big orange bumpers covering its left and right thirds (rivets on their faces), a dark grey
# disc on top with a glowing orange ring, grey straps at the top's front and back edges and a grey
# latch hanging over the seam. The body has a raised front plate with a real carrot on it (a tapered
# cone with ridges and three leaves), orange bands up the back corners, grey corner brackets and a
# grey bottom rim. A glowing orange seam runs between lid and body; the inside glows when it opens.
# NewLua pack style: gradient atlas (slot 0 M_GradientTexture), glowing parts in slot 1 (M_GradientGlow).
# Two meshes so the game can swing the lid open:
#   SM_LootBox_Base  pivot at the bottom centre, front -Y, 1.0 x 0.9 x 0.58 m
#   SM_LootBox_Lid   pivot ON THE HINGE (the body's back top edge): rotate about X to open
#   exec(open(r"<skills>/blender-game-props/lootbox.py").read())
#   build_lootbox()
# --- skill file finder: works for manual installs (~/.claude/skills) and plugin installs ---
def _skill(rel):
    import os, glob
    roots = [os.environ.get("CLAUDE_BLENDER_SKILLS", ""), os.path.expanduser("~/.claude/skills")]
    roots += sorted(glob.glob(os.path.expanduser("~/.claude/plugins/**/skills"), recursive=True),
                    key=os.path.getmtime, reverse=True)
    for r in roots:
        if r and os.path.exists(os.path.join(r, rel)):
            os.environ["CLAUDE_BLENDER_SKILLS"] = r   # remember it for the next scripts
            return os.path.join(r, rel)
    raise FileNotFoundError("Blender skill file not found: %s (set the CLAUDE_BLENDER_SKILLS env var "
                            "to the folder that holds blender-game-props)" % rel)
# --- end skill file finder ---

import bpy, bmesh, math
from mathutils import Vector, Matrix

exec(open(_skill("blender-game-props/gates2.py")).read())
exec(open(_skill("blender-game-props/mailbox.py")).read())

LB_ORANGE = c0(10, 0.88, 0.95)      # bumpers, back bands
LB_CARROT = c0(8, 0.92, 0.99)       # the carrot
LB_RIDGE = c0(8, 0.88, 0.91)        # the carrot's ridges, darker
LB_LEAF = c0(9, 0.90, 0.99)
LB_CREAM = c1(9, 0.79, 0.826)
LB_CREAM_L = c1(9, 0.80, 0.828)    # the front plate, a touch lighter
LB_CREAM_D = c1(9, 0.765, 0.795)    # the groove round the plate
LB_METAL = c1(6, 0.72, 0.79)
LB_RIVET = c1(6, 0.76, 0.81)
LB_GLOW = c0(8, 0.93, 0.955)        # glow slot: deep orange (the brighter ends read yellow)

W, D, H = 1.0, 0.9, 0.58            # body (to the seam)
LID_H = 0.36
SOFT = dict(cuts=3, power=8.0)      # crisp boxes with softly rounded edges


def glow_part(bm, fn):
    t = bmesh.new()
    fn(t)
    for f in t.faces:
        f.material_index = 1
    merge(bm, t)


def shaped(bm, size, col, profile, rot, at, cuts=5, power=2.4, flat=1.0):
    """An ellipsoid-ish rbox along Z whose X/Y width follows profile(t) (t 0 bottom .. 1 top),
    squashed in Y by flat, turned rot degrees about Y (the front plane) and moved to at."""
    t = bmesh.new()
    rbox(t, (0, 0, 0), size, col, cuts=cuts, power=power)
    h = size[2] / 2
    for v in t.verts:
        k = profile(min(max((v.co.z + h) / (2 * h), 0.0), 1.0))
        v.co.x *= k
        v.co.y *= k * flat
    bmesh.ops.rotate(t, cent=Vector((0, 0, 0)), matrix=Matrix.Rotation(math.radians(rot), 3, 'Y'), verts=t.verts)
    bmesh.ops.translate(t, vec=Vector(at), verts=t.verts)
    merge(bm, t)


def carrot(bm, center, L=0.27, tilt=-32.0):
    """The front emblem: a carrot pointing down-left with ridges and three leaves on top."""
    R = Matrix.Rotation(math.radians(tilt), 3, 'Y')
    c = Vector(center)
    shaped(bm, (0.13, 0.08, L), LB_CARROT, lambda t: 0.1 + 0.9 * min(1.0, t ** 0.6 * 1.08), tilt, c, flat=0.6)
    # ridges across the front of the body
    for t in (0.35, 0.55, 0.75):
        w = 0.13 * (0.1 + 0.9 * t ** 0.6) * 0.55
        p = c + R @ Vector((0.012, 0, (t - 0.5) * L))
        p.y -= 0.022 * (0.4 + 0.6 * t)
        shaped(bm, (w, 0.02, 0.014), LB_RIDGE, lambda s: 1.0, tilt + 90 - 90, p, cuts=2, power=2.2)
    # three leaves fanned out from the top
    top = c + R @ Vector((0, 0, L / 2 - 0.01))
    for a, length in ((-38, 0.11), (0, 0.13), (38, 0.11)):
        leaf_rot = tilt + a
        base = top + Matrix.Rotation(math.radians(leaf_rot), 3, 'Y') @ Vector((0, 0, length / 2 - 0.01))
        shaped(bm, (0.06, 0.035, length), LB_LEAF, lambda t: 0.2 + 0.8 * math.sin(math.pi * min(t * 1.05, 1.0)) ** 0.8, leaf_rot, base, cuts=4, power=2.2, flat=0.7)


def torus(bm, center, R, r, col, n=32, m=8):
    """Quad torus lying flat (axis Z)."""
    t = bmesh.new()
    rings = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ring = []
        for j in range(m):
            b = 2 * math.pi * j / m
            p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
            ring.append(t.verts.new(p + Vector(center)))
        rings.append(ring)
    for i in range(n):
        for j in range(m):
            a, b = rings[i][j], rings[i][(j + 1) % m]
            c, d = rings[(i + 1) % n][(j + 1) % m], rings[(i + 1) % n][j]
            t.faces.new((a, b, c, d))
    uv_part(t, col)
    merge(bm, t)


def rivet(bm, c, s=0.035):
    rbox(bm, c, (s, s, s), LB_RIVET, cuts=2, power=2.2)


def body(bm):
    fy = -D / 2
    # grey bottom rim and the cream box
    rbox(bm, (0, 0, 0.03), (W - 0.02, D - 0.02, 0.06), LB_METAL, **SOFT)
    rbox(bm, (0, 0, 0.31), (W - 0.04, D - 0.04, 0.52), LB_CREAM, **SOFT)
    # the front plate: a darker groove round a lighter raised plate
    rbox(bm, (0, fy + 0.01, 0.3), (0.66, 0.03, 0.42), LB_CREAM_D, **SOFT)
    rbox(bm, (0, fy - 0.004, 0.3), (0.62, 0.03, 0.38), LB_CREAM_L, **SOFT)
    # orange bands up the back corners
    for sx in (-1, 1):
        rbox(bm, (sx * (W / 2 - 0.07), D / 2 - 0.07, 0.31), (0.16, 0.16, 0.46), LB_ORANGE, **SOFT)
    # grey corner brackets with rivets on their outer faces
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (W / 2 - 0.08), sy * (D / 2 - 0.08)
            rbox(bm, (cx, cy, 0.1), (0.2, 0.2, 0.2), LB_METAL, **SOFT)
            rivet(bm, (cx + sx * 0.1, cy, 0.11))
            rivet(bm, (cx, cy + sy * 0.1, 0.11))
    # the carrot on the plate
    carrot(bm, (0.0, fy - 0.035, 0.27))
    # the glowing seam all round, and the glowing inside (seen when the lid opens)
    glow_part(bm, lambda t: rbox(t, (0, 0, H - 0.012), (W - 0.07, D - 0.07, 0.03), LB_GLOW, power=8.0))
    glow_part(bm, lambda t: rbox(t, (0, 0, H - 0.005), (W - 0.2, D - 0.2, 0.02), LB_GLOW, power=8.0))


def lid(bm):
    # built with the hinge at the origin: the lid reaches forward (-Y) by D, its bottom at z = 0
    yc = -D / 2
    rbox(bm, (0, yc, LID_H / 2), (W - 0.04, D - 0.04, LID_H), LB_CREAM, **SOFT)
    # the two orange bumpers over the left and right thirds, rivets on their front and side faces
    for sx in (-1, 1):
        cx = sx * (W / 2 - 0.15)
        rbox(bm, (cx, yc, LID_H / 2 + 0.005), (0.3, D - 0.01, LID_H + 0.02), LB_ORANGE, cuts=4, power=7.0)
        rivet(bm, (cx + sx * 0.06, -D + 0.002, LID_H * 0.5))
        rivet(bm, (sx * (W / 2 - 0.004), yc - 0.3, LID_H * 0.5))
        rivet(bm, (sx * (W / 2 - 0.004), yc + 0.3, LID_H * 0.5))
    # grey straps at the top's front and back edges, the latch hanging over the seam
    for sy in (-1, 1):
        rbox(bm, (0, yc + sy * (D / 2 - 0.08), LID_H + 0.005), (0.26, 0.18, 0.05), LB_METAL, **SOFT)
    rbox(bm, (0, -D + 0.01, 0.06), (0.24, 0.06, 0.15), LB_METAL, **SOFT)
    rbox(bm, (0, -D + 0.005, 0.15), (0.3, 0.05, 0.05), LB_METAL, **SOFT)
    # the grey disc on top with its glowing ring
    rbox(bm, (0, yc, LID_H + 0.02), (0.44, 0.44, 0.06), LB_METAL, cuts=4, power=2.2)
    glow_part(bm, lambda t: torus(t, (0, yc, LID_H + 0.05), 0.15, 0.022, LB_GLOW))


def build_lootbox():
    mat = bpy.data.materials["M_GradientTexture"]
    glow = bpy.data.materials["M_GradientGlow"]
    coll = bpy.data.collections.get("LootBox")
    if coll is None:
        coll = bpy.data.collections.new("LootBox")
        bpy.context.scene.collection.children.link(coll)
    bm = bmesh.new()
    body(bm)
    base = finish(bm, "SM_LootBox_Base", coll, (0, 0, 0), mat)
    bm = bmesh.new()
    lid(bm)
    top = finish(bm, "SM_LootBox_Lid", coll, (0, D / 2, H), mat)
    for o in (base, top):
        o.data.materials.append(glow)
    return base, top
