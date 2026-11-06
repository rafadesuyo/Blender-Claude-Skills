# gab house decorations, Brazilian set (Dante's 4 "Brazilian Style" sheets, 2026-10-29): Banheiro /
# Sala de Estar / Quarto / Cozinha, 12 items each. Same rules and helpers as decor.py +
# decor_japanese.py (one atlas material, rounded boxes, lathed round parts, every item closed, pivot at
# the bottom centre, front -Y). Collections: DecorBrazil > DecorBR_Bathroom / DecorBR_LivingRoom /
# DecorBR_Bedroom / DecorBR_Kitchen, objects SM_DecorBR_<Name> (rows at y -300 ...).
#   exec(open(r"<skills>/blender-game-props/decor_brazil.py").read())
#   build_brazil()                 # every item; build_brazil(["Kitchen"]) for one area
#   render_brazil_previews(dir)    # one framed PNG per item (dir/<area>/<name>.png)
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

exec(open(_skill("blender-game-props/decor_japanese.py")).read())

BR_GREEN = S("r1", 13, 0.0, 0.4)
BR_BLUE = S("r4", 10, 0.0, 0.45)
BR_BLUE_D = S("r4", 10, 0.6, 0.95)
CORAL = S("r4", 3, 0.0, 0.35)
RED_D = S("r4", 14, 0.4, 0.7)
LIGHTGREY = S("r3", 24, 0.0, 0.2)
AMBER = S("r4", 16, 0.3, 0.7)


# ---------- Brazilian helpers ----------
def plastic_chair(bm, at=(0, 0, 0), yaw=0.0, s=WHITE):
    """A white monobloc chair, front -Y."""
    b = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            capsule(b, (sx * 0.21, sy * 0.21, 0.02), (sx * 0.19, sy * 0.19, 0.43), 0.024, s, segs=8)
    rbox(b, (0, 0, 0.45), (0.46, 0.46, 0.05), s, r=0.02)
    for sx in (-1, 1):
        capsule(b, (sx * 0.2, 0.2, 0.45), (sx * 0.21, 0.27, 0.86), 0.022, s, segs=8)
        capsule(b, (sx * 0.21, 0.24, 0.63), (sx * 0.22, -0.18, 0.62), 0.02, s, segs=8)
        capsule(b, (sx * 0.2, -0.19, 0.45), (sx * 0.22, -0.18, 0.62), 0.018, s, segs=8)
    rbox(b, (0, 0.27, 0.84), (0.48, 0.05, 0.1), s, r=0.02, rot=(-8, 0, 0))
    for k in range(4):
        rbox(b, (-0.12 + k * 0.08, 0.245, 0.64), (0.035, 0.03, 0.32), s, r=0.008, rot=(-8, 0, 0))
    _merge(bm, b, (0, 0, yaw), at)


def jar(bm, c, s, h=0.095, r=0.04, lid=WOOD_D):
    x, y, z = c
    lathe(bm, [(0, z), (r, z), (r * 1.05, z + h * 0.85), (r * 0.75, z + h), (0, z + h)], s, (x, y, 0), segs=14)
    rbox(bm, (x, y - r * 1.02, z + h * 0.45), (r * 1.1, 0.01, h * 0.35), CREAM, r=0.003)
    cyl(bm, (x, y, z + h * 0.95), r * 0.78, 0.028, lid, segs=12)


def bottle(bm, c, s, h=0.2, r=0.045, cap=BLACK, pump=True):
    x, y, z = c
    lathe(bm, [(0, z), (r, z), (r * 1.05, z + h * 0.15), (r * 1.05, z + h * 0.8), (r * 0.6, z + h), (0, z + h)], s, (x, y, 0), segs=14)
    cyl(bm, (x, y, z + h - 0.005), r * 0.35, 0.04, cap, segs=8)
    if pump:
        rbox(bm, (x - 0.015, y, z + h + 0.045), (0.045, 0.016, 0.014), cap, r=0.004)


def potted(bm, c, r=0.07, h=0.1, s=TERRA, size=0.32, seed=3, vines=0):
    lathe(bm, [(0, 0), (r * 0.8, 0), (r, h * 0.9), (r * 1.05, h), (0, h)], s, c)
    cyl(bm, (c[0], c[1], c[2] + h * 0.88), r * 0.88, h * 0.1, SOIL, segs=16)
    monstera(bm, (c[0], c[1], c[2] + h * 0.95), size, 5, seed=seed)
    for k in range(vines):
        a = math.radians(-60 - 60 * k)
        vine(bm, (c[0] + r * math.cos(a), c[1] + r * math.sin(a), c[2] + h), (0.003, -0.002, -0.08), 6, size=0.06, seed=seed + k)


def frame_art(bm, w, h, paint):
    """Wall picture: wooden frame + cream canvas (front at y -0.022, centre z h/2 + 0.05)."""
    rbox(bm, (0, 0, h / 2 + 0.05), (w, 0.04, h), WOOD, r=0.012)
    rbox(bm, (0, -0.012, h / 2 + 0.05), (w - 0.08, 0.02, h - 0.08), CREAM, r=0.003)
    paint(bm)


# ---------- Banheiro (bathroom) ----------
def shower_stall(bm):
    rbox(bm, (0, 0, 0.04), (0.92, 0.92, 0.08), WHITE, r=0.02)
    rbox(bm, (0, 0.44, 1.05), (0.92, 0.04, 1.95), LIGHTGREY, r=0.01)
    rbox(bm, (-0.44, 0, 1.05), (0.04, 0.92, 1.95), LIGHTGREY, r=0.01)
    for k in range(1, 9):
        z = 0.08 + k * 0.215
        rbox(bm, (0, 0.418, z), (0.88, 0.006, 0.012), WHITE, r=0.002)
        rbox(bm, (-0.418, 0, z), (0.006, 0.88, 0.012), WHITE, r=0.002)
    rbox(bm, (0.0, -0.445, 1.04), (0.88, 0.012, 1.9), GLASS, r=0.004)
    rbox(bm, (0.445, 0.0, 1.04), (0.012, 0.88, 1.9), GLASS, r=0.004)
    rbox(bm, (0.445, -0.445, 1.04), (0.035, 0.035, 1.95), BLACK, r=0.008)
    rbox(bm, (0.0, -0.445, 2.0), (0.92, 0.03, 0.03), BLACK, r=0.008)
    rbox(bm, (0.445, 0.0, 2.0), (0.03, 0.92, 0.03), BLACK, r=0.008)
    rbox(bm, (0.0, -0.445, 0.1), (0.92, 0.03, 0.03), BLACK, r=0.008)
    rbox(bm, (0.445, 0.0, 0.1), (0.03, 0.92, 0.03), BLACK, r=0.008)
    rbox(bm, (0.02, -0.445, 1.04), (0.025, 0.03, 1.9), BLACK, r=0.006)
    capsule(bm, (0.1, -0.47, 0.9), (0.1, -0.47, 1.3), 0.012, BLACK, segs=8)
    capsule(bm, (0.0, 0.41, 1.1), (0.0, 0.41, 1.9), 0.015, BLACK, segs=8)
    capsule(bm, (0.0, 0.41, 1.9), (0.0, 0.26, 1.93), 0.015, BLACK, segs=8)
    cyl(bm, (0.0, 0.22, 1.88), 0.1, 0.03, BLACK, segs=20)
    cyl(bm, (0.0, 0.42, 1.08), 0.05, 0.03, BLACK, rot=(90, 0, 0), segs=14)


