# Premium store pavilion (gab): a royal backdrop around the three store stalls. Marble floor with
# a gold border, red carpet runner, deep purple back wall with gold trim and cornice, marble
# pilasters with gold capitals, a central arch (purple panel for the PREMIUM STORE title, gold
# rim) with a glowing diamond and a gold crown, two marble towers with gold-tipped purple onion
# domes, purple banners with gold crowns, gem studs along the cornice, gold lamp posts with
# glowing globes and gold coin piles. Glowing parts use slot 1 = M_GradientGlow (atlas colours).
# Pivot: the middle of the stall row on the ground; front -Y; the stalls stand inside y -1..+1.
# Runs check_closed + zfight (must be 0).
#   exec(open(r"<skills>/blender-game-props/premium.py").read())
#   build_premium()
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

ROYAL = canopy(5, 1235, 1335)
ROYAL_DARK = canopy(5, 1130, 1210)
GOLD_T = c0(23, 0.88, 0.97)
MARBLE = CREAM
CARPET = c0(14, 0.9, 0.96)
GEM_CYAN = fruitb(13, 760, 1000)
GEM_PINK = fruitb(11, 760, 1000)
GEM_GREEN = fruitb(7, 760, 1000)
GEM_VIOLET = fruitb(15, 760, 1000)

WALL_Y0, WALL_Y1 = 1.6, 2.0      # back wall depth
WALL_HW = 5.6                     # back wall half width
WALL_H = 4.2
ARCH_HW = 2.2
TOWER_X = 6.15


def gem(bm, c, r, col, glowing=True):
    """Cut gem: a faceted double cone (8 sides), pointing up and down."""
    def build(t):
        revolve(t, [(0.02 * r, -0.7 * r), (0.8 * r, -0.05 * r), (1.0 * r, 0.12 * r), (0.62 * r, 0.42 * r), (0.04 * r, 0.46 * r)], col, c, 8)
    if glowing:
        glow(build)(bm)
    else:
        build(bm)


def crown(bm, c, s):
    x, y, z = c
    revolve(bm, [(0.5 * s, 0.0), (0.52 * s, 0.05 * s), (0.52 * s, 0.24 * s), (0.5 * s, 0.28 * s)], GOLD, (x, y, z), 16)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        px, py = x + 0.44 * s * math.cos(a), y + 0.44 * s * math.sin(a)
        box(bm, (px, py, z + 0.42 * s), (0.16 * s, 0.07 * s, 0.32 * s), GOLD, yaw=math.degrees(a) + 90, taper=0.3)
        ball2(bm, (px, py, z + 0.64 * s), 0.06 * s, GOLD)
    for k, col in enumerate((GEM_CYAN, GEM_PINK, GEM_GREEN, GEM_VIOLET)):
        a = -math.pi / 2 + (k - 1.5) * 0.55
        glow(ball2)(bm, (x + 0.53 * s * math.cos(a), y + 0.53 * s * math.sin(a), z + 0.14 * s), 0.07 * s, col, (1, 0.6, 1.2))
    ball2(bm, (x, y, z + 0.3 * s), 0.38 * s, CARPET, (1, 1, 0.55), 2)   # velvet cap


def onion_dome(bm, c, r):
    x, y, z = c
    revolve(bm, [(0.9 * r, 0.0), (1.05 * r, 0.25 * r), (1.0 * r, 0.6 * r), (0.6 * r, 1.0 * r), (0.2 * r, 1.35 * r), (0.04 * r, 1.5 * r)], GOLD, (x, y, z), 14)
    revolve(bm, [(0.93 * r, 0.06 * r), (1.08 * r, 0.12 * r), (1.08 * r, 0.24 * r), (0.95 * r, 0.3 * r)], ROYAL, (x, y, z), 14)
    revolve(bm, [(0.05 * r, 1.48 * r), (0.05 * r, 1.85 * r)], GOLD, (x, y, z), 8)
    ball2(bm, (x, y, z + 1.95 * r), 0.11 * r, GOLD)


