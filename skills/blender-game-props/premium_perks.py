# Premium store perk items (gab store_item models, sheet 61) in the pack style:
#   SM_PremiumVIP      - gold crown: open ring with a brim, two tall diamond-tipped points (front /
#                        back) with a glowing ruby in a gold frame, two flared side prongs, gold
#                        studs, glowing sparkles.
#   SM_PremiumAutoFarm - tilted rake (grey metal head with 5 curved tines, ferrule, orange wooden
#                        handle) in front of two lime "repeat" arrows, with floating leaves.
# Pivot at the bottom centre (the items spin around it in game). Glow = slot 1 (M_GradientGlow).
# check_closed + zfight must be 0.
#   exec(open(r"<skills>/blender-game-props/premium_perks.py").read())
#   build_premium_perks()
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

exec(open(_skill("blender-game-props/premium.py")).read())

CROWN_GOLD = c0(23, 0.86, 0.96)
CROWN_GOLD_DARK = c0(23, 0.85, 0.87)
RUBY = c0(6, 0.9, 0.98)
METAL = c1(6, 0.74, 0.82)
METAL_DARK = c1(6, 0.7, 0.74)
HANDLE = ORANGE
ARROW = c0(9, 0.95, 0.995)
LEAF_G = c0(9, 0.9, 0.96)
SPARK = STAR_Y


def ring_shell(bm, prof, col, sides=24, at=(0, 0, 0)):
    """Closed loop profile of (radius, z) revolved around Z: a hollow ring, all quads, no caps."""
    b = bmesh.new()
    rings = [[b.verts.new((at[0] + r * math.cos(2 * math.pi * k / sides), at[1] + r * math.sin(2 * math.pi * k / sides), at[2] + z))
              for k in range(sides)] for r, z in prof]
    n = len(rings)
    for j in range(n):
        for k in range(sides):
            b.faces.new((rings[j][k], rings[j][(k + 1) % sides], rings[(j + 1) % n][(k + 1) % sides], rings[(j + 1) % n][k]))
    uv_part(b, col)
    merge(bm, b)


def turned(fn, yaw, at=(0, 0, 0)):
    """Builds fn(t) in its own mesh, turns it yaw degrees around Z and moves it by at."""
    def g(bm, *a, **k):
        t = bmesh.new()
        fn(t, *a, **k)
        bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(yaw), 3, 'Z'), verts=t.verts)
        bmesh.ops.translate(t, vec=Vector(at), verts=t.verts)
        merge(bm, t)
    return g


def sparkle_pts(r, c, thin=0.28):
    """Four-point sparkle outline (8 points) in the x/z plane."""
    return [(c[0] + (r if i % 2 == 0 else r * thin) * math.cos(math.pi / 2 + math.pi * i / 4),
             c[1] + (r if i % 2 == 0 else r * thin) * math.sin(math.pi / 2 + math.pi * i / 4)) for i in range(8)]


def sparkle4(bm, c, r):
    slab(bm, sparkle_pts(r, (c[0], c[2])), SPARK, r * 0.22, r * 0.12, 0.5, center=(c[0], c[2]), at=(0, c[1], 0), glowing=True)


# ---------------------------------------------------------------- VIP crown
CR = 0.44            # ring radius
BAND_Z = 0.36


def crown_point(t, y):
    """The tall front point: shoulders, a notch and a diamond tip; ruby in a gold frame on its face."""
    pts = [(-0.19, 0.18), (0.0, 0.18), (0.19, 0.18), (0.19, 0.44), (0.07, 0.55), (0.15, 0.63),
           (0.0, 0.8), (-0.15, 0.63), (-0.07, 0.55), (-0.19, 0.44)]
    slab(t, pts, CROWN_GOLD, 0.09, 0.025, 0.6, center=(0.0, 0.47), at=(0, y, 0))
    # raised inner border line
    inner = [(-0.13, 0.3), (0.0, 0.3), (0.13, 0.3), (0.13, 0.44), (0.04, 0.53), (0.1, 0.6), (0.0, 0.71), (-0.1, 0.6), (-0.04, 0.53), (-0.13, 0.44)]
    slab(t, inner, CROWN_GOLD_DARK, 0.03, 0.008, 0.6, center=(0.0, 0.47), at=(0, y - 0.05, 0))
    slab(t, [(0.0, 0.25), (0.115, 0.4), (0.0, 0.555), (-0.115, 0.4)], CROWN_GOLD, 0.05, 0.015, 0.5, center=(0.0, 0.4), at=(0, y - 0.08, 0))
    slab(t, [(0.0, 0.28), (0.085, 0.4), (0.0, 0.52), (-0.085, 0.4)], RUBY, 0.05, 0.05, 0.45, center=(0.0, 0.4), at=(0, y - 0.115, 0), glowing=True)