def toilet(bm):
    lathe(bm, [(0, 0), (0.12, 0), (0.11, 0.2), (0.17, 0.32), (0.19, 0.39), (0, 0.39)], WHITE, (0, -0.05, 0), segs=24, sy=1.3)
    ring(bm, (0, -0.05, 0.4), 0.165, 0.025, WHITE, segs=24, rsegs=6, sy=1.3)
    rbox(bm, (0, 0.27, 0.6), (0.42, 0.18, 0.42), WHITE, r=0.04)
    rbox(bm, (0, 0.15, 0.6), (0.36, 0.03, 0.38), WHITE, r=0.03, rot=(-6, 0, 0))
    cyl(bm, (0, 0.27, 0.81), 0.03, 0.015, LIGHTGREY, segs=12)
    lathe(bm, [(0, 0), (0.07, 0), (0.08, 0.2), (0, 0.2)], GREY, (0.38, 0.12, 0), segs=16)
    cyl(bm, (0.38, 0.12, 0.2), 0.082, 0.025, BLACK, segs=16)


def bath_granite_sink(bm):
    rbox(bm, (0, 0, 0.04), (0.76, 0.42, 0.08), WOOD_D, r=0.01)
    rbox(bm, (0, 0, 0.4), (0.8, 0.45, 0.64), WOOD, r=0.02)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.19, -0.225, 0.39), (0.36, 0.02, 0.54), WOOD_L, r=0.01)
        knob(bm, (sx * 0.05, -0.245, 0.5))
    rbox(bm, (0, 0, 0.745), (0.86, 0.5, 0.05), BLACK, r=0.012)
    rnd = random.Random(5)
    for k in range(18):
        sphere(bm, (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.22, 0.22), 0.771), (0.01, 0.01, 0.003), GREY, segs=(6, 3))
    cyl(bm, (0, -0.03, 0.768), 0.16, 0.012, WHITE, segs=24, sx=1.4)
    cyl(bm, (0, -0.03, 0.775), 0.13, 0.008, LIGHTGREY, segs=24, sx=1.4)
    capsule(bm, (0, 0.17, 0.77), (0, 0.17, 0.88), 0.014, BLACK, segs=8)
    capsule(bm, (0, 0.17, 0.88), (0, 0.06, 0.88), 0.012, BLACK, segs=8)
    rbox(bm, (0, 0.24, 1.2), (0.62, 0.04, 0.55), WOOD, r=0.015)
    rbox(bm, (0, 0.22, 1.2), (0.54, 0.02, 0.47), GLASS, r=0.004)
    potted(bm, (-0.32, 0.1, 0.77), 0.06, 0.08, CREAM, 0.28, seed=101)
    bottle(bm, (0.32, 0.1, 0.77), CREAM, 0.13, 0.03, WOOD_D)


def bath_shelf(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            capsule(bm, (sx * 0.26, sy * 0.15, 0.0), (sx * 0.26, sy * 0.15, 1.02), 0.014, WHITE, segs=8)
    for z in (0.06, 0.38, 0.7, 1.0):
        rbox(bm, (0, 0, z), (0.56, 0.34, 0.025), WHITE, r=0.008)
    for i, s in enumerate((BR_BLUE, WHITE, BR_BLUE)):
        rbox(bm, (-0.12, 0, 0.1 + i * 0.05), (0.22, 0.24, 0.045), s, r=0.02)
    rbox(bm, (0.13, 0, 0.14), (0.2, 0.24, 0.13), BR_GREEN, r=0.02)
    for i, s in enumerate((WHITE, BR_BLUE)):
        rbox(bm, (0.1, 0, 0.42 + i * 0.05), (0.24, 0.24, 0.045), s, r=0.02)
    bottle(bm, (-0.15, 0, 0.39), CREAM, 0.14, 0.035, WOOD_D)
    bottle(bm, (-0.15, 0.05, 0.71), YELLOW, 0.12, 0.03, WOOD_D, pump=False)
    jar(bm, (0.12, 0, 0.71), GLASS_G, 0.1, 0.045)
    potted(bm, (0.08, 0.02, 1.01), 0.08, 0.11, TERRA, 0.36, seed=103, vines=2)


def laundry_basket_white(bm):
    rbox(bm, (0, 0, 0.22), (0.5, 0.36, 0.44), WHITE, r=0.035)
    rbox(bm, (0, 0, 0.43), (0.52, 0.38, 0.04), WHITE, r=0.015)
    for r_ in range(4):
        z = 0.08 + r_ * 0.08
        for c_ in range(5):
            rbox(bm, (-0.16 + c_ * 0.08, -0.181, z), (0.035, 0.006, 0.045), LIGHTGREY, r=0.008)
        for c_ in range(3):
            rbox(bm, (0.251, -0.1 + c_ * 0.1, z), (0.006, 0.035, 0.045), LIGHTGREY, r=0.008)
    for i in range(2):
        rbox(bm, (0.02 * i, 0, 0.47 + i * 0.045), (0.34 - i * 0.04, 0.24, 0.045), WOOD if i else WOOD_D, r=0.018)


def br_towel_rack(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.28, 0.05, 0.75), (0.05, 0.06, 0.08), WOOD_D, r=0.012)
    capsule(bm, (-0.3, 0.02, 0.75), (0.3, 0.02, 0.75), 0.02, WOOD, segs=10)
    rbox(bm, (0, -0.01, 0.43), (0.42, 0.025, 0.62), BR_GREEN, r=0.01)
    rbox(bm, (0, 0.045, 0.6), (0.42, 0.025, 0.28), BR_GREEN, r=0.01)
    for z in (0.2, 0.26):
        rbox(bm, (0, -0.024, z), (0.422, 0.006, 0.025), YELLOW, r=0.003)


def flag_bath_mat(bm):
    rbox(bm, (0, 0, 0.015), (0.9, 0.6, 0.03), BR_GREEN, r=0.012)
    b = bmesh.new()
    rbox(b, (0, 0, 0), (0.3, 0.3, 0.012), YELLOW, r=0.004, rot=(0, 0, 45))
    for v in b.verts:
        v.co.x *= 1.75
        v.co.y *= 1.05
    _merge(bm, b, None, (0, 0, 0.034))
    cyl(bm, (0, 0, 0.035), 0.12, 0.012, BR_BLUE, segs=24)
    # the white band: a short arc across the blue circle
    for k in range(5):
        a = math.radians(70 + 10 * k)
        a2 = math.radians(80 + 10 * k)
        capsule(bm, (0.27 * math.cos(a), -0.24 + 0.27 * math.sin(a), 0.048), (0.27 * math.cos(a2), -0.24 + 0.27 * math.sin(a2), 0.048), 0.009, WHITE, segs=6)


def zz_plant(bm):
    lathe(bm, [(0, 0), (0.11, 0), (0.15, 0.22), (0.16, 0.24), (0, 0.24)], CREAM)
    cyl(bm, (0, 0, 0.21), 0.14, 0.022, SOIL, segs=20)
    rnd = random.Random(111)
    for k in range(7):
        a = 2 * math.pi * k / 7 + rnd.uniform(-0.2, 0.2)
        tip = Vector((0.18 * math.cos(a), 0.18 * math.sin(a), 0.55 + rnd.uniform(0, 0.2)))
        base = Vector((0.03 * math.cos(a), 0.03 * math.sin(a), 0.23))
        capsule(bm, base, tip, 0.01, LEAF_D, segs=6)
        for t in (0.3, 0.45, 0.6, 0.75, 0.9):
            p = base.lerp(tip, t)
            for side in (-1, 1):
                d = (math.cos(a + side * 1.2), math.sin(a + side * 1.2), 0.6)
                leaf(bm, tuple(p), d, 0.07, 0.035, LEAF_D if (k + side) % 2 else LEAF, roll=math.degrees(a), thick=0.008)
        leaf(bm, tuple(tip), (math.cos(a) * 0.3, math.sin(a) * 0.3, 1), 0.07, 0.035, LEAF, thick=0.008)


