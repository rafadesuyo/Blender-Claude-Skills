# 30 daily-reward trees (Dante's reference sheet) in the NewLua pack style: gradient atlas, quads
# only, closed shells, smooth. Run inside the pack .blend:
#   exec(open(r"<skills>/blender-game-props/daily_trees.py").read())
#   add_atlas_strips()   # once: writes each tree's canopy + fruit gradient into empty atlas space
#   build_daily()        # or build_daily(["GoldenApple"])
# Output: collection DailyRewards > DR_<nn>_<Name>, objects SM_DR_<Name>Tree_Stage1..4 + SM_DR_<Name>
# (the fruit). Glowing fruit use slot 1 = M_GradientGlow (the same atlas, emissive), so each glows
# in its own colour.
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
import numpy as np
from mathutils import Vector, Matrix

exec(open(_skill("blender-game-props/lamp_posts.py")).read())   # box() + the tree helpers

# Atlas bands for these trees (empty space below the pack's strips, which end at row 1366):
CANOPY_BAND = (1040, 1340)   # pixel rows -> v 0.508 .. 0.654, one 57 px column per tree
FRUIT_BAND = (712, 1012)     # v 0.348 .. 0.494
RAINBOW = ["#FF3B3B", "#FF9A2E", "#FFE94A", "#5BE85A", "#3AC8FF", "#5A6AFF", "#C25AFF"]
GALAXY = ["#140A48", "#3A1A9A", "#8A2ACF", "#E05AC8", "#FFD0F4"]

# name, canopy (bottom, top) or stop list, fruit (bottom, top) or stop list, fruit kind, glows, willow
TREES = [
    ("GoldenApple", ("#3E7A12", "#9BD63A"), ("#D8A000", "#FFF27A"), "apple", False, False),
    ("CrystalPeach", ("#A8285A", "#F07AA8"), ("#FFE2EE", "#FFFFFF"), "peach", True, False),
    ("StarFruit", ("#1240A8", "#4FA3FF"), ("#E8A800", "#FFF27A"), "star", True, False),
    ("RubyPomegranate", ("#3E0810", "#7A1424"), ("#FF1A3A", "#FF9AAA"), "pomegranate", True, False),
    ("MoonPearl", ("#2E8A3A", "#9CE07A"), ("#C8C4D0", "#FFFFFF"), "pearl", False, False),
    ("AmethystFig", ("#2E0E5A", "#6A34A8"), ("#E04AFF", "#FFD8FF"), "drop", True, False),
    ("HoneyGem", ("#C9B48E", "#FFF6E2"), ("#C07A00", "#FFD040"), "honeycomb", False, False),
    ("EmeraldApple", ("#0A3E1A", "#1E7A34"), ("#3AFF7A", "#D8FFE6"), "apple", True, False),
    ("SunstoneOrange", ("#7A2204", "#D2621A"), ("#FFD040", "#FFFBE0"), "lantern", True, False),
    ("SilverBell", ("#1C1F6E", "#5560D0"), ("#9AA0B0", "#F4F6FA"), "bell", False, False),
    ("Frostberry", ("#8FB6E0", "#F4FAFF"), ("#0A4AD0", "#5AB4FF"), "snowflake", True, False),
    ("Heartberry", ("#4A0812", "#8E1626"), ("#FF4A8A", "#FFD8E6"), "heart", True, False),
    ("DreamGrape", ("#8A62C8", "#D8C0FA"), ("#22085A", "#5A2AB8"), "grapes", False, True),
    ("SkyPlum", ("#2E8A1E", "#8CE84A"), ("#1A7AE0", "#9AE8FF"), "drop", True, False),
    ("CloudCherry", ("#D88AA0", "#FFE0E8"), ("#A00A26", "#FF4A6A"), "cherry", False, False),
    ("ShadowFig", ("#0E0A18", "#3A3048"), ("#4A00A8", "#D080FF"), "flame", True, False),
    ("Gearfruit", ("#2E5A0E", "#6AA81E"), ("#E0A000", "#FFF27A"), "gear", True, False),
    ("LightbulbFruit", ("#2E8A2A", "#8AD84A"), ("#E0A000", "#FFF4A0"), "bulb", True, False),
    ("DragonPepper", ("#1E4E16", "#4A9A2A"), ("#D01008", "#FF7A3A"), "chili", False, False),
    ("IceLotus", ("#1E4E9A", "#5A90D8"), ("#D8F4FF", "#FFFFFF"), "star", True, False),
    ("FairyTear", ("#B03A76", "#F088B8"), ("#C8F4FF", "#FFFFFF"), "shard", True, True),
    ("VoidFruit", ("#0E1450", "#2A3A9A"), ("#C03AFF", "#FFC8FF"), "orb", True, False),
    ("GoldNugget", ("#7A4206", "#B87A1A"), ("#FFD000", "#FFFAB0"), "nugget", True, False),
    ("Prismberry", ("#2E8A1E", "#8CE84A"), RAINBOW, "gem", True, False),
    ("Truffle", ("#9A9A98", "#E2E2E0"), ("#2E1206", "#7A4A26"), "truffle", False, False),
    ("ManaFruit", ("#7A0E6A", "#D23AC0"), ("#1A90FF", "#C0F4FF"), "yarn", True, False),
    ("RainbowDrop", ("#2E8A2A", "#92E04E"), RAINBOW, "drop", True, False),
    ("CelestialPeach", ("#E0B4C0", "#FFF0F2"), ("#FF9A30", "#FFE8A0"), "peach", True, False),
    ("GalaxyFruit", ("#0A1A3A", "#1E4A7A"), GALAXY, "orb", True, False),
    ("PrismaticChocolate", ("#2E1206", "#6A3A1E"), RAINBOW, "star", True, False),
]


