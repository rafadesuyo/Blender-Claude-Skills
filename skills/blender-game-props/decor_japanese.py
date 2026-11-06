# gab house decorations, Japanese set (Dante's 4 "Japanese Style" sheets, 2026-10-29): Bathroom /
# Living Room / Bedroom / Kitchen, 12 items each. Same rules and helpers as decor.py (one atlas
# material, rounded boxes, lathed round parts, every item closed, pivot at the bottom centre, front -Y).
# Collections: DecorJapanese > DecorJP_Bathroom / DecorJP_LivingRoom / DecorJP_Bedroom / DecorJP_Kitchen,
# objects SM_DecorJP_<Name> (rows at y -280 ...).
#   exec(open(r"<skills>/blender-game-props/decor_japanese.py").read())
#   build_japanese()                 # every item; build_japanese(["Kitchen"]) for one area
#   render_japanese_previews(dir)    # one framed PNG per item (dir/<area>/<name>.png)
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

exec(open(_skill("blender-game-props/decor.py")).read())

SAKURA = S("r3", 14, 0.0, 0.35)      # soft cherry-blossom pink
HOTPINK = S("r4", 11, 0.05, 0.4)     # futon / cushion pink
PINK_L = S("r4", 1, 0.2, 0.7)        # pale pink (kimono, scroll mount)
NAVY = S("r3", 19, 0.2, 0.7)         # noren / indigo
WATER = S("r1", 15, 0.0, 0.35)
PAPER = S("r2", 9, 0.15, 0.3)        # shoji paper (cream)
PAPER_GLOW = S("r4", 8, 0.0, 0.3)    # lit lantern paper
BAMBOO = S("r1", 11, 0.25, 0.5)
BAMBOO_D = S("r1", 11, 0.6, 0.85)
STONE = S("r3", 24, 0.1, 0.5)
STONE_D = S("r3", 24, 0.45, 0.85)
STONE_L = S("r2", 8, 0.15, 0.5)
MATCHA = S("r1", 0, 0.0, 0.15)
TATAMI = S("r1", 4, 0.45, 0.8)
TATAMI_D = S("r1", 4, 0.1, 0.3)
JRED = S("r4", 14, 0.0, 0.35)
GREEN_D = S("r3", 0, 0.0, 0.35)
BARK = S("r2", 0, 0.1, 0.5)


# ---------- Japanese helpers ----------
def prism(bm, pts, y, depth, s):
    """A flat shape from an outline [(x, z), ...] (convex, counter-clockwise seen from -Y), depth along Y."""
    b = bmesh.new()
    fr = [b.verts.new((x, y - depth / 2, z)) for x, z in pts]
    bk = [b.verts.new((x, y + depth / 2, z)) for x, z in pts]
    b.faces.new(fr)
    b.faces.new(list(reversed(bk)))
    n = len(pts)
    for k in range(n):
        k2 = (k + 1) % n
        b.faces.new((fr[k], bk[k], bk[k2], fr[k2]))
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    for f in b.faces:
        f.smooth = False
    _uv(b, s)
    _merge(bm, b)


def _aim(b, a, d):
    """Turns a part built along +Z from the origin so it runs from a along d."""
    q = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized())
    for v in b.verts:
        v.co = q @ v.co + Vector(a)


def bamboo(bm, a, b_, r, s=BAMBOO, node=BAMBOO_D, step=0.22):
    """A bamboo stalk from a to b_ with a node ring every step."""
    a, b_ = Vector(a), Vector(b_)
    L = (b_ - a).length
    b = bmesh.new()
    cyl(b, (0, 0, 0), r, L, s, segs=12, bevel=0.15)
    z = step
    while z < L - step * 0.4:
        ring(b, (0, 0, z), r, r * 0.2, node, segs=12, rsegs=6)
        z += step
    _aim(b, a, b_ - a)
    _merge(bm, b)


def blossom(bm, c, R, face=None, petal=SAKURA, centre=HOTPINK):
    """A small 5-petal sakura flower (cheap: low-segment petals)."""
    b = bmesh.new()
    for k in range(5):
        a = 2 * math.pi * k / 5
        sphere(b, (math.cos(a) * R * 0.5, math.sin(a) * R * 0.5, 0), (R * 0.42, R * 0.32, R * 0.12), petal, rot=(0, 0, math.degrees(a)), segs=(8, 4))
    sphere(b, (0, 0, R * 0.08), (R * 0.2, R * 0.2, R * 0.14), centre, segs=(6, 4))
    _merge(bm, b, face, c)


def sakura(bm, base, h=0.5, spread=0.25, n=3, seed=1, R=0.035, bark=BARK):
    """Cherry branches growing from base, flowers along the outer part of each."""
    rnd = random.Random(seed)
    base = Vector(base)
    for k in range(n):
        a = math.pi * (0.15 + 0.7 * (k + 0.5) / n) + rnd.uniform(-0.15, 0.15)
        dx, dy = math.cos(a), rnd.uniform(-0.3, 0.3)
        tip = base + Vector((dx * spread, dy * spread * 0.5, h * rnd.uniform(0.8, 1.1)))
        mid = base.lerp(tip, 0.45) + Vector((-dx * 0.04, 0, 0.03))
        capsule(bm, base, mid, 0.011, bark, segs=6)
        capsule(bm, mid, tip, 0.008, bark, segs=6)
        twig = mid + Vector((dx * spread * 0.45 + rnd.uniform(-0.05, 0.05), rnd.uniform(-0.06, 0.06), h * 0.35))
        capsule(bm, mid, twig, 0.006, bark, segs=6)
        for p0, p1, m in ((mid, tip, 4), (mid, twig, 2)):
            for i in range(m):
                p = p0.lerp(p1, 0.35 + 0.65 * (i + 1) / m) + Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), rnd.uniform(-0.01, 0.02)))
                blossom(bm, tuple(p), R * rnd.uniform(0.85, 1.15), face=(rnd.uniform(40, 100), rnd.uniform(-30, 30), rnd.uniform(-40, 40)))


def rock(bm, c, size, seed, s=STONE_D, flat=0.7):
    """A faceted lumpy stone."""
    rnd = random.Random(seed)
    b = bmesh.new()
    sphere(b, (0, 0, 0), (size * rnd.uniform(0.95, 1.2), size * rnd.uniform(0.8, 1.05), size * flat), s, segs=(9, 5))
    for v in b.verts:
        v.co *= rnd.uniform(0.88, 1.08)
    for f in b.faces:
        f.smooth = False
    _merge(bm, b, (rnd.uniform(-10, 10), rnd.uniform(-10, 10), rnd.uniform(0, 180)), c)


def tub(bm, c, r, h, s, band=WOOD_D, staves=16, bands=(), water=True, wall=0.03, fill=0.8, segs=28):
    """A round tub / basin: wall, inner floor, optional water, stave lines and hoops."""
    zf = h * fill - 0.012 if water else h * 0.12
    prof = [(0, 0), (r * 0.96, 0), (r, 0.02), (r, h - 0.008), (r - 0.008, h), (r - wall + 0.008, h), (r - wall, h - 0.008), (r - wall, zf), (0, zf)]
    lathe(bm, prof, s, c, segs=segs)
    if water:
        cyl(bm, (c[0], c[1], c[2] + zf - 0.02), r - wall + 0.01, 0.032, WATER, segs=segs, bevel=0.05)
    for k in range(staves):
        a = 2 * math.pi * (k + 0.5) / staves
        rbox(bm, (c[0] + r * math.cos(a), c[1] + r * math.sin(a), c[2] + h / 2), (0.008, 0.006, h * 0.9), band, r=0.002, rot=(0, 0, math.degrees(a)))
    for z in bands:
        ring(bm, (c[0], c[1], c[2] + z), r + 0.003, 0.012, band, segs=segs, rsegs=6)