def toiletry_basket(bm):
    rbox(bm, (0, 0, 0.1), (0.4, 0.28, 0.2), WICKER, r=0.02)
    for z in (0.05, 0.1, 0.15):
        rbox(bm, (0, 0, z), (0.405, 0.285, 0.012), WICKER_D, r=0.004)
    rbox(bm, (0, 0, 0.205), (0.41, 0.29, 0.02), WICKER_D, r=0.008)
    bottle(bm, (-0.1, 0.03, 0.15), YELLOW, 0.2, 0.04)
    bottle(bm, (0.04, 0.05, 0.15), BR_BLUE, 0.22, 0.042, WHITE)
    bottle(bm, (0.13, -0.03, 0.15), WHITE, 0.15, 0.035, BR_BLUE, pump=False)
    cyl(bm, (-0.18, -0.06, 0.21), 0.045, 0.16, WHITE, rot=(0, 90, 0), segs=14)


def tp_holder(bm):
    rbox(bm, (0, 0.04, 0.42), (0.38, 0.17, 0.03), WOOD, r=0.008)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.175, 0.04, 0.33), (0.03, 0.17, 0.2), WOOD, r=0.008)
    rbox(bm, (0, 0.115, 0.33), (0.34, 0.02, 0.2), WOOD_D, r=0.005)
    capsule(bm, (-0.16, 0.0, 0.33), (0.16, 0.0, 0.33), 0.012, WOOD_D, segs=8)
    cyl(bm, (-0.12, 0.0, 0.33), 0.065, 0.24, WHITE, rot=(0, 90, 0), segs=20)
    rbox(bm, (0.0, -0.065, 0.2), (0.22, 0.008, 0.24), WHITE, r=0.003)
    potted(bm, (0.08, 0.04, 0.435), 0.06, 0.08, TERRA, 0.26, seed=113)


def br_mirror(bm):
    rbox(bm, (0, 0, 0.45), (0.55, 0.05, 0.82), WOOD, r=0.12)
    rbox(bm, (0, -0.012, 0.45), (0.45, 0.035, 0.72), GLASS, r=0.1)
    rbox(bm, (-0.1, -0.031, 0.58), (0.035, 0.004, 0.25), WHITE, r=0.002, rot=(0, -30, 0))


def blue_stool(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(bm, (sx * 0.15, sy * 0.15, 0.18), (0.06, 0.06, 0.38), BR_BLUE, r=0.015, rot=(sy * 5, -sx * 5, 0))
        rbox(bm, (sx * 0.155, 0, 0.12), (0.03, 0.3, 0.04), BR_BLUE, r=0.01)
        rbox(bm, (0, sx * 0.155, 0.12), (0.3, 0.03, 0.04), BR_BLUE, r=0.01)
    rbox(bm, (0, 0, 0.36), (0.36, 0.36, 0.07), BR_BLUE, r=0.025)
    rbox(bm, (0, 0, 0.41), (0.38, 0.38, 0.04), BR_BLUE, r=0.018)
    rbox(bm, (0, 0, 0.429), (0.12, 0.04, 0.006), BR_BLUE_D, r=0.002)


# ---------- Sala de Estar (living room) ----------
def br_sofa(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(bm, [(0, 0), (0.02, 0), (0.03, 0.1), (0, 0.1)], WOOD_D, (sx * 0.75, sy * 0.3, 0), segs=10)
    rbox(bm, (0, 0, 0.25), (1.7, 0.8, 0.3), CREAM, r=0.08)
    rbox(bm, (0, 0.32, 0.62), (1.62, 0.2, 0.5), CREAM, r=0.08)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.78, 0, 0.45), (0.18, 0.8, 0.34), CREAM, r=0.08)
        rbox(bm, (sx * 0.34, -0.05, 0.45), (0.66, 0.62, 0.12), CREAM_D, r=0.05)
    rbox(bm, (-0.45, 0.15, 0.66), (0.3, 0.12, 0.3), NAVY, r=0.06, rot=(-15, 0, 8))
    daisy(bm, (-0.45, 0.085, 0.66), 0.08, petal=YELLOW, centre=JRED, n=5, h=0.008, face=(75, 0, 8))
    rbox(bm, (0.0, 0.15, 0.67), (0.3, 0.12, 0.3), JRED, r=0.06, rot=(-15, 0, -4))
    daisy(bm, (0.0, 0.085, 0.67), 0.08, petal=YELLOW, centre=BR_GREEN, n=5, h=0.008, face=(75, 0, -4))
    rbox(bm, (0.45, 0.15, 0.66), (0.3, 0.12, 0.3), BR_GREEN, r=0.06, rot=(-15, 0, -8))
    b = bmesh.new()
    rbox(b, (0, 0, 0), (0.12, 0.12, 0.01), YELLOW, r=0.004, rot=(0, 0, 45))
    _merge(bm, b, (75, 0, -8), (0.45, 0.085, 0.66))


def br_coffee_table(bm):
    for a in range(4):
        ang = math.radians(45 + 90 * a)
        capsule(bm, (0.33 * math.cos(ang), 0.33 * math.sin(ang), 0.02), (0.28 * math.cos(ang), 0.28 * math.sin(ang), 0.4), 0.022, WOOD_D, segs=8)
    cyl(bm, (0, 0, 0.12), 0.32, 0.03, WOOD, segs=28)
    ring(bm, (0, 0, 0.405), 0.4, 0.018, WOOD_D, segs=32, rsegs=6)
    cyl(bm, (0, 0, 0.405), 0.41, 0.022, GLASS, segs=32)
    books(bm, (0.08, 0.02, 0.15), 2, 0.22, 0.16, 0.04, (BR_BLUE, YELLOW))
    potted(bm, (-0.12, 0.05, 0.427), 0.07, 0.09, TERRA, 0.3, seed=121)
    books(bm, (0.18, -0.05, 0.427), 2, 0.18, 0.13, 0.03, (BR_GREEN, CREAM))


def br_armchair(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(bm, [(0, 0), (0.02, 0), (0.03, 0.12), (0, 0.12)], WOOD_D, (sx * 0.32, sy * 0.28, 0), segs=10)
    rbox(bm, (0, 0, 0.27), (0.86, 0.78, 0.3), YELLOW, r=0.1)
    rbox(bm, (0, 0.3, 0.64), (0.82, 0.22, 0.6), YELLOW, r=0.1)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.38, -0.02, 0.48), (0.2, 0.74, 0.28), YELLOW, r=0.09)
    rbox(bm, (0, -0.05, 0.47), (0.56, 0.6, 0.12), YELLOW, r=0.05)
    rbox(bm, (0.0, 0.14, 0.68), (0.36, 0.12, 0.28), NAVY, r=0.06, rot=(-15, 0, 0))
    for k in range(3):
        b = bmesh.new()
        rbox(b, (0, 0, 0), (0.05, 0.05, 0.008), YELLOW, r=0.003, rot=(0, 0, 45))
        _merge(bm, b, (75, 0, 0), (-0.09 + k * 0.09, 0.077, 0.68))


def br_tv_stand(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            capsule(bm, (sx * 0.58, sy * 0.15, 0.0), (sx * 0.54, sy * 0.14, 0.14), 0.02, WOOD_D, segs=8)
    rbox(bm, (0, 0, 0.3), (1.25, 0.4, 0.34), WOOD, r=0.02)
    for k in range(3):
        x = -0.4 + k * 0.4
        rbox(bm, (x, -0.17, 0.3), (0.34, 0.08, 0.26), WOOD_D, r=0.008)
        rbox(bm, (x, -0.2, 0.26), (0.26, 0.04, 0.15), CREAM if k != 1 else WICKER, r=0.02)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.2, 0, 0.485), (0.06, 0.16, 0.03), BLACK, r=0.008)
    rbox(bm, (0, 0, 0.76), (0.82, 0.05, 0.5), BLACK, r=0.015)
    rbox(bm, (0, -0.027, 0.76), (0.76, 0.004, 0.44), GREY, r=0.002)
    potted(bm, (0.5, 0.0, 0.47), 0.06, 0.08, CREAM, 0.26, seed=123)