def _hex(h):
    h = h.lstrip("#")
    c = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _stops(spec):
    """(bottom, top) pair or a list of stops bottom -> top."""
    return [_hex(s) for s in (spec if isinstance(spec, list) else list(spec))]


def strip_uv(band, k):
    y0, y1 = band
    H = 2048
    return ((k + 0.5) * CW, (y0 + 6) / H, (y1 - 6) / H)


def add_atlas_strips():
    """Writes one canopy and one fruit gradient per tree into CANOPY_BAND / FRUIT_BAND, which are
    reserved for these trees (they were empty when first written, rows 0-1365 of the pack's atlas).
    Re-running rewrites them (to change a colour). Reports any pixel changed outside the strips."""
    img = [i for i in bpy.data.images if i.name.startswith("GradientTexture")][0]
    W, H = img.size
    px = np.empty(W * H * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    orig = px.copy()
    px = px.reshape(H, W, 4)
    touched = np.zeros((H, W), bool)
    for k, (name, canopy, fruit, *_rest) in enumerate(TREES):
        for band, spec in ((CANOPY_BAND, canopy), (FRUIT_BAND, fruit)):
            y0, y1 = band
            x0, x1 = int(k * CW * W) + 3, int((k + 1) * CW * W) - 3
            stops = _stops(spec)
            block = np.zeros((y1 - y0, x1 - x0, 3))
            for y in range(y0, y1):
                t = (y - y0) / (y1 - y0 - 1) * (len(stops) - 1)
                i = min(int(t), len(stops) - 2)
                block[y - y0, :, :] = stops[i] + (stops[i + 1] - stops[i]) * (t - i)
            region = px[y0:y1, x0:x1, :3]
            px[y0:y1, x0:x1, :3] = block
            px[y0:y1, x0:x1, 3] = 1.0
            touched[y0:y1, x0:x1] = True
    flat = px.ravel()
    changed = (np.abs(flat - orig) > 1e-7).reshape(H, W, 4).any(axis=2)
    outside = int((changed & ~touched).sum())
    img.pixels.foreach_set(flat)
    img.update()
    img.pack()
    return {"pixels_changed_outside_new_strips": outside}


def glow_atlas_material():
    m = bpy.data.materials.get("M_GradientGlow") or bpy.data.materials.new("M_GradientGlow")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    t = nt.nodes.get("GlowTex") or nt.nodes.new("ShaderNodeTexImage")
    t.name = "GlowTex"
    t.image = [i for i in bpy.data.images if i.name.startswith("GradientTexture")][0]
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 1.6
    return m


# ---------------- pieces ----------------
def leafy(bm, c, r, col, seed, cuts=2, squash=0.9):
    """A leaf puff: quad sphere with a bumpy, leafy outline."""
    rnd = random.Random(seed)
    b = quad_sphere(r, cuts, (1, 1, squash), 0.0, seed)
    for v in b.verts:
        v.co *= 1.0 + rnd.uniform(-0.05, 0.17)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)