def shoji(bm, c, w, h, cols, rows, frame=WOOD_D, paper=PAPER, bar=0.035, depth=0.04, rotz=0.0):
    """A shoji panel standing on c (bottom centre), in the XZ plane: frame, lattice, paper."""
    b = bmesh.new()
    rbox(b, (0, 0, h / 2), (w - bar, depth * 0.35, h - bar), paper, r=0.002)
    for x in (-w / 2 + bar / 2, w / 2 - bar / 2):
        rbox(b, (x, 0, h / 2), (bar, depth, h), frame, r=0.006)
    for z in (bar / 2, h - bar / 2):
        rbox(b, (0, 0, z), (w - bar * 1.5, depth * 0.96, bar), frame, r=0.006)
    t = bar * 0.4
    for k in range(1, cols):
        rbox(b, (-w / 2 + bar + (w - 2 * bar) * k / cols, 0, h / 2), (t, depth * 0.7, h - bar * 1.5), frame, r=0.002)
    for k in range(1, rows):
        rbox(b, (0, 0, bar + (h - 2 * bar) * k / rows), (w - bar * 1.5, depth * 0.66, t), frame, r=0.002)
    _merge(bm, b, (0, 0, rotz), c)


def andon(bm, c, w, h, leg=0.06, frame=WOOD_D, glow=PAPER_GLOW):
    """A square paper lantern: little legs, base, glowing paper box in a wooden frame."""
    x0, y0, z0 = c
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(bm, (x0 + sx * (w / 2 - 0.018), y0 + sy * (w / 2 - 0.018), z0 + leg / 2), (0.034, 0.034, leg), frame, r=0.006)
    rbox(bm, (x0, y0, z0 + leg + 0.012), (w + 0.01, w + 0.01, 0.024), frame, r=0.006)
    zb = z0 + leg + 0.024
    rbox(bm, (x0, y0, zb + h / 2), (w * 0.9, w * 0.9, h), glow, r=0.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(bm, (x0 + sx * (w / 2 - 0.013), y0 + sy * (w / 2 - 0.013), zb + h / 2), (0.026, 0.026, h), frame, r=0.005)
    for z in (zb + 0.012, zb + h * 0.55, zb + h - 0.012):
        for sy in (-1, 1):
            rbox(bm, (x0, y0 + sy * (w / 2 - 0.01), z), (w - 0.01, 0.02, 0.02), frame, r=0.004)
            rbox(bm, (x0 + sy * (w / 2 - 0.01), y0, z), (0.02, w - 0.01, 0.02), frame, r=0.004)
    for sy in (-1, 1):
        rbox(bm, (x0, y0 + sy * (w * 0.45 + 0.004), zb + h / 2), (0.012, 0.012, h - 0.02), frame, r=0.003)
        rbox(bm, (x0 + sy * (w * 0.45 + 0.004), y0, zb + h / 2), (0.012, 0.012, h - 0.02), frame, r=0.003)
    rbox(bm, (x0, y0, zb + h + 0.012), (w + 0.03, w + 0.03, 0.024), frame, r=0.006)


def tassel(bm, base, d, s=GOLD):
    base, d = Vector(base), Vector(d).normalized()
    capsule(bm, base, base + d * 0.03, 0.01, s, segs=8)
    sphere(bm, tuple(base + d * 0.055), (0.02, 0.02, 0.02), s, segs=(8, 5))


def fern(bm, c, n=6, L=0.14, seed=3, up=0.6):
    """A little clump of leaves fanning out from c."""
    rnd = random.Random(seed)
    for k in range(n):
        a = 2 * math.pi * k / n + rnd.uniform(-0.3, 0.3)
        leaf(bm, c, (math.cos(a), math.sin(a), up + rnd.uniform(-0.2, 0.3)), L * rnd.uniform(0.8, 1.15), L * 0.45, LEAF if k % 2 else LEAF_L, roll=math.degrees(a) + 90, thick=0.008)


def scroll(bm, mount, paint):
    """A hanging scroll: mount + paper, rods with dark knobs, a hanging cord. paint(bm) adds the picture
    (the paper's front is at y -0.012, its centre at z 0.55)."""
    rbox(bm, (0, 0.004, 0.56), (0.42, 0.012, 0.92), mount, r=0.004)
    rbox(bm, (0, -0.004, 0.57), (0.34, 0.012, 0.72), PAPER, r=0.003)
    capsule(bm, (-0.23, 0.0, 1.03), (0.23, 0.0, 1.03), 0.014, WOOD_D, segs=8)
    capsule(bm, (-0.24, 0.0, 0.085), (0.24, 0.0, 0.085), 0.02, WOOD_D, segs=10)
    for sx in (-1, 1):
        sphere(bm, (sx * 0.265, 0, 0.085), (0.026, 0.026, 0.026), BLACK, segs=(10, 6))
        capsule(bm, (sx * 0.17, 0.0, 1.03), (0, 0.0, 1.16), 0.005, BROWN, segs=6)
    ring(bm, (0, 0, 1.175), 0.016, 0.005, BROWN, rot=(90, 0, 0), segs=10, rsegs=5)
    paint(bm)


def zabuton(bm, s, petal, centre, w=0.6):
    rbox(bm, (0, 0, 0.06), (w, w, 0.12), s, r=0.05)
    rbox(bm, (0, 0, 0.12), (w * 0.86, w * 0.86, 0.012), s, r=0.005)
    daisy(bm, (0, 0, 0.13), w * 0.2, petal=petal, centre=centre, n=5, h=0.012)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tassel(bm, (sx * (w / 2 - 0.02), sy * (w / 2 - 0.02), 0.06), (sx, sy, 0), GOLD)


def jp_vase(bm, c, s=BLACK, scale=1.0):
    k = scale
    lathe(bm, [(0, 0), (0.07 * k, 0), (0.12 * k, 0.07 * k), (0.115 * k, 0.15 * k), (0.05 * k, 0.21 * k), (0.038 * k, 0.25 * k), (0.048 * k, 0.27 * k), (0, 0.27 * k)], s, c)
    return c[2] + 0.26 * k


# ---------- Bathroom ----------
def wooden_ofuro(bm):
    tub(bm, (0, 0, 0), 0.5, 0.62, WOOD_L, band=WOOD, staves=22, bands=(0.12, 0.5))
    rbox(bm, (0, 0.44, 0.76), (0.16, 0.14, 0.32), WOOD, r=0.02)
    bamboo(bm, (0, 0.4, 0.82), (0, 0.16, 0.8), 0.026, step=0.1)
    capsule(bm, (0, 0.15, 0.79), (0, 0.12, 0.47), 0.012, WATER, segs=8)


def stone_bath_stool(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.13, 0, 0.12), (0.09, 0.26, 0.24), STONE, r=0.03)
    rbox(bm, (0, 0, 0.27), (0.44, 0.32, 0.08), STONE, r=0.03)


def wooden_bucket(bm):
    tub(bm, (0, 0, 0), 0.18, 0.2, WOOD_L, band=WOOD, staves=14, bands=(0.05, 0.15), wall=0.02)
    rbox(bm, (0.19, 0, 0.15), (0.025, 0.13, 0.12), WHITE, r=0.008)
    rbox(bm, (0.15, 0, 0.212), (0.1, 0.13, 0.022), WHITE, r=0.008)
    rbox(bm, (0.204, 0, 0.12), (0.006, 0.132, 0.016), NAVY, r=0.002)