def costela_adao(bm):
    lathe(bm, [(0, 0), (0.15, 0), (0.2, 0.3), (0.22, 0.34), (0, 0.34)], TERRA)
    ring(bm, (0, 0, 0.32), 0.215, 0.02, TERRA, segs=24, rsegs=6)
    cyl(bm, (0, 0, 0.3), 0.19, 0.03, SOIL, segs=20)
    monstera(bm, (0, 0, 0.32), 1.5, 9, seed=125)


def _beach_painting(bm):
    rbox(bm, (0, -0.024, 0.62), (0.42, 0.004, 0.36), YELLOW, r=0.002)
    sphere(bm, (0.1, -0.028, 0.66), (0.06, 0.004, 0.06), JRED, segs=(16, 6))
    prism(bm, [(-0.21, 0.36), (0.08, 0.36), (-0.06, 0.6)], -0.03, 0.006, BR_GREEN)
    prism(bm, [(-0.02, 0.36), (0.21, 0.36), (0.21, 0.5), (0.12, 0.52)], -0.032, 0.006, LEAF_D)
    rbox(bm, (0, -0.034, 0.25), (0.42, 0.006, 0.22), BR_BLUE, r=0.002)
    rbox(bm, (0, -0.036, 0.17), (0.42, 0.006, 0.06), CREAM_D, r=0.002)


def wall_art_beach(bm):
    frame_art(bm, 0.5, 0.62, _beach_painting)


def zebra_rug(bm):
    rbox(bm, (0, 0, 0.01), (1.3, 0.9, 0.02), WHITE, r=0.009)
    for k in range(7):
        x0 = -0.54 + k * 0.18
        for sy in (-1, 1):
            rbox(bm, (x0, sy * 0.22, 0.021), (0.07, 0.48, 0.004), BLACK, r=0.0015, rot=(0, 0, sy * 16))


def tripod_lamp(bm):
    for a in range(3):
        ang = math.radians(90 + 120 * a)
        capsule(bm, (0.28 * math.cos(ang), 0.28 * math.sin(ang), 0.02), (0.02 * math.cos(ang), 0.02 * math.sin(ang), 1.15), 0.02, WOOD, segs=10)
    cyl(bm, (0, 0, 1.1), 0.035, 0.08, WOOD_D, segs=12)
    lathe(bm, [(0, 1.16), (0.23, 1.16), (0.23, 1.18), (0.2, 1.46), (0, 1.46)], CREAM, segs=28)


def record_player(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(bm, (sx * 0.2, sy * 0.15, 0.012), (0.02, 0.02, 0.014), BLACK, segs=(8, 5))
    rbox(bm, (0, 0, 0.09), (0.52, 0.42, 0.15), RED_D, r=0.02)
    rbox(bm, (0, 0, 0.167), (0.46, 0.36, 0.01), WOOD_L, r=0.004)
    cyl(bm, (-0.05, 0, 0.17), 0.15, 0.015, BLACK, segs=28)
    cyl(bm, (-0.05, 0, 0.183), 0.045, 0.004, JRED, segs=16)
    cyl(bm, (-0.05, 0, 0.183), 0.006, 0.02, GREY, segs=8)
    cyl(bm, (0.17, 0.12, 0.17), 0.025, 0.025, GREY, segs=10)
    capsule(bm, (0.17, 0.12, 0.2), (0.07, -0.08, 0.195), 0.006, GREY, segs=6)
    for x in (0.12, 0.17):
        cyl(bm, (x, -0.14, 0.17), 0.012, 0.012, GOLD, segs=8)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.14, -0.212, 0.13), (0.04, 0.008, 0.03), GOLD, r=0.003)
    b = bmesh.new()
    rbox(b, (0, 0.0, 0.2), (0.52, 0.06, 0.4), RED_D, r=0.02)
    rbox(b, (0, -0.031, 0.2), (0.46, 0.006, 0.34), CREAM_D, r=0.003)
    _merge(bm, b, (-12, 0, 0), (0, 0.2, 0.15))


def bar_cart(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            capsule(bm, (sx * 0.3, sy * 0.18, 0.08), (sx * 0.3, sy * 0.18, 0.8), 0.014, BLACK, segs=8)
            cyl(bm, (sx * 0.3 - 0.02, sy * 0.18, 0.05), 0.05, 0.04, BLACK, rot=(0, 90, 0), segs=14)
    for z in (0.2, 0.6):
        rbox(bm, (0, 0, z), (0.64, 0.4, 0.025), WOOD, r=0.008)
        for sy in (-1, 1):
            capsule(bm, (-0.3, sy * 0.18, z + 0.07), (0.3, sy * 0.18, z + 0.07), 0.008, BLACK, segs=6)
    capsule(bm, (0.3, -0.18, 0.8), (0.3, 0.18, 0.8), 0.014, BLACK, segs=8)
    bottle(bm, (-0.18, 0.04, 0.613), AMBER, 0.24, 0.05, BLACK, pump=False)
    bottle(bm, (-0.06, 0.08, 0.613), GREEN_D, 0.28, 0.045, GOLD, pump=False)
    bottle(bm, (0.06, 0.05, 0.613), AMBER, 0.2, 0.045, WOOD_D, pump=False)
    for x in (0.16, 0.24):
        lathe(bm, [(0, 0.613), (0.025, 0.613), (0.005, 0.63), (0.005, 0.68), (0.035, 0.7), (0.035, 0.75), (0, 0.75)], GLASS, (x, -0.06, 0), segs=12)
    bottle(bm, (-0.15, 0.0, 0.213), AMBER, 0.22, 0.05, GOLD, pump=False)
    bottle(bm, (0.0, 0.03, 0.213), GLASS_G, 0.2, 0.045, BLACK, pump=False)
    jar(bm, (0.17, 0.0, 0.213), CREAM, 0.12, 0.05)


def hanging_plant(bm):
    ring(bm, (0, 0, 1.25), 0.03, 0.008, WOOD_D, rot=(90, 0, 0), segs=10, rsegs=5)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        capsule(bm, (0, 0, 1.22), (0.13 * math.cos(a), 0.13 * math.sin(a), 0.62), 0.006, WICKER, segs=6)
    lathe(bm, [(0, 0.45), (0.1, 0.45), (0.13, 0.6), (0.135, 0.63), (0, 0.63)], WHITE)
    cyl(bm, (0, 0, 0.6), 0.12, 0.03, SOIL, segs=16)
    monstera(bm, (0, 0, 0.62), 0.45, 6, seed=131)
    for k in range(4):
        a = math.radians(-30 - 40 * k)
        vine(bm, (0.13 * math.cos(a), 0.13 * math.sin(a), 0.6), (0.005 * math.cos(a), -0.002, -0.085), 7, size=0.07, seed=132 + k)


def hammock(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 1.0, 0, 0.55), (0.07, 0.07, 1.1), WOOD, r=0.015)
        rbox(bm, (sx * 1.0, 0, 0.03), (0.12, 0.5, 0.06), WOOD_D, r=0.015)
        sphere(bm, (sx * 1.0, 0, 1.12), (0.05, 0.05, 0.04), WOOD_D, segs=(10, 5))
    rbox(bm, (0, 0, 0.04), (2.0, 0.08, 0.06), WOOD_D, r=0.015)
    cols = (JRED, ORANGE, YELLOW, BR_GREEN, BR_BLUE, PURPLE)
    n, X = 10, 0.72

    def z_at(x, y):
        return 0.42 + 0.32 * (x / X) ** 2 + 0.12 * (y / 0.33) ** 2 * (1 - (x / X) ** 2)

    for j in range(6):
        y = -0.275 + j * 0.11
        for i in range(n):
            x0, x1 = -X + 2 * X * i / n, -X + 2 * X * (i + 1) / n
            xm = (x0 + x1) / 2
            dz = z_at(x1, y) - z_at(x0, y)
            L = math.hypot(x1 - x0, dz) * 1.08
            slope = math.degrees(math.atan2(dz, x1 - x0))
            curl = math.degrees(math.atan2(z_at(xm, y + 0.05) - z_at(xm, y - 0.05), 0.1))
            rbox(bm, (xm, y, z_at(xm, y)), (L, 0.115, 0.014), cols[j], r=0.003, rot=(curl, -slope, 0))
    for sx in (-1, 1):
        for y in (-0.3, 0.0, 0.3):
            capsule(bm, (sx * X, y, z_at(X, y)), (sx * 0.98, 0, 1.0), 0.007, CREAM, segs=6)
    for k in range(9):
        x = -0.6 + k * 0.15
        for sy in (-1, 1):
            p = Vector((x, sy * 0.34, z_at(x, sy * 0.33)))
            capsule(bm, p, p + Vector((0, sy * 0.01, -0.09)), 0.01, cols[k % 6], segs=6)