def surface_leaf(bm, base, n, t, length, width, col, lift=12.0):
    """A closed quad leaf slab lying ON a surface: base point, surface normal n, pointing along the
    tangent t; the tip lifts `lift` degrees off the surface."""
    b = bmesh.new()
    prof = [(0.0, 0.25), (0.35, 1.0), (0.75, 0.7), (1.0, 0.06)]
    th = max(0.006, width * 0.05) / 2
    rows = [[b.verts.new((u * length, -w * width / 2, th)), b.verts.new((u * length, w * width / 2, th)),
             b.verts.new((u * length, w * width / 2, -th)), b.verts.new((u * length, -w * width / 2, -th))] for u, w in prof]
    for i in range(len(rows) - 1):
        a, nx = rows[i], rows[i + 1]
        for k in range(4):
            b.faces.new((a[k], nx[k], nx[(k + 1) % 4], a[(k + 1) % 4]))
    b.faces.new(rows[0][::-1])
    b.faces.new(rows[-1])
    for v in b.verts:   # lift the tip away from the surface
        v.co.z += math.tan(math.radians(lift)) * v.co.x * (v.co.x / length)
    side = n.cross(t).normalized()
    m = Matrix((t, side, n)).transposed()
    bmesh.ops.transform(b, matrix=m.to_4x4(), verts=b.verts)
    bmesh.ops.translate(b, vec=Vector(base) - t * length * 0.25, verts=b.verts)
    uv_part(b, col)
    merge(bm, b)


def mound(bm, s):
    b = quad_sphere(0.75 * s, 2, (1, 1, 0.22), 0.06, 3)
    for v in b.verts:
        if v.co.z < 0:
            v.co.z *= 0.1
    uv_part(b, c0(9, 0.85, 0.97))
    merge(bm, b)
    rnd = random.Random(5)
    for i in range(4):
        a = rnd.uniform(0, 2 * math.pi)
        b = quad_sphere(0.11 * s, 1, (1.2, 1, 0.65), 0.15, 40 + i)
        bmesh.ops.translate(b, vec=Vector((0.6 * s * math.cos(a), 0.6 * s * math.sin(a), 0.03 * s)), verts=b.verts)
        uv_part(b, ((6 + 0.5) * CW, 0.685, 0.825))   # grey stone strip
        merge(bm, b)


FRUIT_SIZE = 0.24        # final-stage fruit radius (m): big and readable like the reference
CANOPY_C = 1.95          # canopy centre height (m) at s = 1
CANOPY_R = (0.82, 0.88)  # canopy radius: horizontal, vertical


def curve_pts(p0, p1, p2, n):
    """n points along a smooth quadratic curve p0 -> p2 bending toward p1."""
    p0, p1, p2 = Vector(p0), Vector(p1), Vector(p2)
    return [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2 for t in (i / (n - 1) for i in range(n))]