def bamboo_shower(bm):
    cyl(bm, (0, 0, 0), 0.3, 0.06, WATER, segs=24, bevel=0.1)
    for k in range(10):
        a = 2 * math.pi * k / 10
        rock(bm, (0.32 * math.cos(a), 0.32 * math.sin(a), 0.06), 0.09, 70 + k)
    bamboo(bm, (0.08, 0.2, 0), (0.08, 0.2, 1.2), 0.045)
    bamboo(bm, (0.08, 0.2, 1.06), (-0.05, -0.08, 0.98), 0.028, step=0.12)
    capsule(bm, (-0.06, -0.1, 0.955), (-0.07, -0.11, 0.08), 0.012, WATER, segs=8)
    fern(bm, (0.12, 0.22, 0.7), 3, 0.12, seed=4, up=0.2)


def rock_onsen_divider(bm):
    rnd = random.Random(81)
    for k in range(9):
        x = -0.4 + 0.1 * k
        bamboo(bm, (x, 0.12, 0), (x, 0.12, rnd.uniform(0.82, 0.95)), 0.045)
    for z in (0.3, 0.68):
        bamboo(bm, (-0.47, 0.06, z), (0.47, 0.06, z), 0.02, step=0.3)
    for i, (x, sz) in enumerate(((-0.33, 0.2), (-0.08, 0.24), (0.2, 0.2), (0.38, 0.15), (0.05, 0.13), (-0.2, 0.13))):
        rock(bm, (x, -0.08 + (0.06 if i > 3 else 0), sz * 0.55 + (0.2 if i > 3 else 0)), sz, 90 + i)
    for p in ((-0.42, -0.02, 0.15), (0.43, -0.05, 0.15), (0.3, 0.0, 0.3)):
        fern(bm, p, 6, 0.15, seed=int(p[0] * 100))


def jp_towel_rack(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.32, 0, 0.56), (0.06, 0.06, 1.08), WOOD, r=0.015)
        rbox(bm, (sx * 0.32, 0, 0.03), (0.09, 0.36, 0.06), WOOD_D, r=0.015)
    for z in (0.35, 0.7):
        capsule(bm, (-0.3, 0, z), (0.3, 0, z), 0.018, WOOD_D, segs=8)
    rbox(bm, (0, 0, 1.11), (0.74, 0.26, 0.035), WOOD_D, r=0.01)
    for x, z in ((-0.12, 1.19), (0.12, 1.19), (0.0, 1.31)):
        cyl(bm, (x - 0.13, 0, z), 0.065, 0.26, WHITE, rot=(0, 90, 0), segs=16)
        ring(bm, (x + 0.09, 0, z), 0.066, 0.006, NAVY, rot=(0, 90, 0), segs=16, rsegs=5)
    rbox(bm, (0, -0.025, 0.6), (0.4, 0.025, 0.22), WHITE, r=0.008)
    rbox(bm, (0, 0.025, 0.63), (0.4, 0.025, 0.16), WHITE, r=0.008)
    rbox(bm, (0, -0.04, 0.53), (0.402, 0.006, 0.02), NAVY, r=0.002)


def wash_basin(bm):
    tub(bm, (0, 0, 0), 0.3, 0.32, STONE, staves=0, wall=0.06, fill=0.82, segs=20)
    bamboo(bm, (0.3, 0.16, 0), (0.3, 0.16, 0.7), 0.04)
    bamboo(bm, (0.3, 0.16, 0.62), (0.08, 0.05, 0.56), 0.024, step=0.1)
    capsule(bm, (0.07, 0.045, 0.545), (0.06, 0.04, 0.26), 0.01, WATER, segs=8)
    for i, p in enumerate(((-0.33, -0.12, 0.05), (-0.22, -0.27, 0.04), (0.28, -0.22, 0.04))):
        rock(bm, p, 0.07, 120 + i)
    fern(bm, (-0.3, 0.12, 0.02), 7, 0.16, seed=12)
    fern(bm, (0.36, 0.05, 0.02), 5, 0.12, seed=13)


def aroma_lantern(bm):
    lathe(bm, [(0, 0), (0.2, 0), (0.2, 0.06), (0.15, 0.1), (0, 0.1)], STONE, segs=6, smooth=False)
    cyl(bm, (0, 0, 0.1), 0.07, 0.26, STONE, segs=8)
    lathe(bm, [(0, 0.35), (0.12, 0.35), (0.19, 0.42), (0, 0.42)], STONE, segs=6, smooth=False)
    rbox(bm, (0, 0, 0.53), (0.22, 0.22, 0.22), STONE, r=0.02)
    rbox(bm, (0, 0, 0.53), (0.12, 0.24, 0.13), PAPER_GLOW, r=0.006)
    rbox(bm, (0, 0, 0.53), (0.24, 0.12, 0.13), PAPER_GLOW, r=0.006)
    lathe(bm, [(0, 0.63), (0.27, 0.63), (0.29, 0.67), (0.16, 0.74), (0.05, 0.79), (0, 0.79)], STONE, segs=6, smooth=False)
    sphere(bm, (0, 0, 0.83), (0.045, 0.045, 0.05), STONE, segs=(8, 5))
    for k in range(3):
        a = math.radians(30 + 120 * k)
        sphere(bm, (0.24 * math.cos(a), 0.24 * math.sin(a), 0.675), (0.05, 0.04, 0.02), LEAF_D, segs=(8, 4))


def jp_bath_mat(bm):
    rbox(bm, (0, 0, 0.012), (0.8, 0.5, 0.024), TATAMI, r=0.008)
    for k in range(13):
        y = -0.21 + k * 0.035
        capsule(bm, (-0.36, y, 0.022), (0.36, y, 0.022), 0.006, TATAMI_D, segs=6)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.38, 0, 0.016), (0.045, 0.505, 0.028), WICKER_D, r=0.006)


def bath_set(bm):
    cyl(bm, (0, 0, 0), 0.17, 0.03, WOOD_D, segs=28, sx=1.55)
    ring(bm, (0, 0, 0.032), 0.165, 0.012, WOOD_D, segs=28, rsegs=6, sx=1.55)
    lathe(bm, [(0, 0.03), (0.05, 0.03), (0.055, 0.05), (0.055, 0.22), (0.035, 0.26), (0, 0.26)], GREEN_D, (-0.12, 0.02, 0))
    cyl(bm, (-0.12, 0.02, 0.255), 0.016, 0.04, BLACK, segs=8)
    rbox(bm, (-0.14, 0.02, 0.3), (0.05, 0.02, 0.015), BLACK, r=0.004)
    sprig(bm, (-0.12, -0.036, 0.14), 0.045, CREAM)
    lathe(bm, [(0, 0.03), (0.045, 0.03), (0.048, 0.05), (0.048, 0.16), (0.03, 0.19), (0, 0.19)], CREAM, (0.0, 0.03, 0))
    cyl(bm, (0, 0.03, 0.185), 0.014, 0.035, WOOD, segs=8)
    rbox(bm, (-0.018, 0.03, 0.225), (0.045, 0.018, 0.013), WOOD, r=0.004)
    sprig(bm, (0, -0.019, 0.11), 0.04, SAGE_D)
    rbox(bm, (0.15, -0.02, 0.055), (0.12, 0.08, 0.05), SAGE, r=0.018)
    leaf(bm, (0.15, -0.02, 0.08), (0.3, 0.2, 0.25), 0.06, 0.03, LEAF, roll=30, thick=0.006)


def potted_bamboo(bm):
    lathe(bm, [(0, 0), (0.12, 0), (0.15, 0.2), (0.16, 0.22), (0, 0.22)], TERRA)
    cyl(bm, (0, 0, 0.2), 0.14, 0.03, SOIL, segs=20)
    rnd = random.Random(55)
    for k, (x, y, h) in enumerate(((-0.04, 0.02, 0.85), (0.05, -0.02, 0.7), (0.0, 0.06, 0.95))):
        top = (x + rnd.uniform(-0.04, 0.04), y, h)
        bamboo(bm, (x, y, 0.2), top, 0.018, step=0.16)
        for z in (h * 0.6, h * 0.8, h):
            p = Vector((x, y, 0.2)).lerp(Vector(top), (z - 0.2) / (h - 0.2))
            for j in range(3):
                a = 2 * math.pi * (j + k * 0.3) / 3 + rnd.uniform(-0.3, 0.3)
                leaf(bm, tuple(p), (math.cos(a), math.sin(a), rnd.uniform(-0.3, 0.3)), 0.13, 0.035, LEAF if j % 2 else LEAF_L, roll=math.degrees(a) + 90, thick=0.006)