# ---------- Quarto (bedroom) ----------
def br_bed(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(bm, (sx * 0.72, sy * 0.92, 0.08), (0.08, 0.08, 0.16), WOOD_D, r=0.015)
    rbox(bm, (0, 0, 0.22), (1.5, 1.9, 0.14), WOOD, r=0.03)
    rbox(bm, (0, 0.96, 0.55), (1.56, 0.1, 0.8), WOOD, r=0.04)
    rbox(bm, (0, 0, 0.36), (1.4, 1.82, 0.16), WHITE, r=0.06)
    rbox(bm, (0, -0.28, 0.43), (1.46, 1.26, 0.08), BR_GREEN, r=0.04)
    rbox(bm, (0, -0.72, 0.475), (1.47, 0.32, 0.03), CORAL, r=0.012)
    rbox(bm, (0, 0.38, 0.45), (1.42, 0.14, 0.07), WHITE, r=0.03)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.33, 0.72, 0.52), (0.56, 0.28, 0.14), CORAL, r=0.06, rot=(-12, 0, 0))
    rbox(bm, (0.1, 0.56, 0.56), (0.34, 0.12, 0.22), WHITE, r=0.05, rot=(-20, 0, 0))


def br_nightstand(bm):
    legs4(bm, 0.17, 0.14, 0.08)
    rbox(bm, (0, 0, 0.3), (0.44, 0.38, 0.44), WOOD, r=0.02)
    rbox(bm, (0, 0, 0.535), (0.47, 0.41, 0.03), WOOD_D, r=0.01)
    drawers(bm, 0.44, 0.38, 0.08, 0.52, 2)
    lathe(bm, [(0, 0.55), (0.05, 0.55), (0.08, 0.62), (0.05, 0.69), (0.015, 0.71), (0, 0.71)], WOOD_D, (-0.07, 0.02, 0))
    lathe(bm, [(0, 0.7), (0.13, 0.7), (0.12, 0.72), (0.08, 0.86), (0, 0.86)], PAPER_GLOW, (-0.07, 0.02, 0), segs=24)
    potted(bm, (0.13, -0.03, 0.55), 0.05, 0.07, TERRA, 0.22, seed=141)


def br_wardrobe(bm):
    legs4(bm, 0.43, 0.22, 0.08)
    rbox(bm, (0, 0, 1.0), (1.0, 0.55, 1.84), WOOD, r=0.03)
    rbox(bm, (0, 0, 1.94), (1.06, 0.6, 0.06), WOOD_D, r=0.02)
    rbox(bm, (-0.235, -0.283, 1.0), (0.44, 0.02, 1.7), LIGHTGREY, r=0.012)
    rbox(bm, (0.235, -0.283, 1.0), (0.44, 0.02, 1.7), CREAM, r=0.012)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.05, -0.3, 1.05), (0.02, 0.02, 0.22), WOOD_D, r=0.006)


def full_mirror(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.33, 0.05, 0.75), (0.05, 0.05, 1.5), WOOD, r=0.012, rot=(-6, 0, 0))
        rbox(bm, (sx * 0.33, 0.0, 0.025), (0.08, 0.45, 0.05), WOOD_D, r=0.012)
        sphere(bm, (sx * 0.3, -0.02, 0.95), (0.03, 0.03, 0.03), GOLD, segs=(8, 5))
        sphere(bm, (sx * 0.33, 0.12, 1.51), (0.035, 0.035, 0.03), WOOD_D, segs=(8, 5))
    capsule(bm, (-0.33, 0.1, 0.2), (0.33, 0.1, 0.2), 0.015, WOOD_D, segs=8)
    ring(bm, (0, -0.02, 0.95), 0.27, 0.035, WOOD, rot=(90, 0, 0), segs=32, rsegs=8, sy=2.0)
    cyl(bm, (0, -0.01, 0.95), 0.265, 0.02, GLASS, rot=(90, 0, 0), segs=32, sy=2.0)
    rbox(bm, (-0.08, -0.033, 1.08), (0.035, 0.004, 0.3), WHITE, r=0.002, rot=(0, -20, 0))


def br_dresser(bm):
    legs4(bm, 0.36, 0.17, 0.09)
    rbox(bm, (0, 0, 0.45), (0.86, 0.44, 0.72), WOOD, r=0.025)
    rbox(bm, (0, 0, 0.825), (0.9, 0.48, 0.035), WOOD_D, r=0.012)
    drawers(bm, 0.86, 0.44, 0.09, 0.81, 4, cols=2)
    potted(bm, (0.2, 0.04, 0.843), 0.08, 0.11, LIGHTGREY, 0.36, seed=151)
    jar(bm, (-0.2, 0.0, 0.843), YELLOW, 0.11, 0.05, WOOD_D)


def br_pouf(bm):
    lathe(bm, [(0, 0), (0.24, 0), (0.3, 0.07), (0.31, 0.2), (0.27, 0.3), (0.12, 0.33), (0, 0.33)], WICKER, segs=28)
    # chunky knitted braids running up the sides, a coil on top
    for k in range(20):
        a = 2 * math.pi * k / 20
        for z0, z1, r0, r1 in ((0.02, 0.12, 0.27, 0.315), (0.12, 0.22, 0.315, 0.31), (0.22, 0.31, 0.31, 0.25)):
            for side in (-1, 1):
                a0, a1 = a + side * 0.035, a - side * 0.035
                capsule(bm, (r0 * math.cos(a0), r0 * math.sin(a0), z0 + 0.01), (r1 * math.cos(a1), r1 * math.sin(a1), z1 - 0.01), 0.017, WICKER if side > 0 else WICKER_D, segs=6)
    for R in (0.08, 0.16):
        ring(bm, (0, 0, 0.325 - R * 0.12), R, 0.012, WICKER_D, segs=20, rsegs=5)


def wavy_rug(bm):
    cyl(bm, (0, 0, 0), 0.6, 0.02, CREAM, segs=36, sx=1.35, bevel=0.3)
    cols = (CORAL, ORANGE, HOTPINK)
    for k in range(9):
        y0 = -0.48 + k * 0.12
        half = 0.81 * math.sqrt(max(1 - (y0 / 0.58) ** 2, 0)) - 0.06
        if half < 0.12:
            continue
        n = 10
        for i in range(n):
            x0, x1 = -half + 2 * half * i / n, -half + 2 * half * (i + 1) / n
            ya, yb = y0 + 0.035 * math.sin(x0 * 7), y0 + 0.035 * math.sin(x1 * 7)
            L = math.hypot(x1 - x0, yb - ya) * 1.1
            rbox(bm, ((x0 + x1) / 2, (ya + yb) / 2, 0.021), (L, 0.07, 0.005), cols[k % 3], r=0.002, rot=(0, 0, math.degrees(math.atan2(yb - ya, x1 - x0))))