def lush_trunk(bm, s):
    """Short, chunky trunk with ONE gentle curve (smooth, not zig-zag), flared at the base, with
    root flares and gently curved branches into the canopy."""
    H = 1.45 * s
    pts = curve_pts((0, 0, 0), (0.2 * s, 0.04 * s, 0.75 * s), (0.04 * s, 0, H), 10)
    radii = [s * (0.16 + 0.2 * (1 - i / 9) ** 3) for i in range(10)]   # wide flare at the foot
    tube(bm, pts, radii, BARK, 10, 0, H)
    for i in range(5):   # root flares
        a = 2 * math.pi * i / 5 + 0.3
        tube(bm, curve_pts((0.12 * s * math.cos(a), 0.12 * s * math.sin(a), 0.26 * s), (0.36 * s * math.cos(a), 0.36 * s * math.sin(a), 0.14 * s),
                           (0.52 * s * math.cos(a), 0.52 * s * math.sin(a), 0.02 * s), 4),
             [0.1 * s, 0.07 * s, 0.045 * s, 0.02 * s], BARK, 6, 0, H)
    for a, h in ((0.6, 1.0), (3.4, 1.15), (5.0, 0.9)):   # branches into the canopy
        base = Vector(pts[int(h / 1.45 * 9)])
        tip = Vector((0.55 * s * math.cos(a), 0.55 * s * math.sin(a), (h + 0.55) * s))
        mid = base + (tip - base) * 0.5 + Vector((0, 0, -0.1 * s))
        tube(bm, curve_pts(base, mid, tip, 5), [0.09 * s, 0.075 * s, 0.06 * s, 0.05 * s, 0.04 * s], BARK, 6, 0, H)


def lush_canopy(bm, s, col, willow=False):
    """Round, slightly tall canopy of leafy puffs (no leaf cards on them: he found those weird)."""
    rnd = random.Random(11)
    C = Vector((0, 0, CANOPY_C * s))
    rx, rz = CANOPY_R[0] * s, CANOPY_R[1] * s
    puffs = [(C, 0.62 * s)]
    for el, n, off in ((-0.38, 6, 0.0), (0.12, 7, 0.45), (0.62, 5, 0.2)):
        for i in range(n):
            a = 2 * math.pi * i / n + off
            R = Vector((rx * math.cos(a) * math.cos(el), rx * math.sin(a) * math.cos(el), rz * math.sin(el)))
            puffs.append((C + R, rnd.uniform(0.34, 0.42) * s))
    puffs.append((C + Vector((0, 0, rz * 0.95)), 0.38 * s))
    for i, (c, r) in enumerate(puffs):
        leafy(bm, c, r, col, 100 + i)
    if willow:   # drooping strands (Dream Grape, Fairy Tear)
        for i in range(12):
            a = 2 * math.pi * i / 12
            top = C + Vector((rx * 1.05 * math.cos(a), rx * 1.05 * math.sin(a), -0.2 * s))
            for j in range(4):
                leafy(bm, top + Vector((0.04 * s * j * math.cos(a), 0.04 * s * j * math.sin(a), -0.2 * s * j)), (0.17 - 0.025 * j) * s, col, 300 + i * 4 + j, cuts=1, squash=1.3)
    return puffs


def fruit_spots(s, n_front=8, n_back=3, seed=0):
    """Points on the canopy surface: most on the front (-Y) half where players look, a few behind."""
    rnd = random.Random(seed)
    C = Vector((0, 0, CANOPY_C * s))
    rx, rz = (CANOPY_R[0] + 0.3) * s, (CANOPY_R[1] + 0.22) * s
    spots = []
    for i in range(n_front + n_back):
        if i < n_front:
            az = math.radians(-90 + (i - (n_front - 1) / 2) * 24 + rnd.uniform(-6, 6))
            el = [-0.45, 0.05, -0.2, 0.35][i % 4] + rnd.uniform(-0.08, 0.08)
        else:
            az = math.radians(90 + (i - n_front - 1) * 50)
            el = rnd.uniform(-0.3, 0.2)
        spots.append(C + Vector((rx * math.cos(az) * math.cos(el), rx * math.sin(az) * math.cos(el), rz * math.sin(el))))
    return spots