def crown_prong(t, y):
    """A flared side prong (tulip shape)."""
    pts = [(-0.14, 0.18), (0.14, 0.18), (0.14, 0.4), (0.24, 0.58), (0.06, 0.47), (-0.06, 0.47), (-0.24, 0.58), (-0.14, 0.4)]
    slab(t, pts, CROWN_GOLD, 0.09, 0.02, 0.6, center=(0.0, 0.36), at=(0, y, 0))


def g_vip(bm):
    # open ring: brim at the bottom, band above, inner wall
    ring_shell(bm, [(CR - 0.05, 0.0), (CR + 0.04, 0.0), (CR + 0.06, 0.04), (CR + 0.04, 0.09), (CR + 0.005, 0.1),
                    (CR + 0.005, BAND_Z - 0.03), (CR + 0.02, BAND_Z), (CR - 0.05, BAND_Z)], CROWN_GOLD, 28)
    # points: front / back tall, left / right prongs; sit just inside the band so they read as one piece
    for yaw in (0, 180):
        turned(crown_point, yaw)(bm, -(CR - 0.015))
    for yaw in (90, 270):
        turned(crown_prong, yaw)(bm, -(CR - 0.015))
    # gold studs on the band between the points
    for k in range(8):
        a = math.radians(45 * k + 22.5)
        ball2(bm, (math.sin(a) * (CR + 0.02), -math.cos(a) * (CR + 0.02), 0.2), 0.04, CROWN_GOLD, (1, 1, 1))
    # sparkles around it
    for k, (x, y, z, r) in enumerate(((-0.62, -0.1, 0.78, 0.1), (-0.4, -0.2, 0.98, 0.055), (0.58, -0.1, 0.86, 0.08), (-0.64, -0.15, 0.25, 0.06), (0.66, -0.15, 0.3, 0.07))):
        sparkle4(bm, (x, y + 0.004 * k, z), r)


# ---------------------------------------------------------------- Auto-Farm rake
RAKE_TILT = 38.0


def rake(t):
    """Upright rake: head at the bottom, handle up +Z, tines bending toward the front (-Y)."""
    tube(t, [(-0.36, 0, 0.36), (0.36, 0, 0.36)], [0.055, 0.055], METAL, 8)
    for sx in (-1, 1):
        ball2(t, (sx * 0.36, 0, 0.36), 0.06, METAL)
    for k in range(5):
        x = -0.3 + 0.15 * k
        pts = [(x, 0.0, 0.36), (x, 0.0, 0.22), (x, -0.03, 0.12), (x, -0.09, 0.06), (x, -0.15, 0.05)]
        tube(t, pts, [0.046, 0.045, 0.043, 0.04, 0.036], METAL, 8)
        ball2(t, (x, -0.15, 0.05), 0.037, METAL)
    # neck with a brace into the bar
    tube(t, [(0, 0, 0.36), (0, 0, 0.62)], [0.045, 0.04], METAL, 8)
    for sx in (-1, 1):
        tube(t, [(sx * 0.15, 0, 0.37), (sx * 0.02, 0, 0.55)], [0.025, 0.022], METAL, 8)
    # ferrule (two rings) and the wooden handle with a rounded end
    revolve(t, [(0.058, 0.6), (0.068, 0.62), (0.068, 0.7), (0.062, 0.72)], METAL_DARK, (0, 0, 0), 12)
    revolve(t, [(0.062, 0.72), (0.072, 0.74), (0.072, 0.78), (0.064, 0.8)], METAL, (0, 0, 0), 12)
    tube(t, [(0, 0, 0.8), (0, 0, 1.5)], [0.058, 0.064], HANDLE, 10)
    ball2(t, (0, 0, 1.5), 0.064, HANDLE, (1, 1, 0.9), 2)
    # grip grooves
    for z in (1.18, 1.26, 1.34):
        revolve(t, [(0.061, z), (0.066, z + 0.012), (0.061, z + 0.024)], c1(1, 0.69, 0.72), (0, 0, 0), 10)