def banner_crown(bm, x, y, ztop):
    pts = [(x - 0.42, ztop), (x + 0.42, ztop), (x + 0.42, ztop - 1.5), (x, ztop - 1.8), (x - 0.42, ztop - 1.5), (x - 0.42, ztop - 0.75)]
    slab(bm, pts, ROYAL_DARK, 0.04, 0.012, center=(x, ztop - 0.8), at=(0, y, 0))
    # gold crown emblem: band + three points
    slab(bm, [(x - 0.22, ztop - 0.95), (x + 0.22, ztop - 0.95), (x + 0.24, ztop - 0.7), (x + 0.12, ztop - 0.8), (x, ztop - 0.62), (x - 0.12, ztop - 0.8), (x - 0.24, ztop - 0.7), (x - 0.23, ztop - 0.83)],
         GOLD, 0.03, 0.01, center=(x, ztop - 0.82), at=(0, y - 0.04, 0))
    box(bm, (x, y - 0.012, ztop + 0.04), (0.98, 0.07, 0.08), GOLD)     # hanging rod


def lamp_post(bm, x, y):
    box(bm, (x, y, 0.08), (0.36, 0.36, 0.16), GOLD_T)
    tube(bm, [(x, y, 0.16), (x, y, 2.3)], [0.07, 0.055], GOLD, 10)
    revolve(bm, [(0.12, 2.3), (0.16, 2.38), (0.09, 2.42)], GOLD, (x, y, 0), 10)
    glow(ball2)(bm, (x, y, 2.62), 0.22, STAR_Y, (1, 1, 1.05), 2)
    revolve(bm, [(0.1, 2.82), (0.14, 2.86), (0.03, 3.0)], GOLD, (x, y, 0), 10)


def coins(bm, c, n, seed):
    rnd = random.Random(seed)
    x, y, z = c
    for i in range(n):
        revolve(bm, [(0.15, z + i * 0.052), (0.15, z + i * 0.052 + 0.045)], GOLD, (x + rnd.uniform(-0.03, 0.03), y + rnd.uniform(-0.03, 0.03), 0), 12)