# ---------------- fruits: f(bm, c, r, col, seed) ----------------
def _sphere(bm, c, r, col, scale=(1, 1, 1), cuts=1, seed=0, jit=0.02):
    b = quad_sphere(r, cuts, scale, jit, seed)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)


def _stem(bm, c, r):
    tube(bm, [(c[0], c[1], c[2] + r * 0.8), (c[0] + r * 0.1, c[1], c[2] + r * 1.3)], [r * 0.1, r * 0.07], BARK_DARK, 4)


def fr_apple(bm, c, r, col, sd):
    b = quad_sphere(r, 1, (1, 1, 0.92), 0.03, sd)
    for v in b.verts:
        if v.co.z > r * 0.8:
            v.co.z -= r * 0.18
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)
    _stem(bm, c, r)
    leaf(bm, (c[0], c[1], c[2] + r * 1.05), sd * 37 % 360, r * 0.9, r * 0.5, 15, LEAFY)


def fr_peach(bm, c, r, col, sd):
    b = quad_sphere(r, 2, (1, 1, 0.97), 0.02, sd)
    for v in b.verts:
        if v.co.x > r * 0.6 and abs(v.co.y) < r * 0.25:
            v.co.x -= r * 0.12
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)
    leaf(bm, (c[0], c[1], c[2] + r * 0.95), sd * 37 % 360, r * 0.9, r * 0.5, 15, LEAFY)


def fr_star(bm, c, r, col, sd):
    star(bm, c, r * 1.35, col, yaw=90)   # faces -Y like every fruit (add_fruit turns it outward)


def fr_pomegranate(bm, c, r, col, sd):
    _sphere(bm, c, r, col, (1, 1, 0.95), 2, sd)
    for i in range(4):   # crown
        a = 2 * math.pi * i / 4
        box(bm, (c[0] + r * 0.18 * math.cos(a), c[1] + r * 0.18 * math.sin(a), c[2] + r * 1.05), (r * 0.16, r * 0.16, r * 0.3), col, yaw=math.degrees(a), taper=0.3)


def fr_pearl(bm, c, r, col, sd):
    _sphere(bm, c, r * 0.95, col, (1, 1, 1), 2, sd, 0)
    _stem(bm, c, r)


def fr_drop(bm, c, r, col, sd):
    b = quad_sphere(r, 2, (1, 1, 1), 0.0, sd)
    for v in b.verts:
        if v.co.z > 0:   # pull the top into a point
            k = 1 - (v.co.z / r) ** 1.2 * 0.92
            v.co.x *= k
            v.co.y *= k
            v.co.z *= 1.7
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)


def fr_flame(bm, c, r, col, sd):
    fr_drop(bm, c, r * 1.05, col, sd)


def fr_honeycomb(bm, c, r, col, sd):
    tube(bm, [(c[0], c[1], c[2] - r), (c[0], c[1], c[2] + r)], [r * 0.85, r * 0.85], col, 6)
    for z in (-0.5, 0.0, 0.5):
        tube(bm, [(c[0], c[1], c[2] + r * z - r * 0.08), (c[0], c[1], c[2] + r * z + r * 0.08)], [r * 0.95, r * 0.95], col, 6)


def fr_lantern(bm, c, r, col, sd):
    b = quad_sphere(r, 2, (1, 1, 1.3), 0.0, sd)
    for v in b.verts:
        k = 1 - abs(v.co.z / (r * 1.3)) ** 2 * 0.75
        v.co.x *= k
        v.co.y *= k
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)
    _stem(bm, (c[0], c[1], c[2] + r * 0.4), r)


def fr_bell(bm, c, r, col, sd):
    prof = [(0.12 * r, r * 1.0), (0.45 * r, r * 0.85), (0.6 * r, r * 0.2), (0.95 * r, -r * 0.7), (0.7 * r, -r * 0.8)]
    lathe(bm, [(p, c[2] + z) for p, z in prof], col, 12)
    # lathe builds around the origin: move the last piece over
    _sphere(bm, (c[0], c[1], c[2] - r * 0.85), r * 0.18, col, cuts=1, seed=sd)