def snake_plant(bm):
    lathe(bm, [(0, 0), (0.1, 0), (0.13, 0.2), (0.14, 0.22), (0, 0.22)], WHITE)
    cyl(bm, (0, 0, 0.19), 0.125, 0.022, SOIL, segs=20)
    rnd = random.Random(161)
    for k in range(8):
        a = 2 * math.pi * k / 8 + rnd.uniform(-0.3, 0.3)
        r = rnd.uniform(0.02, 0.07)
        base = (r * math.cos(a), r * math.sin(a), 0.2)
        d = (math.cos(a) * 0.15, math.sin(a) * 0.15, 1)
        leaf(bm, base, d, rnd.uniform(0.45, 0.7), 0.09, LEAF_D if k % 2 else LEAF, roll=math.degrees(a) + 90, thick=0.018)


def wall_shelves(bm):
    for z in (0.25, 0.65):
        rbox(bm, (0, 0, z), (0.8, 0.2, 0.03), WOOD, r=0.008)
        for sx in (-1, 1):
            rbox(bm, (sx * 0.3, 0.08, z - 0.06), (0.025, 0.04, 0.1), BLACK, r=0.006)
    rnd = random.Random(171)
    x = -0.36
    cols = (CREAM, JRED, BR_BLUE, YELLOW, BR_GREEN, CORAL)
    while x < -0.05:
        w = rnd.uniform(0.035, 0.05)
        h = rnd.uniform(0.17, 0.22)
        rbox(bm, (x + w / 2, 0, 0.665 + h / 2), (w * 0.9, 0.15, h), cols[rnd.randrange(6)], r=0.005)
        x += w
    potted(bm, (0.2, 0.0, 0.665), 0.07, 0.1, CREAM, 0.32, seed=172, vines=2)
    rbox(bm, (-0.18, 0, 0.32), (0.22, 0.16, 0.11), WICKER, r=0.02)
    rbox(bm, (-0.18, 0, 0.38), (0.23, 0.165, 0.015), WICKER_D, r=0.005)
    books(bm, (0.15, 0, 0.265), 3, 0.22, 0.15, 0.035, (BR_GREEN, CREAM, CORAL))


def _palm_painting(bm):
    rbox(bm, (0, -0.024, 0.5), (0.36, 0.004, 0.5), CORAL, r=0.002)
    rbox(bm, (0, -0.026, 0.62), (0.36, 0.004, 0.26), HOTPINK, r=0.002)
    sphere(bm, (0.08, -0.03, 0.55), (0.07, 0.004, 0.07), ORANGE, segs=(16, 6))
    rbox(bm, (0, -0.03, 0.27), (0.36, 0.006, 0.08), PINK_L, r=0.002)
    pts = [Vector((-0.05, -0.034, 0.3)), Vector((-0.07, -0.034, 0.45)), Vector((-0.04, -0.034, 0.6))]
    for k in range(2):
        capsule(bm, pts[k], pts[k + 1], 0.012, BARK, segs=6)
    for k in range(6):
        a = math.radians(10 + 32 * k)
        leaf(bm, tuple(pts[2]), (math.cos(a), 0, math.sin(a) * 0.6 - 0.2), 0.13, 0.04, LEAF_D, roll=0, thick=0.005)


def wall_art_palm(bm):
    frame_art(bm, 0.44, 0.62, _palm_painting)


def fabric_laundry_basket(bm):
    lathe(bm, [(0, 0), (0.18, 0), (0.2, 0.03), (0.22, 0.42), (0, 0.42)], CREAM, segs=28)
    ring(bm, (0, 0, 0.42), 0.215, 0.025, CREAM_D, segs=28, rsegs=6)
    for sx in (-1, 1):
        ring(bm, (sx * 0.2, 0, 0.42), 0.06, 0.012, WOOD, rot=(90, 0, 90), segs=14, rsegs=5)
    for k in range(5):
        a = math.radians(-150 + 30 * k)
        b = bmesh.new()
        prism(b, [(-0.03, -0.025), (0.03, -0.025), (0.0, 0.03)], 0, 0.006, WOOD_L if k % 2 else BR_GREEN)
        _merge(bm, b, (0, 0, math.degrees(a) + 90), (0.215 * math.cos(a), 0.215 * math.sin(a), 0.2 + 0.05 * (k % 2)))
    sphere(bm, (0.05, 0.02, 0.43), (0.13, 0.11, 0.06), BR_BLUE)
    sphere(bm, (-0.07, -0.04, 0.44), (0.1, 0.09, 0.06), WHITE)


def coat_rack(bm):
    for a in range(3):
        ang = math.radians(90 + 120 * a)
        capsule(bm, (0.25 * math.cos(ang), 0.25 * math.sin(ang), 0.02), (0.03 * math.cos(ang), 0.03 * math.sin(ang), 0.2), 0.022, WOOD_D, segs=8)
    cyl(bm, (0, 0, 0.0), 0.03, 1.72, WOOD, segs=12)
    sphere(bm, (0, 0, 1.74), (0.045, 0.045, 0.04), WOOD_D, segs=(10, 5))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        capsule(bm, (0, 0, 1.58), (0.16 * math.cos(a), 0.16 * math.sin(a), 1.66), 0.014, WOOD_D, segs=6)
    b = bmesh.new()
    lathe(b, [(0, 0), (0.2, 0), (0.2, 0.012), (0.1, 0.02), (0.1, 0.1), (0.08, 0.12), (0, 0.12)], WICKER, segs=24)
    ring(b, (0, 0, 0.035), 0.1, 0.012, BLACK, segs=20, rsegs=5)
    _merge(bm, b, (70, 0, 45), (0.15, -0.15, 1.5))
    rbox(bm, (-0.14, -0.12, 1.12), (0.18, 0.06, 0.22), BLACK, r=0.03, rot=(0, 0, -45))
    capsule(bm, (-0.2, -0.06, 1.2), (-0.12, -0.12, 1.62), 0.008, BLACK, segs=6)
    capsule(bm, (-0.08, -0.18, 1.2), (-0.12, -0.12, 1.62), 0.008, BLACK, segs=6)
    rbox(bm, (0.12, 0.12, 1.3), (0.1, 0.04, 0.6), BR_GREEN, r=0.015, rot=(0, 0, 45))


# ---------- Cozinha (kitchen) ----------
def br_fridge(bm):
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(bm, (sx * 0.28, sy * 0.25, 0.02), (0.05, 0.05, 0.04), LIGHTGREY, r=0.01)
    rbox(bm, (0, 0, 0.92), (0.7, 0.65, 1.76), WHITE, r=0.06)
    rbox(bm, (0, -0.326, 1.25), (0.68, 0.012, 0.015), LIGHTGREY, r=0.003)
    for z0, z1 in ((1.3, 1.6), (0.5, 1.15)):
        rbox(bm, (-0.27, -0.345, (z0 + z1) / 2), (0.03, 0.035, z1 - z0), LIGHTGREY, r=0.01)
    rbox(bm, (0.1, -0.33, 0.95), (0.12, 0.006, 0.16), YELLOW, r=0.004, rot=(0, 6, 0))
    for p, s in (((0.1, -0.336, 1.03), JRED), ((0.2, -0.33, 1.45), BR_GREEN), ((-0.05, -0.33, 1.4), BR_BLUE), ((0.18, -0.33, 0.7), ORANGE)):
        cyl(bm, p, 0.025, 0.012, s, rot=(90, 0, 0), segs=12)
    daisy(bm, (0.02, -0.334, 0.8), 0.045, petal=YELLOW, centre=ORANGE, n=5, h=0.005, face=(90, 0, 0))
    potted(bm, (0.15, 0.05, 1.8), 0.07, 0.09, TERRA, 0.3, seed=181)