def sliding_screen(bm):
    shoji(bm, (0, 0, 0.05), 0.72, 1.45, 3, 4)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.3, 0, 0.03), (0.08, 0.3, 0.06), WOOD_D, r=0.015)
    rbox(bm, (0, 0, 0.055), (0.72, 0.06, 0.03), WOOD_D, r=0.008)


# ---------- Living room ----------
def low_tea_table(bm):
    for a in range(4):
        ang = math.radians(45 + 90 * a)
        rbox(bm, (0.3 * math.cos(ang), 0.3 * math.sin(ang), 0.11), (0.07, 0.07, 0.22), WOOD_D, r=0.015)
    cyl(bm, (0, 0, 0.21), 0.47, 0.06, WOOD, segs=32)
    rbox(bm, (0.05, -0.03, 0.283), (0.44, 0.3, 0.025), BLACK, r=0.008)
    lathe(bm, [(0, 0.29), (0.07, 0.29), (0.095, 0.33), (0.08, 0.38), (0.035, 0.395), (0, 0.395)], TERRA, (0.1, 0.0, 0))
    sphere(bm, (0.1, 0.0, 0.405), (0.018, 0.018, 0.015), TERRA, segs=(8, 5))
    capsule(bm, (0.17, 0, 0.33), (0.22, -0.01, 0.37), 0.014, TERRA, segs=8)
    ring(bm, (0.02, 0, 0.34), 0.035, 0.008, TERRA, rot=(90, 0, 0), segs=12, rsegs=5)
    for x, y in ((-0.1, -0.1), (0.05, -0.12)):
        lathe(bm, [(0, 0.295), (0.025, 0.295), (0.035, 0.35), (0, 0.35)], MATCHA, (x, y, 0), segs=14)
    top = jp_vase(bm, (-0.26, 0.2, 0.24), BLACK, 0.45)
    sakura(bm, (-0.26, 0.2, top), 0.3, 0.16, 2, seed=5, R=0.028)


def zabuton_cushion(bm):
    zabuton(bm, MATCHA, CREAM, MATCHA)


def floor_chair(bm):
    rbox(bm, (0, 0, 0.05), (0.56, 0.6, 0.1), WOOD, r=0.025)
    rbox(bm, (0, -0.03, 0.135), (0.48, 0.48, 0.08), MATCHA, r=0.035)
    daisy(bm, (0, -0.03, 0.18), 0.09, petal=CREAM, centre=MATCHA, n=5, h=0.01)
    b = bmesh.new()
    rbox(b, (0, 0, 0.33), (0.54, 0.07, 0.66), WOOD, r=0.03)
    rbox(b, (0, 0, 0.53), (0.16, 0.074, 0.065), BLACK, r=0.02)
    rbox(b, (0, -0.02, 0.24), (0.42, 0.04, 0.32), MATCHA, r=0.03)
    _merge(bm, b, (-14, 0, 0), (0, 0.27, 0.06))


def paper_lantern(bm):
    andon(bm, (0, 0, 0), 0.32, 0.5, leg=0.08)


def indoor_bonsai(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(bm, (sx * 0.17, sy * 0.1, 0.012), (0.05, 0.04, 0.024), NAVY, r=0.008)
    rbox(bm, (0, 0, 0.09), (0.46, 0.3, 0.13), NAVY, r=0.02)
    rbox(bm, (0, 0, 0.15), (0.42, 0.26, 0.02), SOIL, r=0.006)
    for x, y in ((-0.12, -0.06), (0.14, 0.05), (0.05, -0.08)):
        sphere(bm, (x, y, 0.16), (0.05, 0.04, 0.02), LEAF_D, segs=(8, 4))
    pts = [Vector(p) for p in ((0.02, 0, 0.15), (0.07, 0, 0.26), (-0.03, 0, 0.36), (0.02, 0, 0.46), (-0.02, 0, 0.53))]
    for k in range(len(pts) - 1):
        capsule(bm, pts[k], pts[k + 1], 0.045 - k * 0.008, BARK, segs=10)
    clouds = [((-0.2, 0, 0.4), 0.13), ((0.2, 0.02, 0.48), 0.12), ((0.0, 0, 0.6), 0.14), ((-0.12, 0.05, 0.62), 0.09), ((0.12, -0.02, 0.36), 0.1)]
    for (c, r), p in zip(clouds, (pts[2], pts[3], pts[4], pts[4], pts[1])):
        capsule(bm, p, Vector(c) * 0.85 + p * 0.15, 0.018, BARK, segs=6)
        sphere(bm, c, (r, r * 0.85, r * 0.55), LEAF_D, segs=(14, 7))
        sphere(bm, (c[0] - 0.02, c[1] - 0.02, c[2] + r * 0.25), (r * 0.75, r * 0.65, r * 0.42), LEAF, segs=(14, 7))


def _mountain_painting(bm):
    sphere(bm, (0.08, -0.012, 0.8), (0.055, 0.004, 0.055), JRED, segs=(16, 6))
    prism(bm, [(-0.13, 0.4), (0.13, 0.4), (0.0, 0.62)], -0.012, 0.006, STONE)
    prism(bm, [(-0.042, 0.555), (0.042, 0.555), (0.0, 0.62)], -0.016, 0.006, WHITE)
    for x in (-0.14, -0.09):
        prism(bm, [(x - 0.04, 0.4), (x + 0.04, 0.4), (x, 0.47)], -0.016, 0.006, STONE_D)


def hanging_scroll(bm):
    scroll(bm, CREAM_D, _mountain_painting)


def room_divider(bm):
    w = 0.46
    p = Vector((0, 0, 0))
    centres = []
    for a in (-20, 20, -20):
        d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        centres.append((p + d * w / 2, a))
        p = p + d * w
    off = p / 2
    for c, a in centres:
        shoji(bm, tuple(c - off), w, 1.5, 2, 5, depth=0.035, rotz=a)


def irori_hearth(bm):
    for sy in (-1, 1):
        rbox(bm, (0, sy * 0.4, 0.08), (0.92, 0.12, 0.16), WOOD, r=0.02)
        rbox(bm, (sy * 0.4, 0, 0.08), (0.12, 0.92, 0.16), WOOD, r=0.02)
    rbox(bm, (0, 0, 0.06), (0.7, 0.7, 0.12), GREY, r=0.01)
    rnd = random.Random(7)
    for k in range(5):
        a = 2 * math.pi * k / 5
        capsule(bm, (0.12 * math.cos(a), 0.12 * math.sin(a), 0.135), (0.03 * math.cos(a), 0.03 * math.sin(a), 0.15), 0.025, BLACK, segs=8)
    for k in range(4):
        sphere(bm, (rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), 0.15), (0.03, 0.03, 0.02), FLAME, segs=(8, 4))
    capsule(bm, (0, 0, 0.55), (0, 0, 1.55), 0.022, BLACK, segs=8)
    rbox(bm, (0, 0, 0.95), (0.3, 0.05, 0.07), WOOD, r=0.02)
    sphere(bm, (0, 0, 0.32), (0.16, 0.16, 0.12), BLACK)
    cyl(bm, (0, 0, 0.42), 0.08, 0.025, BLACK, segs=16)
    sphere(bm, (0, 0, 0.455), (0.02, 0.02, 0.015), BLACK, segs=(8, 5))
    capsule(bm, (-0.13, 0, 0.34), (-0.21, 0, 0.4), 0.02, BLACK, segs=8)
    ring(bm, (0, 0, 0.4), 0.13, 0.01, BLACK, rot=(90, 0, 0), segs=20, rsegs=5)
    capsule(bm, (0, 0, 0.53), (0, 0, 0.56), 0.012, BLACK, segs=6)