def arrow_arc(bm, c, R, a0, a1, y, r=0.07):
    """A thick arc from angle a0 to a1 (degrees, x/z plane around c), ending in a flat arrowhead."""
    n = 10
    angs = [math.radians(a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    pts = [(c[0] + R * math.cos(a), y, c[1] + R * math.sin(a)) for a in angs]
    a = angs[-1]
    sgn = 1 if a1 > a0 else -1
    tx, tz = -math.sin(a) * sgn, math.cos(a) * sgn        # direction of travel at the end
    nx, nz = math.cos(a), math.sin(a)                      # outward
    ex, ez = pts[-1][0] + tx * 0.04, pts[-1][2] + tz * 0.04
    tube(bm, pts[:-1] + [(ex, y, ez)], [r] * (n + 1), ARROW, 10)
    ball2(bm, pts[0], r, ARROW, (1, 1, 1))
    bx, bz = pts[-1][0] + tx * 0.02, pts[-1][2] + tz * 0.02
    head = [(bx + nx * 0.17, bz + nz * 0.17), (bx + tx * 0.24, bz + tz * 0.24),
            (bx - nx * 0.17, bz - nz * 0.17), (bx - tx * 0.03, bz - tz * 0.03)]
    slab(bm, head, ARROW, 0.12, 0.03, 0.5, center=(bx + tx * 0.06, bz + tz * 0.06), at=(0, y, 0))


def leaf_slab(bm, c, L, W, rot, col=LEAF_G):
    pts = [(c[0] + L / 2 * math.cos(math.radians(rot)) * math.cos(a) - W / 2 * (math.sin(a) * abs(math.sin(a)) ** 0.3) * math.sin(math.radians(rot)),
            c[2] + L / 2 * math.sin(math.radians(rot)) * math.cos(a) + W / 2 * (math.sin(a) * abs(math.sin(a)) ** 0.3) * math.cos(math.radians(rot)))
           for a in [2 * math.pi * i / 14 for i in range(14)]]
    slab(bm, pts, col, 0.03, 0.025, 0.55, center=(c[0], c[2]), at=(0, c[1], 0))
    # mid rib
    ex, ez = math.cos(math.radians(rot)) * L * 0.38, math.sin(math.radians(rot)) * L * 0.38
    beam(bm, (c[0] - ex, c[1] - 0.034, c[2] - ez), (c[0] + ex, c[1] - 0.034, c[2] + ez), 0.012, 0.014, c0(9, 0.86, 0.88))


def g_autofarm(bm):
    t = bmesh.new()
    rake(t)
    bmesh.ops.rotate(t, cent=Vector(), matrix=Matrix.Rotation(math.radians(RAKE_TILT), 3, 'Y'), verts=t.verts)
    bmesh.ops.translate(t, vec=Vector((-0.12, 0, 0.1)), verts=t.verts)
    merge(bm, t)
    # repeat arrows behind the handle, up and left
    c, R, y = (-0.02, 0.88), 0.33, 0.16
    arrow_arc(bm, c, R, 168, 28, y)
    arrow_arc(bm, c, R, -12, -152, y + 0.003)
    # leaves
    for k, (x, z, L, rot) in enumerate(((-0.62, 0.86, 0.24, 140), (0.62, 1.12, 0.22, 60), (0.66, 0.72, 0.3, 30))):
        leaf_slab(bm, (x, -0.02 * k, z), L, 0.13, rot)


PERKS = [("SM_PremiumVIP", g_vip), ("SM_PremiumAutoFarm", g_autofarm)]


def _ground(o):
    """Bottom centre pivot: x/y centred on the bounds, lowest point on z = 0."""
    me = o.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    d = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    for v in me.vertices:
        v.co -= d


def build_premium_perks():
    root = bpy.data.collections.get("PremiumItems") or bpy.data.collections.new("PremiumItems")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    out = {}
    for i, (name, fn) in enumerate(PERKS):
        bm = bmesh.new()
        fn(bm)
        o = finish_lamp(bm, name, root, (9.0 + i * 3.0, -240.0, 0))
        o.data.materials[1] = bpy.data.materials["M_GradientGlow"]
        _ground(o)
        out[name] = (check_closed([o])[name], zfight(o)[:6], [round(d, 2) for d in o.dimensions], len(o.data.polygons))
    return out