def br_stove(bm):
    rbox(bm, (0, 0, 0.43), (0.6, 0.6, 0.86), WHITE, r=0.03)
    rbox(bm, (0, 0, 0.875), (0.6, 0.6, 0.03), BLACK, r=0.01)
    rbox(bm, (0, 0.28, 0.96), (0.6, 0.04, 0.16), WHITE, r=0.015)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (sx * 0.14, -0.02 + sy * 0.14, 0.89)
            cyl(bm, c, 0.065, 0.015, GREY, segs=16)
            for a in (0, 90):
                rbox(bm, (c[0], c[1], 0.91), (0.17, 0.014, 0.014), BLACK, r=0.004, rot=(0, 0, a))
    rbox(bm, (0, -0.305, 0.4), (0.52, 0.02, 0.48), BLACK, r=0.015)
    rbox(bm, (0, -0.317, 0.38), (0.38, 0.006, 0.26), GREY, r=0.004)
    capsule(bm, (-0.22, -0.34, 0.68), (0.22, -0.34, 0.68), 0.013, GREY, segs=8)
    for k in range(4):
        cyl(bm, (-0.21 + k * 0.14, -0.3, 0.78), 0.025, 0.03, BLACK, rot=(90, 0, 0), segs=12)
    rbox(bm, (0.08, -0.35, 0.56), (0.18, 0.015, 0.24), YELLOW, r=0.006)
    rbox(bm, (0.08, -0.33, 0.67), (0.18, 0.04, 0.03), YELLOW, r=0.01)


def kitchen_granite_sink(bm):
    rbox(bm, (0, 0, 0.04), (1.16, 0.5, 0.08), CREAM_D, r=0.01)
    rbox(bm, (0, 0, 0.45), (1.2, 0.55, 0.74), CREAM, r=0.02)
    for k in range(3):
        x = -0.4 + k * 0.4
        rbox(bm, (x, -0.275, 0.44), (0.37, 0.02, 0.62), CREAM, r=0.01)
        rbox(bm, (x + (0.12 if k != 1 else 0), -0.29, 0.62), (0.08, 0.015, 0.02), GREY, r=0.005)
    rbox(bm, (0, 0, 0.84), (1.24, 0.58, 0.05), BLACK, r=0.012)
    rnd = random.Random(191)
    for k in range(24):
        sphere(bm, (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.27, 0.27), 0.866), (0.01, 0.01, 0.003), GREY, segs=(6, 3))
    rbox(bm, (-0.05, -0.04, 0.866), (0.44, 0.32, 0.008), GREY, r=0.02)
    rbox(bm, (-0.05, -0.04, 0.869), (0.38, 0.26, 0.006), LIGHTGREY, r=0.02)
    capsule(bm, (-0.05, 0.18, 0.86), (-0.05, 0.18, 1.08), 0.016, BLACK, segs=8)
    capsule(bm, (-0.05, 0.18, 1.08), (-0.05, 0.05, 1.05), 0.014, BLACK, segs=8)
    rbox(bm, (0, 0.27, 1.07), (1.24, 0.04, 0.42), CREAM_D, r=0.008)
    for k in range(1, 3):
        rbox(bm, (0, 0.248, 0.865 + k * 0.14), (1.2, 0.006, 0.01), WHITE, r=0.002)
    for k in range(1, 8):
        rbox(bm, (-0.62 + k * 0.155, 0.248, 1.07), (0.01, 0.006, 0.4), WHITE, r=0.002)
    rbox(bm, (0.4, 0.0, 0.9), (0.26, 0.18, 0.04), WHITE, r=0.008)
    for k in range(4):
        cyl(bm, (0.32 + k * 0.05, 0.0, 0.99), 0.07, 0.012, WHITE if k % 2 else CREAM, rot=(0, 90, 0), segs=20, bevel=0.5)
    potted(bm, (-0.48, 0.12, 0.865), 0.06, 0.08, YELLOW, 0.26, seed=192)