def fr_snowflake(bm, c, r, col, sd):
    for i in range(3):
        box(bm, c, (r * 2.4, r * 0.22, r * 0.22), col, yaw=0, roll=0, pitch=60 * i)
    for i in range(6):
        a = math.radians(60 * i)
        p = (c[0] + r * 0.8 * math.cos(a), c[1], c[2] + r * 0.8 * math.sin(a))
        box(bm, p, (r * 0.5, r * 0.15, r * 0.15), col, pitch=-60 * i + 45)
        box(bm, p, (r * 0.5, r * 0.15, r * 0.15), col, pitch=-60 * i - 45)


def fr_heart(bm, c, r, col, sd):
    for sx in (-1, 1):
        _sphere(bm, (c[0] + sx * r * 0.42, c[1], c[2] + r * 0.25), r * 0.6, col, (1, 0.8, 1), 2, sd)
    b = quad_sphere(r * 0.7, 2, (1.2, 0.8, 1), 0, sd)
    for v in b.verts:
        if v.co.z < 0:
            k = 1 - min(1, -v.co.z / (r * 0.7)) * 0.9
            v.co.x *= k
            v.co.y *= k
            v.co.z *= 1.5
    bmesh.ops.translate(b, vec=Vector((c[0], c[1], c[2] - r * 0.05)), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)


def fr_grapes(bm, c, r, col, sd):
    rnd = random.Random(sd)
    for j in range(5):
        n = max(1, 4 - j)
        for i in range(n):
            a = 2 * math.pi * i / n + j
            rr = r * 0.32 * (n - 1) / 3 + 0.001
            _sphere(bm, (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a), c[2] + r * 0.6 - j * r * 0.38), r * 0.3, col, cuts=1, seed=sd * 10 + j * 4 + i)
    _stem(bm, (c[0], c[1], c[2] + r * 0.5), r * 0.6)


def fr_cherry(bm, c, r, col, sd):
    for dx in (-0.55, 0.55):
        p = (c[0] + dx * r, c[1], c[2] - r * 0.2)
        _sphere(bm, p, r * 0.6, col, cuts=1, seed=sd)
        tube(bm, [(p[0], p[1], p[2] + r * 0.5), (c[0], c[1], c[2] + r * 1.3)], [r * 0.06, r * 0.05], BARK_DARK, 4)


def fr_gear(bm, c, r, col, sd):
    tube(bm, [(c[0], c[1] - r * 0.25, c[2]), (c[0], c[1] + r * 0.25, c[2])], [r * 0.75, r * 0.75], col, 12)
    for i in range(8):
        a = 2 * math.pi * i / 8
        box(bm, (c[0] + r * 0.85 * math.cos(a), c[1], c[2] + r * 0.85 * math.sin(a)), (r * 0.3, r * 0.45, r * 0.3), col, pitch=-math.degrees(a))
    _sphere(bm, (c[0], c[1], c[2]), r * 0.35, col, (1, 1.5, 1), 1, sd)


def fr_bulb(bm, c, r, col, sd):
    _sphere(bm, (c[0], c[1], c[2] - r * 0.2), r * 0.85, col, (1, 1, 1.05), 2, sd)
    tube(bm, [(c[0], c[1], c[2] + r * 0.45), (c[0], c[1], c[2] + r * 0.9)], [r * 0.38, r * 0.34], ((7 + 0.5) * CW, 0.685, 0.825), 8)