def wooden_cabinet(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(bm, (sx * 0.36, sy * 0.15, 0.03), (0.05, 0.05, 0.06), WOOD_D, r=0.01)
    rbox(bm, (0, 0, 0.3), (0.82, 0.38, 0.5), WOOD, r=0.02)
    rbox(bm, (0, 0, 0.565), (0.86, 0.42, 0.035), WOOD_D, r=0.01)
    for sx in (-1, 1):
        shoji(bm, (sx * 0.19, -0.195, 0.08), 0.37, 0.36, 3, 2, depth=0.02, bar=0.03)
        rbox(bm, (sx * 0.04, -0.21, 0.26), (0.012, 0.01, 0.06), BLACK, r=0.003)
    top = jp_vase(bm, (-0.25, 0.02, 0.583), BLACK, 0.55)
    sakura(bm, (-0.25, 0.02, top), 0.35, 0.18, 2, seed=8, R=0.03)
    lathe(bm, [(0, 0.583), (0.035, 0.583), (0.045, 0.63), (0, 0.63)], MATCHA, (0.2, -0.02, 0), segs=14)
    cyl(bm, (0.2, -0.02, 0.583), 0.08, 0.012, WOOD_D, segs=16)


def decorative_fan(bm):
    rbox(bm, (0, 0.02, 0.02), (0.3, 0.12, 0.04), BLACK, r=0.012)
    for sx in (-1, 1):
        capsule(bm, (sx * 0.06, 0.02, 0.03), (sx * 0.02, 0.02, 0.13), 0.012, BLACK, segs=8)
    pv = Vector((0, 0, 0.12))
    n = 13
    for k in range(n):
        a = math.radians(10 + 160 * k / (n - 1))
        d = Vector((math.cos(a), 0, math.sin(a)))
        rbox(bm, tuple(pv + d * 0.2), (0.016, 0.006, 0.4), BLACK, r=0.003, rot=(0, 90 - math.degrees(a), 0))
    for k in range(n - 1):
        a = math.radians(10 + 160 * (k + 0.5) / (n - 1))
        d = Vector((math.cos(a), 0, math.sin(a)))
        y = -0.008 if k % 2 else -0.012
        rbox(bm, tuple(pv + d * 0.29 + Vector((0, y, 0))), (0.075, 0.004, 0.2), WHITE, r=0.001, rot=(0, 90 - math.degrees(a), 0))
    for a, rr, R in ((40, 0.3, 0.06), (95, 0.28, 0.07), (145, 0.3, 0.055), (68, 0.33, 0.035), (122, 0.34, 0.035)):
        d = Vector((math.cos(math.radians(a)), 0, math.sin(math.radians(a))))
        daisy(bm, tuple(pv + d * rr + Vector((0, -0.017, 0))), R, petal=JRED, centre=WHITE, n=5, h=0.004, face=(90, 0, 0))
    cyl(bm, (0, -0.015, 0.12), 0.02, 0.03, GOLD, rot=(90, 0, 0), segs=12)


def ikebana_vase(bm):
    top = jp_vase(bm, (0, 0, 0), BLACK, 1.0)
    sakura(bm, (0, 0, top), 0.5, 0.25, 3, seed=11, R=0.04)


def tatami_rug(bm):
    rbox(bm, (0, 0, 0.02), (1.4, 0.9, 0.04), TATAMI, r=0.01)
    for k in range(17):
        x = -0.6 + k * 0.075
        rbox(bm, (x, 0, 0.0405), (0.006, 0.76, 0.003), TATAMI_D, r=0.001)
    for sy in (-1, 1):
        rbox(bm, (0, sy * 0.415, 0.022), (1.41, 0.08, 0.042), LEAF_D, r=0.008)


# ---------- Bedroom ----------
def futon_bed(bm):
    rbox(bm, (0, 0, 0.06), (1.0, 1.9, 0.12), WHITE, r=0.05)
    rbox(bm, (0, -0.22, 0.15), (1.04, 1.36, 0.1), HOTPINK, r=0.05)
    rbox(bm, (0, 0.42, 0.15), (1.02, 0.14, 0.11), WHITE, r=0.05)
    rbox(bm, (0, 0.7, 0.17), (0.5, 0.28, 0.1), CREAM, r=0.045)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.24, 0.7, 0.17), (0.05, 0.285, 0.105), HOTPINK, r=0.03)
    for x, y, R in ((-0.25, -0.55, 0.13), (0.22, -0.2, 0.11), (-0.18, 0.12, 0.09), (0.3, -0.75, 0.08), (0.05, -0.35, 0.06), (0.3, 0.15, 0.06)):
        daisy(bm, (x, y, 0.2), R, petal=PINK_L, centre=HOTPINK, n=5, h=0.01)


def jp_pillow(bm):
    rbox(bm, (0, 0, 0.075), (0.42, 0.24, 0.15), CREAM, r=0.065)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.19, 0, 0.075), (0.06, 0.246, 0.155), HOTPINK, r=0.06)
        for sy in (-1, 1):
            tassel(bm, (sx * 0.22, sy * 0.1, 0.075), (sx, sy * 0.6, -0.3), HOTPINK)
    daisy(bm, (0, -0.08, 0.13), 0.05, petal=HOTPINK, centre=YELLOW, n=5, h=0.008, face=(-40, 0, 0))


def nightstand(bm):
    legs4(bm, 0.16, 0.14, 0.06, taper=False, r=0.025)
    rbox(bm, (0, 0, 0.26), (0.42, 0.38, 0.4), WOOD, r=0.02)
    rbox(bm, (0, 0, 0.475), (0.45, 0.41, 0.03), WOOD_D, r=0.01)
    drawers(bm, 0.42, 0.38, 0.06, 0.46, 2)
    andon(bm, (0.0, 0.02, 0.49), 0.15, 0.17, leg=0.03)
    ring(bm, (0, 0.02, 0.76), 0.05, 0.008, BLACK, rot=(90, 0, 0), segs=14, rsegs=5)


def tansu_chest(bm):
    rbox(bm, (0, 0, 0.03), (0.78, 0.46, 0.06), BARK, r=0.012)
    rbox(bm, (0, 0, 0.6), (0.76, 0.44, 1.1), BARK, r=0.02)
    rbox(bm, (0, 0, 1.165), (0.8, 0.48, 0.035), BLACK, r=0.01)
    fronts = [(-0.18, 1.0, 0.34, 0.22), (0.18, 1.0, 0.34, 0.22), (0, 0.76, 0.7, 0.2), (0, 0.53, 0.7, 0.2), (0, 0.3, 0.7, 0.2), (0, 0.11, 0.7, 0.13)]
    for x, z, w, h in fronts:
        rbox(bm, (x, -0.225, z), (w, 0.02, h), WOOD_D, r=0.008)
        for hx in ((x,) if w < 0.5 else (x - 0.17, x + 0.17)):
            rbox(bm, (hx, -0.238, z + 0.01), (0.08, 0.008, 0.05), BLACK, r=0.003)
            ring(bm, (hx, -0.246, z - 0.005), 0.03, 0.006, BLACK, rot=(90, 0, 0), segs=12, rsegs=5)
    for sx in (-1, 1):
        for z in (0.12, 1.1):
            rbox(bm, (sx * 0.355, -0.226, z), (0.06, 0.006, 0.1), BLACK, r=0.002)


