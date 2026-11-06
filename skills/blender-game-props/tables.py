# Wooden tables (gab, for the barns / market) in the barn's flat-shaded wood: a plank top (planks
# with small gaps and a little height / length jitter), an apron frame under it, tapered legs on
# feet and stretchers between the legs (a centre one on the long tables). Six sizes:
#   Tiny (side table), Small, Medium, Big, Wide (6 legs), Short (low coffee table).
# Pivot at the bottom centre, length along X, front -Y. check_closed + zfight must be 0.
#   exec(open(r"<skills>/blender-game-props/tables.py").read())
#   build_tables()
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

import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(_skill("blender-game-props/barn_set2.py")).read())

T_WOOD = c1(1, 0.72, 0.78)
T_WOOD_LIGHT = c1(1, 0.77, 0.82)
T_WOOD_DARK = c1(2, 0.69, 0.73)

# name: (length, depth, height, planks, leg width, middle legs)
TABLES = {
    "Tiny":   (0.6, 0.5, 0.55, 3, 0.07, False),
    "Small":  (1.0, 0.7, 0.8, 4, 0.08, False),
    "Medium": (1.6, 0.9, 0.85, 5, 0.1, False),
    "Big":    (2.4, 1.1, 0.9, 6, 0.12, False),
    "Wide":   (3.2, 1.4, 0.9, 7, 0.13, True),
    "Short":  (1.4, 0.8, 0.45, 5, 0.1, False),
}
TOP_T = 0.07        # plank thickness
GAP = 0.012         # gap between planks
OVER = 0.06         # top overhang past the legs


def g_table(bm, L, D, H, n, lw, mid, seed):
    rnd = random.Random(seed)
    under = H - TOP_T
    # plank top
    pw = (D - GAP * (n - 1)) / n
    for k in range(n):
        y = -D / 2 + pw / 2 + k * (pw + GAP)
        h = TOP_T + 0.004 * (k % 3)
        box(bm, (rnd.uniform(-0.01, 0.01), y, under + h / 2), (L - rnd.uniform(0, 0.025), pw, h), T_WOOD_LIGHT if k % 2 else T_WOOD)
    # legs (tapered, wider at the top) on feet
    lx, ly = L / 2 - OVER - lw / 2, D / 2 - OVER - lw / 2
    xs = [-lx, 0.0, lx] if mid else [-lx, lx]
    for x in xs:
        for sy in (-1, 1):
            box(bm, (x, sy * ly, 0.02 + (under + 0.025 - 0.02) / 2), (lw * 0.82, lw * 0.82, under + 0.025 - 0.02), T_WOOD_DARK, taper=1.2)
            box(bm, (x, sy * ly, 0.03), (lw * 1.15, lw * 1.15, 0.06), T_WOOD, taper=0.85)
    # apron: long sides between the legs, short ends between the long sides (a bit lower)
    ah = min(0.12, under * 0.3)
    at = 0.035
    for sy in (-1, 1):
        box(bm, (0.0, sy * (ly - lw * 0.1), under + 0.012 - ah / 2), (2 * lx, at, ah), T_WOOD)
    for sx in (-1, 1):
        box(bm, (sx * (lx - lw * 0.1), 0.0, under + 0.006 - (ah - 0.03) / 2), (at, 2 * ly - at - 0.01, ah - 0.03), T_WOOD)
    # stretchers low between the legs (ends inside the legs), plus a long centre one
    sz = max(0.12, H * 0.2)
    for x in xs:
        box(bm, (x, 0.0, sz), (lw * 0.45, 2 * ly, lw * 0.45), T_WOOD)
    if L > 1.2:
        box(bm, (0.0, 0.0, sz + lw * 0.14), (2 * lx, lw * 0.42, lw * 0.42), T_WOOD_LIGHT)


def build_tables(only=None):
    root = bpy.data.collections.get("Tables") or bpy.data.collections.new("Tables")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    out = {}
    for i, (name, (L, D, H, n, lw, mid)) in enumerate(TABLES.items()):
        if only and name not in only:
            continue
        bm = bmesh.new()
        g_table(bm, L, D, H, n, lw, mid, 400 + i)
        o = finish_lamp(bm, "SM_Table_" + name, root, (i * 4.0, -250.0, 0))
        out[o.name] = (check_closed([o])[o.name], zfight(o)[:6], [round(d, 2) for d in o.dimensions], len(o.data.polygons))
    return out