def fr_chili(bm, c, r, col, sd):
    pts = [(c[0], c[1], c[2] + r * 0.9), (c[0] + r * 0.12, c[1], c[2] + r * 0.2), (c[0] + r * 0.05, c[1], c[2] - r * 0.6), (c[0] - r * 0.25, c[1], c[2] - r * 1.25)]
    tube(bm, pts, [r * 0.32, r * 0.36, r * 0.24, r * 0.03], col, 8)
    tube(bm, [(c[0], c[1], c[2] + r * 0.85), (c[0] + r * 0.12, c[1], c[2] + r * 1.25)], [r * 0.08, r * 0.06], c0(13), 4)


def fr_shard(bm, c, r, col, sd):
    b = bmesh.new()
    ring = [b.verts.new((c[0] + r * 0.45 * math.cos(2 * math.pi * k / 6), c[1] + r * 0.45 * math.sin(2 * math.pi * k / 6), c[2])) for k in range(6)]
    top = [b.verts.new((c[0] + r * 0.06 * math.cos(2 * math.pi * k / 6), c[1] + r * 0.06 * math.sin(2 * math.pi * k / 6), c[2] + r * 0.6)) for k in range(6)]
    bot = [b.verts.new((c[0] + r * 0.05 * math.cos(2 * math.pi * k / 6), c[1] + r * 0.05 * math.sin(2 * math.pi * k / 6), c[2] - r * 1.6)) for k in range(6)]
    for k in range(6):
        b.faces.new((ring[k], ring[(k + 1) % 6], top[(k + 1) % 6], top[k]))
        b.faces.new((bot[k], bot[(k + 1) % 6], ring[(k + 1) % 6], ring[k]))
    quad_cap(b, top)
    quad_cap(b, bot)
    uv_part(b, col)
    merge(bm, b)


def fr_orb(bm, c, r, col, sd):
    _sphere(bm, c, r, col, (1, 1, 1), 2, sd, 0)
    _stem(bm, c, r)


def fr_nugget(bm, c, r, col, sd):
    b = quad_sphere(r, 1, (1.2, 1, 0.85), 0.28, sd)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)


def fr_gem(bm, c, r, col, sd):
    lathe(bm, [(0.05 * r, -r * 1.0), (r * 0.8, r * 0.05), (r * 0.55, r * 0.45), (0.05 * r, r * 0.5)], col, 8)


def fr_truffle(bm, c, r, col, sd):
    b = quad_sphere(r, 2, (1, 1, 0.95), 0.0, sd)
    rnd = random.Random(sd)
    for v in b.verts:
        v.co *= 1 + rnd.uniform(-0.04, 0.12)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    uv_part(b, col)
    merge(bm, b)


def fr_yarn(bm, c, r, col, sd):
    _sphere(bm, c, r, col, (1, 1, 1), 2, sd, 0)
    for i in range(3):   # swirl bands
        tube(bm, [Vector(c) + Matrix.Rotation(math.radians(60 * i), 3, 'Z') @ Vector((r * 0.98 * math.cos(t), 0, r * 0.98 * math.sin(t))) for t in
                  [k * math.pi / 5 for k in range(11)]], [r * 0.07] * 11, col, 4)


FRUITS = {"apple": fr_apple, "peach": fr_peach, "star": fr_star, "pomegranate": fr_pomegranate, "pearl": fr_pearl,
          "drop": fr_drop, "flame": fr_flame, "honeycomb": fr_honeycomb, "lantern": fr_lantern, "bell": fr_bell,
          "snowflake": fr_snowflake, "heart": fr_heart, "grapes": fr_grapes, "cherry": fr_cherry, "gear": fr_gear,
          "bulb": fr_bulb, "chili": fr_chili, "shard": fr_shard, "orb": fr_orb, "nugget": fr_nugget, "gem": fr_gem,
          "truffle": fr_truffle, "yarn": fr_yarn}


def _relocate(fn):
    """Fruits built by lathe() are made around the origin: build them alone and move them."""
    def g(bm, c, r, col, sd):
        b = bmesh.new()
        fn(b, (0, 0, 0), r, col, sd)
        bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
        merge(bm, b)
    return g


FRUITS["bell"] = _relocate(fr_bell)
FRUITS["gem"] = _relocate(fr_gem)