def kimono_stand(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.48, 0, 0.78), (0.05, 0.05, 1.5), BLACK, r=0.012)
        rbox(bm, (sx * 0.48, 0, 0.03), (0.08, 0.42, 0.06), BLACK, r=0.015)
    capsule(bm, (-0.58, 0, 1.5), (0.58, 0, 1.5), 0.022, BLACK, segs=8)
    for sx in (-1, 1):
        capsule(bm, (sx * 0.58, 0, 1.5), (sx * 0.63, 0, 1.54), 0.022, BLACK, segs=8)
    capsule(bm, (-0.48, 0, 0.45), (0.48, 0, 0.45), 0.015, BLACK, segs=8)
    rbox(bm, (0, 0, 1.33), (0.92, 0.06, 0.28), SAKURA, r=0.02)
    rbox(bm, (0, 0, 0.9), (0.46, 0.07, 0.86), SAKURA, r=0.02)
    rbox(bm, (0, -0.005, 1.08), (0.48, 0.08, 0.11), HOTPINK, r=0.015)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.06, -0.038, 1.32), (0.03, 0.006, 0.28), WHITE, r=0.003, rot=(0, sx * 18, 0))
    for x, z, R in ((-0.14, 0.82, 0.07), (0.1, 0.62, 0.06), (0.12, 0.93, 0.05), (-0.35, 1.33, 0.06), (0.33, 1.3, 0.055), (-0.08, 0.55, 0.04)):
        daisy(bm, (x, -0.04, z), R, petal=WHITE, centre=HOTPINK, n=5, h=0.005, face=(90, 0, 0))


def clothing_basket(bm):
    lathe(bm, [(0, 0), (0.18, 0), (0.2, 0.03), (0.22, 0.22), (0, 0.22)], WICKER, segs=28, sx=1.4)
    for z in (0.07, 0.14):
        ring(bm, (0, 0, z), 0.207 + z * 0.07, 0.009, WICKER_D, segs=28, rsegs=6, sx=1.4)
    ring(bm, (0, 0, 0.225), 0.22, 0.022, WICKER_D, segs=28, rsegs=6, sx=1.4)
    ring(bm, (0, 0, 0.27), 0.24, 0.014, WICKER_D, rot=(90, 0, 0), segs=24, rsegs=6)
    for i, (s, h) in enumerate(((WHITE, 0.05), (PINK_L, 0.045), (SAGE, 0.04))):
        rbox(bm, (0.02 * (i % 2), 0, 0.2 + i * 0.045 + h / 2), (0.36 - i * 0.04, 0.26 - i * 0.02, h), s, r=0.018)


def shoji_lamp(bm):
    andon(bm, (0, 0, 0), 0.26, 0.72, leg=0.07)


def sakura_branch_vase(bm):
    top = jp_vase(bm, (0, 0, 0), BLACK, 0.85)
    sakura(bm, (0, 0, top), 0.55, 0.2, 3, seed=21, R=0.036)


def incense_burner(bm):
    for k in range(3):
        a = math.radians(90 + 120 * k)
        sphere(bm, (0.11 * math.cos(a), 0.11 * math.sin(a), 0.025), (0.025, 0.025, 0.03), GREEN_D, segs=(8, 5))
    lathe(bm, [(0, 0.03), (0.12, 0.03), (0.17, 0.1), (0.16, 0.17), (0.13, 0.19), (0, 0.19)], SAGE_D, segs=24)
    lathe(bm, [(0, 0.185), (0.13, 0.185), (0.11, 0.25), (0.04, 0.28), (0, 0.28)], SAGE_D, segs=24)
    sphere(bm, (0, 0, 0.29), (0.025, 0.025, 0.025), GOLD, segs=(8, 5))
    for k in range(6):
        a = 2 * math.pi * k / 6
        sphere(bm, (0.09 * math.cos(a), 0.09 * math.sin(a), 0.235), (0.012, 0.012, 0.012), BLACK, segs=(6, 4))
    ring(bm, (0, 0, 0.12), 0.168, 0.008, GOLD, segs=24, rsegs=5)
    pts = [Vector((0.01 * math.sin(k * 1.4) + 0.02 * math.sin(k * 0.7), 0, 0.31 + 0.05 * k)) for k in range(7)]
    for k in range(len(pts) - 1):
        capsule(bm, pts[k], pts[k + 1], 0.012 - k * 0.0012, WHITE, segs=6)


def floor_cushion(bm):
    zabuton(bm, HOTPINK, PINK_L, HOTPINK, w=0.62)


def makeup_box(bm):
    rbox(bm, (0, 0, 0.01), (0.38, 0.28, 0.02), WOOD_D, r=0.006)
    for sy in (-1, 1):
        rbox(bm, (0, sy * 0.125, 0.11), (0.38, 0.03, 0.2), WOOD, r=0.008)
        rbox(bm, (sy * 0.175, 0, 0.11), (0.03, 0.28, 0.2), WOOD, r=0.008)
    rbox(bm, (0, 0, 0.12), (0.34, 0.24, 0.02), WOOD_D, r=0.005)
    rbox(bm, (0, 0, 0.16), (0.012, 0.23, 0.06), WOOD, r=0.003)
    rbox(bm, (0.085, 0, 0.16), (0.16, 0.012, 0.06), WOOD, r=0.003)
    rbox(bm, (0, -0.142, 0.065), (0.2, 0.01, 0.08), WOOD_L, r=0.004)
    knob(bm, (0, -0.155, 0.065), 0.014, GOLD)
    sphere(bm, (-0.08, -0.05, 0.14), (0.04, 0.04, 0.025), PINK_L, segs=(10, 5))
    lathe(bm, [(0, 0.13), (0.02, 0.13), (0.02, 0.2), (0, 0.2)], JRED, (0.1, 0.06, 0), segs=10)
    b = bmesh.new()
    rbox(b, (0, 0.015, 0.14), (0.38, 0.03, 0.28), WOOD, r=0.008)
    rbox(b, (0, -0.002, 0.14), (0.3, 0.008, 0.2), GLASS, r=0.004)
    _merge(bm, b, (-12, 0, 0), (0, 0.14, 0.2))


def _sakura_painting(bm):
    pts = [Vector(p) for p in ((-0.12, -0.012, 0.3), (-0.05, -0.012, 0.45), (0.02, -0.012, 0.6), (0.06, -0.012, 0.82))]
    for k in range(3):
        capsule(bm, pts[k], pts[k + 1], 0.011 - k * 0.002, BARK, segs=6)
    capsule(bm, pts[1], (0.11, -0.012, 0.52), 0.006, BARK, segs=6)
    capsule(bm, pts[2], (-0.09, -0.012, 0.74), 0.006, BARK, segs=6)
    for x, z in ((-0.05, 0.47), (0.03, 0.6), (0.07, 0.8), (0.11, 0.53), (-0.09, 0.74), (0.0, 0.68), (0.08, 0.68), (-0.02, 0.54), (0.05, 0.42)):
        blossom(bm, (x, -0.018, z), 0.03, face=(90, 0, 0))


def wall_scroll(bm):
    scroll(bm, PINK_L, _sakura_painting)


# ---------- Kitchen ----------
def hearth_stove(bm):
    rbox(bm, (0, 0, 0.3), (0.72, 0.56, 0.6), STONE_L, r=0.05)
    rbox(bm, (0, -0.27, 0.15), (0.3, 0.04, 0.2), BLACK, r=0.01)
    cyl(bm, (0, -0.25, 0.25), 0.15, 0.04, BLACK, rot=(90, 0, 0), segs=20, bevel=0.1)
    for sx in (-1, 1):
        capsule(bm, (sx * 0.1, -0.33, 0.07), (-sx * 0.02, -0.2, 0.09), 0.025, WOOD_D, segs=8)
    for x, h in ((-0.05, 0.13), (0.04, 0.16), (0.0, 0.2)):
        lathe(bm, [(0, 0.07), (0.035, 0.09), (0.03, 0.07 + h * 0.6), (0, 0.07 + h)], FLAME, (x, -0.27, 0), segs=10)
    lathe(bm, [(0, 0.55), (0.12, 0.55), (0.2, 0.62), (0.21, 0.7), (0, 0.7)], BLACK, segs=24)
    ring(bm, (0, 0, 0.66), 0.22, 0.015, BLACK, segs=24, rsegs=6)
    cyl(bm, (0, 0, 0.69), 0.2, 0.03, WOOD, segs=24)
    rbox(bm, (0, 0, 0.73), (0.24, 0.045, 0.04), WOOD_D, r=0.012)