def g_premium(bm):
    # marble floor under the stalls with a gold border, carpet runner to the front
    box(bm, (0, 0.175, 0.02), (12.6, 3.15, 0.04), MARBLE)          # runs under the wall
    for yy in (-1.35, 1.5):
        box(bm, (0, yy, 0.05), (12.6, 0.1, 0.02), GOLD_T)
    for sx in (-1, 1):
        box(bm, (sx * 6.25, 0.075, 0.051), (0.1, 2.75, 0.022), GOLD_T)
    box(bm, (0, -2.75, 0.018), (2.2, 2.7, 0.036), CARPET)
    for sx in (-1, 1):
        box(bm, (sx * 1.13, -2.75, 0.024), (0.06, 2.7, 0.048), GOLD_T)
    # back wall, gold rail and cornice
    box(bm, (0, (WALL_Y0 + WALL_Y1) / 2, WALL_H / 2), (2 * WALL_HW, WALL_Y1 - WALL_Y0, WALL_H), ROYAL)
    box(bm, (0, WALL_Y0 - 0.03, 1.2), (2 * WALL_HW - 0.02, 0.05, 0.08), GOLD_T)   # 5 mm off the wall
    box(bm, (0, (WALL_Y0 + WALL_Y1) / 2 - 0.06, WALL_H + 0.12), (2 * WALL_HW + 0.3, 0.6, 0.24), GOLD)
    box(bm, (0, (WALL_Y0 + WALL_Y1) / 2 - 0.08, WALL_H + 0.29), (2 * WALL_HW + 0.12, 0.56, 0.1), GOLD_T)
    # marble pilasters with gold capitals and bases
    for x in (-4.0, -2.2, 2.2, 4.0):
        box(bm, (x, WALL_Y0 - 0.1, WALL_H / 2), (0.42, 0.2, WALL_H - 0.02), MARBLE)
        box(bm, (x, WALL_Y0 - 0.13, 0.12), (0.56, 0.3, 0.24), GOLD_T)
        box(bm, (x, WALL_Y0 - 0.14, WALL_H - 0.12), (0.58, 0.32, 0.2), GOLD_T)
    # banners between the outer pilasters
    for x in (-3.1, 3.1):
        banner_crown(bm, x, WALL_Y0 - 0.05, WALL_H - 0.35)
    # gems studding the cornice front
    for i, x in enumerate([-5.0, -3.1, -1.25, 1.25, 3.1, 5.0]):
        gem_cols = (GEM_PINK, GEM_GREEN, GEM_VIOLET)
        glow(ball2)(bm, (x, WALL_Y0 - 0.43, WALL_H + 0.12), 0.11, gem_cols[i % 3], (1, 0.55, 1))
    # central arch above the cornice: purple panel for the title, gold rim, diamond, crown
    arch = [(ARCH_HW * math.cos(math.pi * i / 16), 6.0 * 0 + (WALL_H + 0.35) + 1.55 * math.sin(math.pi * i / 16)) for i in range(17)]
    panel = [(ARCH_HW, WALL_H + 0.35)] + [(x, z) for x, z in arch[1:-1]] + [(-ARCH_HW, WALL_H + 0.35)]
    if len(panel) % 2:
        panel.insert(1, ((panel[0][0] + panel[1][0]) / 2, (panel[0][1] + panel[1][1]) / 2))
    slab(bm, panel, ROYAL, 0.36, 0.0, 0.6, center=(0.0, WALL_H + 0.9), at=(0, WALL_Y0 + 0.08, 0))
    band(bm, [(x, WALL_Y0 - 0.15, z) for x, z in arch], 0.22, 0.22, GOLD)
    gem(bm, (0, WALL_Y0 - 0.36, WALL_H + 1.55), 0.42, GEM_CYAN)
    crown(bm, (0, WALL_Y0 + 0.08, WALL_H + 1.98), 1.7)
    # gold diamond lattice in the wall bays (just in front of the wall)
    for x0, x1 in ((-5.55, -4.25), (4.25, 5.55), (-1.95, 1.95)):
        t = bmesh.new()
        lattice(t, x0, x1, 1.3, WALL_H - 0.12, GOLD_T, 0.34, 0.045, 0.03)
        bmesh.ops.translate(t, vec=Vector((0, WALL_Y0 - 0.035, 0)), verts=t.verts)
        merge(bm, t)
    # glowing light strip under the cornice
    glow(box)(bm, (0, WALL_Y0 - 0.33, WALL_H - 0.05), (2 * WALL_HW - 0.2, 0.04, 0.05), STAR_Y)
    # towers with onion domes
    for sx in (-1, 1):
        x = sx * TOWER_X
        box(bm, (x, 1.4, 0.15), (1.18, 1.18, 0.3), GOLD_T)
        box(bm, (x, 1.4, 2.6), (0.96, 0.96, 4.6), MARBLE)
        for z in (1.4, 3.2):
            box(bm, (x, 1.4, z), (1.04, 1.04, 0.12), GOLD_T)
        box(bm, (x, 1.4, 4.98), (1.16, 1.16, 0.16), GOLD)
        onion_dome(bm, (x, 1.4, 5.06), 0.55)
        gem(bm, (x, 1.4 - 0.55, 4.3), 0.17, GEM_PINK if sx < 0 else GEM_GREEN)
        # arched window slit on the tower front
        slab(bm, [(x - 0.18, 2.2), (x + 0.18, 2.2), (x + 0.18, 2.95), (x + 0.1, 3.05), (x, 3.08), (x - 0.1, 3.05), (x - 0.18, 2.95), (x - 0.18, 2.6)],
             ROYAL_DARK, 0.03, 0.005, center=(x, 2.62), at=(0, 1.4 - 0.48 - 0.016, 0))
        lamp_post(bm, sx * 6.4, -1.75)
        coins(bm, (sx * 5.35, -1.75, 0.0), 6, 30 + (sx > 0))
        coins(bm, (sx * 5.05, -1.55, 0.0), 4, 40 + (sx > 0))


def build_premium():
    root = bpy.data.collections.get("Premium") or bpy.data.collections.new("Premium")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    bm = bmesh.new()
    g_premium(bm)
    o = finish_lamp(bm, "SM_PremiumPavilion", root, (0, -190.0, 0))
    o.data.materials[1] = bpy.data.materials["M_GradientGlow"]
    return check_closed([o]), zfight(o), [round(d, 2) for d in o.dimensions]