def add_fruit(bm, kind, c, r, col, seed, glows, facing=-90.0):
    """Builds a fruit facing -Y at the origin, turns it to face `facing` (degrees, the direction
    from the tree outward; -90 = the front) and puts it at c. Glowing fruit bodies go to slot 1."""
    b = bmesh.new()
    FRUITS[kind](b, (0, 0, 0), r, col, seed)
    bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(facing + 90), 3, 'Z'), verts=b.verts)
    bmesh.ops.translate(b, vec=Vector(c), verts=b.verts)
    if glows:
        uvl = b.loops.layers.uv.verify()
        for f in b.faces:
            u, v = f.loops[0][uvl].uv
            if abs(u - col[0]) < 1e-4:   # the fruit body, not its stem or leaf
                f.material_index = 1
    merge(bm, b)


def build_daily(only=None):
    atlas = bpy.data.materials["M_GradientTexture"]
    glow = glow_atlas_material()
    root = bpy.data.collections.get("DailyRewards") or bpy.data.collections.new("DailyRewards")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    objs = []
    for k, (name, _canopy, _fruit, kind, glows, willow) in enumerate(TREES):
        if only and name not in only:
            continue
        sub_name = "DR_%02d_%s" % (k + 1, name)
        sub = bpy.data.collections.get(sub_name) or bpy.data.collections.new(sub_name)
        if sub.name not in [c.name for c in root.children]:
            root.children.link(sub)
        CAN = strip_uv(CANOPY_BAND, k)
        FRU = strip_uv(FRUIT_BAND, k)
        y = -60 - k * 4.5

        def done(bm, nm, x):
            o = bpy.data.objects.get(nm)
            if o:
                bpy.data.objects.remove(o, do_unlink=True)
            me = bpy.data.meshes.new(nm)
            bm.to_mesh(me)
            bm.free()
            me.materials.append(atlas)
            me.materials.append(glow)
            if not any(p.material_index == 1 for p in me.polygons):
                me.materials.pop(index=1)
            for p in me.polygons:
                p.use_smooth = True
            o = bpy.data.objects.new(nm, me)
            sub.objects.link(o)
            o.location = (x, y, 0)
            objs.append(o)

        bm = bmesh.new()   # Stage1: sprout in the tree's own leaf colour
        tube(bm, [(0, 0, 0), (0.01, 0, 0.18), (0.02, 0, 0.36)], [0.025, 0.02, 0.016], BARK, 6)
        for yaw, z, ln in ((20, 0.34, 0.2), (200, 0.34, 0.2), (110, 0.22, 0.15)):
            leaf(bm, (0.02, 0, z), yaw, ln, ln * 0.55, 25, CAN)
        done(bm, "SM_DR_%sTree_Stage1" % name, 1.5)
        for st, (s, x) in enumerate(((0.33, 3.3), (0.63, 6.0), (1.0, 10.0)), start=2):
            bm = bmesh.new()
            if st >= 3:
                mound(bm, s)
            lush_trunk(bm, s)
            puffs = lush_canopy(bm, s, CAN, willow and st >= 3)
            if st == 4:   # big fruit sitting on the outside of the canopy, mostly facing the front
                for i, p in enumerate(fruit_spots(s, seed=k)):
                    add_fruit(bm, kind, (p.x, p.y, p.z), FRUIT_SIZE, FRU, k * 100 + i, glows, math.degrees(math.atan2(p.y, p.x)))
            done(bm, "SM_DR_%sTree_Stage%d" % (name, st), x)
        bm = bmesh.new()
        add_fruit(bm, kind, (0, 0, 0.3), 0.17, FRU, 999, glows)
        zs = [v.co.z for v in bm.verts]
        bmesh.ops.translate(bm, vec=Vector((0, 0, -min(zs))), verts=bm.verts)
        done(bm, "SM_DR_%s" % name, 13.5)
    return check_closed(objs)