def rice_cooker_pot(bm):
    lathe(bm, [(0, 0), (0.13, 0), (0.2, 0.06), (0.21, 0.16), (0, 0.16)], BLACK, segs=24)
    ring(bm, (0, 0, 0.12), 0.215, 0.018, BLACK, segs=24, rsegs=6)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.23, 0, 0.13), (0.05, 0.07, 0.03), BLACK, r=0.01)
    cyl(bm, (0, 0, 0.155), 0.2, 0.03, WOOD, segs=24)
    rbox(bm, (0, 0, 0.2), (0.22, 0.05, 0.04), WOOD_D, r=0.012)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.08, 0, 0.19), (0.03, 0.05, 0.03), WOOD_D, r=0.008)


def steamer_basket(bm):
    for k in range(2):
        z = k * 0.1
        lathe(bm, [(0, z), (0.18, z), (0.18, z + 0.095), (0, z + 0.095)], WICKER, segs=28)
        for dz in (0.012, 0.083):
            ring(bm, (0, 0, z + dz), 0.183, 0.011, WOOD_D, segs=28, rsegs=6)
    lathe(bm, [(0, 0.195), (0.19, 0.195), (0.19, 0.235), (0, 0.235)], WOOD_D, segs=28)
    lathe(bm, [(0, 0.23), (0.17, 0.23), (0.17, 0.245), (0, 0.245)], WICKER, segs=28)
    for k in range(7):
        t = -0.135 + k * 0.045
        L = 2 * math.sqrt(max(0.17 ** 2 - t ** 2, 0.0)) - 0.02
        rbox(bm, (t, 0, 0.248), (0.016, L, 0.008), WICKER_D, r=0.003)
        rbox(bm, (0, t, 0.25), (L, 0.016, 0.008), WICKER_D, r=0.003)


def jp_cutting_board(bm):
    rbox(bm, (0, 0, 0.025), (0.5, 0.32, 0.05), WOOD_L, r=0.012)
    rbox(bm, (0.08, 0.02, 0.055), (0.24, 0.05, 0.008), GREY, r=0.003, rot=(0, 0, -20))
    rbox(bm, (0.25, -0.04, 0.062), (0.12, 0.028, 0.024), WOOD_D, r=0.008, rot=(0, 0, -20))
    b = bmesh.new()
    lathe(b, [(0, 0), (0.025, 0.01), (0.02, 0.12), (0, 0.17)], ORANGE, segs=12)
    _merge(bm, b, (0, 90, 15), (-0.2, -0.04, 0.075))
    for k in range(3):
        leaf(bm, (-0.21, -0.04, 0.075), (-1, 0.3 * (k - 1), 0.3), 0.07, 0.025, LEAF, roll=60 * k, thick=0.006)
    for k in range(3):
        cyl(bm, (0.0 + k * 0.035, -0.09, 0.05), 0.022, 0.012, ORANGE, segs=12)
    for p in ((-0.12, 0.08, 0.08), (-0.07, 0.1, 0.075), (-0.1, 0.12, 0.09)):
        sphere(bm, p, (0.035, 0.035, 0.03), LEAF, segs=(10, 6))
    capsule(bm, (-0.09, 0.09, 0.05), (-0.09, 0.1, 0.07), 0.012, LEAF_L, segs=6)


def jp_dish_rack(bm):
    rbox(bm, (0, 0, 0.02), (0.5, 0.26, 0.04), WOOD, r=0.01)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.24, 0, 0.14), (0.03, 0.26, 0.24), WOOD, r=0.008)
    for sy in (-1, 1):
        capsule(bm, (-0.24, sy * 0.1, 0.24), (0.24, sy * 0.1, 0.24), 0.01, WOOD_D, segs=6)
    for k in range(7):
        x = -0.18 + k * 0.06
        for sy in (-1, 1):
            capsule(bm, (x, sy * 0.07, 0.04), (x, sy * 0.07, 0.15), 0.007, WOOD_D, segs=6)
    for k in range(5):
        x = -0.15 + k * 0.06 + 0.03
        cyl(bm, (x - 0.006, 0, 0.17), 0.13, 0.012, WHITE if k % 2 else CREAM, rot=(0, 90, 0), segs=24, bevel=0.5)
    lathe(bm, [(0, 0.04), (0.04, 0.04), (0.08, 0.1), (0, 0.1)], NAVY, (0.33, 0.02, 0), segs=16)


def hanging_utensils(bm):
    rbox(bm, (0, 0.03, 0.62), (0.7, 0.04, 0.06), WOOD_D, r=0.012)
    xs = (-0.22, -0.07, 0.08, 0.23)
    for x in xs:
        ring(bm, (x, 0.0, 0.575), 0.018, 0.004, BLACK, rot=(0, 90, 0), segs=10, rsegs=4)
        capsule(bm, (x, 0.0, 0.56), (x, 0.0, 0.32), 0.011, WOOD, segs=8)
    sphere(bm, (xs[0], -0.01, 0.27), (0.055, 0.04, 0.05), WOOD_L, segs=(12, 6))
    rbox(bm, (xs[1], 0, 0.24), (0.07, 0.014, 0.16), WOOD_L, r=0.02)
    sphere(bm, (xs[2], -0.005, 0.28), (0.035, 0.015, 0.05), WOOD_L, segs=(10, 6))
    for k in range(4):
        ring(bm, (xs[3], 0, 0.22), 0.06, 0.003, GREY, rot=(90, 0, 45 * k), segs=16, rsegs=4, sx=0.55)


def spice_shelf(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.2, 0, 0.18), (0.03, 0.16, 0.36), WOOD, r=0.008)
    for z in (0.015, 0.18, 0.345):
        rbox(bm, (0, 0, z), (0.43, 0.16, 0.025), WOOD_D, r=0.006)
    rbox(bm, (0, 0.07, 0.25), (0.38, 0.015, 0.16), WOOD, r=0.004)
    cols = (ORANGE, LEAF, JRED, YELLOW, GREEN_D, TERRA)
    for i in range(6):
        x = -0.12 + (i % 3) * 0.12
        z = 0.028 if i < 3 else 0.193
        lathe(bm, [(0, z), (0.038, z), (0.042, z + 0.08), (0.03, z + 0.095), (0, z + 0.095)], cols[i], (x, -0.01, 0), segs=14)
        rbox(bm, (x, -0.05, z + 0.045), (0.045, 0.012, 0.035), CREAM, r=0.004)
        cyl(bm, (x, -0.01, z + 0.09), 0.03, 0.03, WOOD_D, segs=12)


def pickle_jar(bm):
    lathe(bm, [(0, 0), (0.1, 0), (0.15, 0.08), (0.16, 0.15), (0.12, 0.24), (0.08, 0.27), (0, 0.27)], WHITE, segs=24)
    cyl(bm, (0, 0, 0.255), 0.09, 0.04, NAVY, segs=20)
    sphere(bm, (0, 0, 0.305), (0.025, 0.025, 0.02), NAVY, segs=(8, 5))
    ring(bm, (0, 0, 0.02), 0.105, 0.008, NAVY, segs=24, rsegs=5)
    ring(bm, (0, 0, 0.215), 0.137, 0.008, NAVY, segs=24, rsegs=5)
    for k in range(4):
        a = math.radians(-90 + 90 * k)
        daisy(bm, (0.163 * math.cos(a), 0.163 * math.sin(a), 0.13), 0.05, petal=NAVY, centre=WHITE, n=5, h=0.005, face=(90, 0, math.degrees(a) + 90))