def microwave(bm):
    rbox(bm, (0, 0, 0.04), (0.66, 0.46, 0.08), CREAM_D, r=0.01)
    rbox(bm, (0, 0, 0.45), (0.7, 0.5, 0.74), CREAM, r=0.02)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.17, -0.25, 0.44), (0.32, 0.02, 0.62), CREAM, r=0.01)
        rbox(bm, (sx * 0.04, -0.265, 0.62), (0.015, 0.012, 0.08), GREY, r=0.004)
    rbox(bm, (0, 0, 0.835), (0.72, 0.52, 0.03), WOOD, r=0.008)
    rbox(bm, (0, 0, 1.0), (0.54, 0.38, 0.3), WHITE, r=0.03)
    rbox(bm, (-0.06, -0.19, 1.0), (0.34, 0.012, 0.22), BLACK, r=0.01)
    rbox(bm, (0.19, -0.19, 1.0), (0.1, 0.012, 0.22), LIGHTGREY, r=0.008)
    for k in range(6):
        cyl(bm, (0.17 + (k % 2) * 0.04, -0.195, 0.95 + (k // 2) * 0.04), 0.012, 0.006, GREY, rot=(90, 0, 0), segs=8)
    rbox(bm, (0.19, -0.198, 1.075), (0.07, 0.006, 0.03), BR_GREEN, r=0.003)


def water_filter(bm):
    for a in range(3):
        ang = math.radians(90 + 120 * a)
        capsule(bm, (0.17 * math.cos(ang), 0.17 * math.sin(ang), 0.02), (0.12 * math.cos(ang), 0.12 * math.sin(ang), 0.3), 0.022, WOOD_D, segs=8)
    cyl(bm, (0, 0, 0.3), 0.19, 0.04, WOOD, segs=24)
    lathe(bm, [(0, 0.34), (0.13, 0.34), (0.19, 0.42), (0.2, 0.55), (0.17, 0.62), (0, 0.62)], TERRA, segs=24)
    lathe(bm, [(0, 0.6), (0.15, 0.6), (0.18, 0.66), (0.18, 0.86), (0.15, 0.9), (0, 0.9)], TERRA, segs=24)
    lathe(bm, [(0, 0.89), (0.14, 0.89), (0.1, 0.95), (0, 0.97)], TERRA, segs=20)
    sphere(bm, (0, 0, 0.98), (0.03, 0.03, 0.025), TERRA, segs=(8, 5))
    for z, R in ((0.61, 0.17), (0.88, 0.165), (0.45, 0.195)):
        ring(bm, (0, 0, z), R, 0.012, BROWN, segs=24, rsegs=5)
    capsule(bm, (0, -0.18, 0.44), (0, -0.25, 0.43), 0.018, GREY, segs=8)
    capsule(bm, (0, -0.25, 0.43), (0, -0.25, 0.39), 0.012, GREY, segs=6)
    rbox(bm, (0, -0.23, 0.475), (0.012, 0.012, 0.05), GREY, r=0.004)


def br_spice_shelf(bm):
    for z in (0.15, 0.48):
        rbox(bm, (0, 0, z), (0.7, 0.18, 0.03), WOOD, r=0.008)
        for sx in (-1, 1):
            rbox(bm, (sx * 0.28, 0.07, z - 0.06), (0.025, 0.04, 0.1), WOOD_D, r=0.006)
    cols = (ORANGE, JRED, YELLOW, BR_GREEN, BROWN)
    for k in range(5):
        jar(bm, (-0.27 + k * 0.1, -0.01, 0.165), GLASS_G if k % 2 else CREAM, 0.1, 0.035, cols[k])
    for k in range(3):
        jar(bm, (-0.26 + k * 0.1, -0.01, 0.495), CREAM, 0.12, 0.04, cols[(k + 2) % 5])
    potted(bm, (0.2, 0.0, 0.495), 0.07, 0.1, TERRA, 0.3, seed=201, vines=2)


def br_dining_table(bm):
    for a in range(4):
        ang = math.radians(45 + 90 * a)
        cyl(bm, (0.25 * math.cos(ang), 0.25 * math.sin(ang), 0), 0.03, 0.56, WOOD_D, segs=10)
    lathe(bm, [(0, 0.55), (0.52, 0.55), (0.56, 0.57), (0.56, 0.76), (0.52, 0.78), (0, 0.78)], BR_BLUE, segs=36)
    for k in range(6):
        a = 2 * math.pi * k / 6
        daisy(bm, (0.38 * math.cos(a), 0.38 * math.sin(a), 0.785), 0.07, petal=YELLOW, centre=JRED, n=5, h=0.006)
        daisy(bm, (0.563 * math.cos(a + 0.5), 0.563 * math.sin(a + 0.5), 0.65), 0.055, petal=YELLOW, centre=WHITE, n=5, h=0.005, face=(90, 0, math.degrees(a + 0.5) + 90))
    lathe(bm, [(0, 0.78), (0.07, 0.78), (0.14, 0.84), (0.14, 0.85), (0, 0.85)], WHITE)
    for p, s in (((0.03, 0.02, 0.87), ORANGE), ((-0.05, -0.03, 0.87), YELLOW), ((0.05, -0.05, 0.875), BR_GREEN), ((-0.02, 0.06, 0.88), ORANGE)):
        sphere(bm, p, (0.045, 0.045, 0.042), s, segs=(12, 6))
    plastic_chair(bm, (-0.78, 0, 0), 90)
    plastic_chair(bm, (0.78, 0, 0), -90)


def br_plastic_chair(bm):
    plastic_chair(bm)


def br_blender(bm):
    rbox(bm, (0, 0, 0.08), (0.2, 0.2, 0.16), JRED, r=0.04)
    cyl(bm, (0, -0.105, 0.08), 0.025, 0.02, LIGHTGREY, rot=(90, 0, 0), segs=12)
    lathe(bm, [(0, 0.16), (0.07, 0.16), (0.08, 0.18), (0.095, 0.44), (0, 0.44)], GLASS, segs=16)
    lathe(bm, [(0, 0.17), (0.07, 0.17), (0.08, 0.26), (0, 0.26)], JRED, segs=16)
    cyl(bm, (0, 0, 0.44), 0.1, 0.035, BLACK, segs=16)
    cyl(bm, (0, 0, 0.47), 0.03, 0.025, BLACK, segs=10)
    ring(bm, (0.12, 0, 0.32), 0.07, 0.016, GLASS, rot=(90, 0, 0), segs=16, rsegs=5, sy=1.3)


def cookware(bm):
    for sx in (-1, 1):
        rbox(bm, (sx * 0.31, 0, 0.32), (0.035, 0.36, 0.64), WOOD, r=0.008)
    for z in (0.02, 0.32, 0.63):
        rbox(bm, (0, 0, z), (0.65, 0.36, 0.035), WOOD, r=0.008)
    rbox(bm, (0, 0.17, 0.32), (0.6, 0.02, 0.6), WOOD_D, r=0.004)
    for (x, z, s) in ((-0.14, 0.037, BR_GREEN), (0.14, 0.037, PURPLE), (-0.14, 0.338, BR_BLUE), (0.14, 0.338, JRED)):
        lathe(bm, [(0, z), (0.1, z), (0.105, z + 0.12), (0, z + 0.12)], s, (x, -0.01, 0), segs=20)
        lathe(bm, [(0, z + 0.115), (0.108, z + 0.115), (0.09, z + 0.14), (0, z + 0.15)], s, (x, -0.01, 0), segs=20)
        sphere(bm, (x, -0.01, z + 0.16), (0.018, 0.018, 0.014), BLACK, segs=(8, 5))
        for sx in (-1, 1):
            rbox(bm, (x + sx * 0.115, -0.01, z + 0.1), (0.03, 0.04, 0.02), BLACK, r=0.006)


def utensil_holder(bm):
    lathe(bm, [(0, 0), (0.08, 0), (0.085, 0.22), (0.09, 0.23), (0, 0.23)], WHITE)
    ring(bm, (0, 0, 0.03), 0.082, 0.008, BR_BLUE, segs=20, rsegs=5)
    ring(bm, (0, 0, 0.2), 0.087, 0.008, BR_BLUE, segs=20, rsegs=5)
    for k in range(3):
        a = math.radians(-90 + 120 * k)
        daisy(bm, (0.087 * math.cos(a), 0.087 * math.sin(a), 0.115), 0.035, petal=BR_BLUE, centre=WHITE, n=5, h=0.004, face=(90, 0, math.degrees(a) + 90))
    for x, tilt, kind in ((-0.03, -14, 0), (0.0, 2, 1), (0.035, 14, 2)):
        top = Vector((x + 0.2 * math.sin(math.radians(tilt)), 0, 0.42))
        capsule(bm, (x * 0.5, 0, 0.05), top, 0.009, WOOD, segs=8)
        if kind == 1:
            rbox(bm, tuple(top + Vector((0, 0, 0.04))), (0.06, 0.012, 0.1), WOOD_L, r=0.015, rot=(0, tilt, 0))
        else:
            sphere(bm, tuple(top + Vector((0, 0, 0.04))), (0.035, 0.015, 0.05), WOOD_L, rot=(0, tilt, 0), segs=(10, 6))


def kitchen_mat(bm):
    rbox(bm, (0, 0, 0.01), (1.0, 0.6, 0.02), BR_BLUE, r=0.008)
    for sy in (-1, 1):
        rbox(bm, (0, sy * 0.26, 0.021), (0.94, 0.02, 0.003), WHITE, r=0.001)
        rbox(bm, (sy * 0.46, 0, 0.021), (0.02, 0.54, 0.003), WHITE, r=0.001)
    for i in range(7):
        for j in range(3):
            x, y = -0.36 + i * 0.12, -0.12 + j * 0.12
            rbox(bm, (x, y, 0.021), (0.06, 0.06, 0.003), WHITE, r=0.001, rot=(0, 0, 45))
            rbox(bm, (x, y, 0.0225), (0.025, 0.025, 0.003), BR_BLUE_D, r=0.001, rot=(0, 0, 45))


AREAS_BR = {
    "Bathroom": [("ShowerStall", shower_stall), ("Toilet", toilet), ("BathSink", bath_granite_sink), ("Shelf", bath_shelf),
                 ("LaundryBasketWhite", laundry_basket_white), ("TowelRack", br_towel_rack), ("BathMat", flag_bath_mat), ("Plant", zz_plant),
                 ("ToiletryBasket", toiletry_basket), ("ToiletPaperHolder", tp_holder), ("Mirror", br_mirror), ("Stool", blue_stool)],
    "LivingRoom": [("Sofa", br_sofa), ("CoffeeTable", br_coffee_table), ("Armchair", br_armchair), ("TVStand", br_tv_stand),
                   ("MonsteraPlant", costela_adao), ("WallArtBeach", wall_art_beach), ("ZebraRug", zebra_rug), ("FloorLamp", tripod_lamp),
                   ("RecordPlayer", record_player), ("BarCart", bar_cart), ("HangingPlant", hanging_plant), ("Hammock", hammock)],
    "Bedroom": [("Bed", br_bed), ("Nightstand", br_nightstand), ("Wardrobe", br_wardrobe), ("FullMirror", full_mirror),
                ("Dresser", br_dresser), ("Pouf", br_pouf), ("Rug", wavy_rug), ("SnakePlant", snake_plant),
                ("WallShelves", wall_shelves), ("WallArtPalm", wall_art_palm), ("LaundryBasketFabric", fabric_laundry_basket), ("CoatRack", coat_rack)],
    "Kitchen": [("Refrigerator", br_fridge), ("Stove", br_stove), ("KitchenSink", kitchen_granite_sink), ("Microwave", microwave),
                ("WaterFilter", water_filter), ("SpiceShelf", br_spice_shelf), ("DiningTable", br_dining_table), ("PlasticChair", br_plastic_chair),
                ("Blender", br_blender), ("Cookware", cookware), ("Utensils", utensil_holder), ("KitchenMat", kitchen_mat)],
}


def build_brazil(only=None):
    return build_decor(only, AREAS_BR, "SM_DecorBR_", "DecorBrazil", "DecorBR_", -300.0)


def render_brazil_previews(out_dir, only=None, size=360):
    render_decor_previews(out_dir, only, size, AREAS_BR, "SM_DecorBR_")