def bamboo_basket(bm):
    lathe(bm, [(0, 0), (0.2, 0), (0.24, 0.04), (0.27, 0.16), (0, 0.16)], WICKER, segs=28)
    for z in (0.06, 0.11):
        ring(bm, (0, 0, z), 0.25 + z * 0.15, 0.008, WICKER_D, segs=28, rsegs=5)
    ring(bm, (0, 0, 0.165), 0.27, 0.02, WICKER_D, segs=28, rsegs=6)
    b = bmesh.new()
    lathe(b, [(0, 0), (0.035, 0.02), (0.03, 0.2), (0, 0.25)], ORANGE, segs=12)
    _merge(bm, b, (0, 70, 20), (-0.14, -0.05, 0.17))
    b = bmesh.new()
    lathe(b, [(0, 0), (0.045, 0.03), (0.045, 0.28), (0, 0.33)], WHITE, segs=14)
    _merge(bm, b, (20, -55, 0), (0.12, 0.0, 0.15))
    for k in range(4):
        leaf(bm, (0.08, -0.0, 0.25), (-0.4 + k * 0.25, -0.2 + k * 0.1, 1), 0.2, 0.07, LEAF if k % 2 else LEAF_L, roll=40 * k, thick=0.01)
    sphere(bm, (-0.02, 0.1, 0.2), (0.12, 0.11, 0.09), LEAF_L)
    sphere(bm, (0.02, -0.14, 0.18), (0.05, 0.05, 0.045), JRED, segs=(12, 6))
    for k in range(3):
        leaf(bm, (-0.15, 0.04, 0.2), (-0.6 + k * 0.4, 0.3, 1), 0.16, 0.05, LEAF, roll=30 * k, thick=0.008)


def noren_curtain(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.52, 0, 0.9), (0.06, 0.06, 1.8), WOOD_D, r=0.015)
        rbox(bm, (sx * 0.52, 0, 0.03), (0.1, 0.32, 0.06), WOOD_D, r=0.015)
    rbox(bm, (0, 0, 1.79), (1.2, 0.08, 0.08), WOOD, r=0.02)
    capsule(bm, (-0.5, -0.005, 1.7), (0.5, -0.005, 1.7), 0.014, WOOD_D, segs=8)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.24, -0.005, 1.22), (0.46, 0.02, 0.92), NAVY, r=0.008)
        rbox(bm, (sx * 0.24, -0.005, 1.67), (0.46, 0.035, 0.06), NAVY, r=0.012)
    daisy(bm, (-0.24, -0.017, 1.22), 0.15, petal=WHITE, centre=NAVY, n=5, h=0.006, face=(90, 0, 0))
    for x, z, R in ((0.33, 1.35, 0.06), (0.17, 1.05, 0.05), (0.32, 0.88, 0.04)):
        daisy(bm, (x, -0.017, z), R, petal=WHITE, centre=NAVY, n=5, h=0.005, face=(90, 0, 0))


def sake_set(bm):
    cyl(bm, (0, 0, 0), 0.2, 0.025, WOOD_D, segs=28)
    ring(bm, (0, 0, 0.027), 0.195, 0.01, WOOD_D, segs=28, rsegs=5)
    lathe(bm, [(0, 0.025), (0.06, 0.025), (0.085, 0.09), (0.07, 0.15), (0.025, 0.2), (0.022, 0.24), (0.032, 0.255), (0, 0.255)], BARK, (-0.07, 0.03, 0))
    daisy(bm, (-0.07, -0.056, 0.1), 0.035, petal=CREAM, centre=YELLOW, n=5, h=0.004, face=(90, 0, 0))
    for x, y in ((0.07, -0.06), (0.11, 0.06)):
        lathe(bm, [(0, 0.025), (0.025, 0.025), (0.035, 0.07), (0.032, 0.075), (0, 0.075)], MATCHA, (x, y, 0), segs=14)


def wooden_refrigerator(bm):
    legs4(bm, 0.27, 0.24, 0.06, taper=False, r=0.03)
    rbox(bm, (0, 0, 0.82), (0.66, 0.6, 1.52), WOOD, r=0.025)
    rbox(bm, (0, 0, 1.6), (0.7, 0.64, 0.05), WOOD_D, r=0.012)
    rbox(bm, (0, -0.3, 1.08), (0.58, 0.02, 0.88), WOOD_L, r=0.01)
    for k in range(7):
        rbox(bm, (-0.21 + k * 0.07, -0.312, 1.08), (0.022, 0.008, 0.8), WOOD, r=0.003)
    rbox(bm, (0, -0.3, 0.38), (0.58, 0.02, 0.46), WOOD_L, r=0.01)
    for k in range(4):
        rbox(bm, (0, -0.312, 0.22 + k * 0.1), (0.52, 0.008, 0.022), WOOD, r=0.003)
    rbox(bm, (0.24, -0.325, 1.0), (0.025, 0.015, 0.2), BLACK, r=0.006)
    rbox(bm, (0, -0.325, 0.56), (0.16, 0.015, 0.025), BLACK, r=0.006)


AREAS_JP = {
    "Bathroom": [("WoodenOfuro", wooden_ofuro), ("StoneBathStool", stone_bath_stool), ("WoodenBucket", wooden_bucket), ("BambooShower", bamboo_shower),
                 ("RockOnsenDivider", rock_onsen_divider), ("TowelRack", jp_towel_rack), ("WashBasin", wash_basin), ("AromaLantern", aroma_lantern),
                 ("BathMat", jp_bath_mat), ("BathSet", bath_set), ("PottedBamboo", potted_bamboo), ("SlidingScreen", sliding_screen)],
    "LivingRoom": [("LowTeaTable", low_tea_table), ("ZabutonCushion", zabuton_cushion), ("FloorChair", floor_chair), ("PaperLantern", paper_lantern),
                   ("IndoorBonsai", indoor_bonsai), ("HangingScroll", hanging_scroll), ("RoomDivider", room_divider), ("IroriHearth", irori_hearth),
                   ("WoodenCabinet", wooden_cabinet), ("DecorativeFan", decorative_fan), ("IkebanaVase", ikebana_vase), ("TatamiRug", tatami_rug)],
    "Bedroom": [("FutonBed", futon_bed), ("Pillow", jp_pillow), ("Nightstand", nightstand), ("TansuChest", tansu_chest),
                ("KimonoStand", kimono_stand), ("ClothingBasket", clothing_basket), ("ShojiLamp", shoji_lamp), ("SakuraBranchVase", sakura_branch_vase),
                ("IncenseBurner", incense_burner), ("FloorCushion", floor_cushion), ("MakeupBox", makeup_box), ("WallScroll", wall_scroll)],
    "Kitchen": [("HearthStove", hearth_stove), ("RiceCookerPot", rice_cooker_pot), ("SteamerBasket", steamer_basket), ("CuttingBoard", jp_cutting_board),
                ("DishRack", jp_dish_rack), ("HangingUtensils", hanging_utensils), ("SpiceShelf", spice_shelf), ("PickleJar", pickle_jar),
                ("BambooBasket", bamboo_basket), ("NorenCurtain", noren_curtain), ("SakeSet", sake_set), ("Refrigerator", wooden_refrigerator)],
}


def build_japanese(only=None):
    return build_decor(only, AREAS_JP, "SM_DecorJP_", "DecorJapanese", "DecorJP_", -280.0)


def render_japanese_previews(out_dir, only=None, size=360):
    render_decor_previews(out_dir, only, size, AREAS_JP, "SM_DecorJP_")
