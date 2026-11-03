# Themed loot boxes (gab, 2026-11-02): the carrot loot box (lootbox.py, same shapes and pivots) recoloured
# for the three house decor sets, each with its own emblem on the front plate instead of the carrot:
#   Cozy       cream body, pink bumpers, warm wood fittings, a red heart, pink glow
#   Japanese   red lacquer body, black bumpers, gold fittings, a sakura blossom, pink glow
#   Brazilian  sunny yellow body, green bumpers, blue fittings, a monstera leaf, green glow
# Meshes SM_LootBox<Theme>_Base / _Lid in the LootBox collection (pivots as in lootbox.py).
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/lootbox_themes.py")).read())
#   build_lootbox_themes()
exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/lootbox.py")).read())

_ROWS = {"r1": (6, 316), "r3": (712, 1003), "r4": (1040, 1331)}  # atlas pixel rows, top down


def strip(row, col, t0=0.0, t1=1.0):
    """(u, v at the part's bottom, v at its top) of one atlas gradient column; t0/t1 pick a part of it."""
    y0, y1 = _ROWS[row]
    v = lambda t: 1 - (y0 + (y1 - y0) * t) / 2048
    return ((28 + 57 * col) / 2048, v(t0), v(t1))


def slab(bm, outline, col, thick=0.1, bulge=0.06, inner=0.5, center=None, at=(0, 0, 0), rot=0.0, depth=0.0):
    """Chunky 2D shape (outline of (x, z) points, even count) extruded along Y with domed faces (seasons.py)."""
    n = len(outline)
    cx, cz = center if center else (sum(p[0] for p in outline) / n, sum(p[1] for p in outline) / n)
    b = bmesh.new()

    def side(sign):
        ring = [b.verts.new((x, sign * thick / 2, z)) for x, z in outline]
        inn = [b.verts.new((cx + (x - cx) * inner, sign * (thick / 2 + bulge * 0.7), cz + (z - cz) * inner)) for x, z in outline]
        mid = b.verts.new((cx, sign * (thick / 2 + bulge), cz))
        return ring, inn, mid
    fr, fi, fm = side(-1)
    br, bi, bmid = side(1)
    for i in range(n):
        j = (i + 1) % n
        b.faces.new((fr[i], fr[j], br[j], br[i]))
        b.faces.new((fr[i], fi[i], fi[j], fr[j]))
        b.faces.new((br[j], bi[j], bi[i], br[i]))
    for i in range(0, n, 2):
        b.faces.new((fm, fi[(i + 2) % n], fi[i + 1], fi[i]))
        b.faces.new((bmid, bi[i], bi[i + 1], bi[(i + 2) % n]))
    uv_part(b, col)
    bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(rot), 3, 'Y'), verts=b.verts)
    bmesh.ops.translate(b, vec=Vector(at) + Vector((0, depth, 0)), verts=b.verts)
    merge(bm, b)


def ellipse(rx, rz, n=12, z0=0.0, pinch=0.0):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        x, z = rx * math.cos(a), rz * math.sin(a)
        if z < 0:
            x *= 1 - pinch * (-z / rz)
        pts.append((x, z + z0))
    return pts


def heart_emblem(bm, center, col, hi):
    """A plump heart with a small shine on its upper left lobe."""
    pts = []
    n = 24
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        z = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * 0.0105, z * 0.0105))
    c = Vector(center)
    slab(bm, pts, col, thick=0.05, bulge=0.035, inner=0.55, center=(0, 0.02), at=(c.x, c.y, c.z))
    slab(bm, ellipse(0.022, 0.032, 8), hi, thick=0.02, bulge=0.01, at=(c.x - 0.07, c.y - 0.04, c.z + 0.05), rot=-35)


def sakura_emblem(bm, center, petal, middle):
    """Five rounded petals round a yellow centre."""
    c = Vector(center)
    for i in range(5):
        slab(bm, ellipse(0.062, 0.085, 12, z0=0.085, pinch=0.55), petal, thick=0.04, bulge=0.03, inner=0.55, center=(0, 0.085), at=(c.x, c.y, c.z), rot=72 * i)
    slab(bm, ellipse(0.04, 0.04, 12), middle, thick=0.05, bulge=0.03, at=(c.x, c.y - 0.03, c.z))
    for i in range(5):  # stamens
        a = math.radians(72 * i + 36)
        rbox(bm, (c.x + math.sin(a) * 0.05, c.y - 0.06, c.z + math.cos(a) * 0.05), (0.018, 0.018, 0.018), middle, cuts=2, power=2.2)


def monstera_emblem(bm, center, leaf, dark, stem):
    """A tilted monstera leaf: a wide heart-shaped blade, darker slits from the midrib, a stem."""
    c = Vector(center)
    tilt = -18
    blade = []
    n = 20
    for i in range(n):
        a = 2 * math.pi * i / n
        x = 0.16 * math.sin(a)
        z = 0.15 * math.cos(a) + 0.03 * math.cos(2 * a)
        if abs(math.sin(a)) < 0.2 and math.cos(a) > 0:   # the notch at the top
            z -= 0.03
        blade.append((x, z))
    slab(bm, blade, leaf, thick=0.04, bulge=0.025, inner=0.6, center=(0, 0), at=(c.x, c.y, c.z + 0.02), rot=tilt)
    R = Matrix.Rotation(math.radians(tilt), 3, 'Y')
    rbox_rot = lambda p, size, col: rbox(bm, tuple(c + R @ Vector(p)), size, col, cuts=2, power=3.0)
    for z in (-0.06, 0.0, 0.06):   # slits either side of the midrib
        for sx in (-1, 1):
            p = Vector((sx * 0.085, -0.04, z + 0.02))
            rbox(bm, tuple(c + R @ p), (0.07, 0.012, 0.016), dark, cuts=2, power=3.0)
    rbox(bm, tuple(c + R @ Vector((0, -0.04, 0.02))), (0.016, 0.014, 0.24), dark, cuts=2, power=3.0)  # midrib
    shaped(bm, (0.024, 0.024, 0.16), stem, lambda t: 1.0, tilt + 25, tuple(c + R @ Vector((0.02, -0.01, -0.17))), cuts=3, power=2.4)


THEMES = {
    "Cozy": dict(
        ORANGE=strip("r3", 14, 0.15, 0.55), CREAM=c1(9, 0.79, 0.826), CREAM_L=c1(9, 0.80, 0.828), CREAM_D=strip("r3", 22, 0.25, 0.5),
        METAL=strip("r3", 22, 0.2, 0.6), RIVET=strip("r4", 2, 0.2, 0.5), GLOW=strip("r4", 11, 0.15, 0.4),
        emblem=lambda bm, at: heart_emblem(bm, at, strip("r4", 3, 0.15, 0.6), c1(9, 0.80, 0.828))),
    "Japanese": dict(
        ORANGE=c1(7, 0.70, 0.79), CREAM=strip("r1", 14, 0.2, 0.5), CREAM_L=c1(9, 0.80, 0.828), CREAM_D=c1(7, 0.70, 0.78),
        METAL=strip("r4", 16, 0.2, 0.6), RIVET=strip("r4", 2, 0.2, 0.5), GLOW=strip("r4", 11, 0.15, 0.4),
        emblem=lambda bm, at: sakura_emblem(bm, at, strip("r4", 11, 0.1, 0.45), strip("r4", 8, 0.2, 0.6))),
    "Brazilian": dict(
        ORANGE=strip("r1", 13, 0.15, 0.55), CREAM=strip("r4", 0, 0.1, 0.45), CREAM_L=c1(9, 0.80, 0.828), CREAM_D=strip("r4", 10, 0.2, 0.6),
        METAL=strip("r4", 10, 0.2, 0.6), RIVET=c1(9, 0.80, 0.828), GLOW=strip("r1", 22, 0.1, 0.4),
        emblem=lambda bm, at: monstera_emblem(bm, at, strip("r1", 13, 0.1, 0.45), strip("r3", 7, 0.2, 0.6), strip("r1", 9, 0.3, 0.7))),
}


def build_lootbox_themes(only=None):
    global LB_ORANGE, LB_CREAM, LB_CREAM_L, LB_CREAM_D, LB_METAL, LB_RIVET, LB_GLOW, carrot
    mat = bpy.data.materials["M_GradientTexture"]
    glow = bpy.data.materials["M_GradientGlow"]
    coll = bpy.data.collections["LootBox"]
    made = []
    for i, (name, t) in enumerate(THEMES.items()):
        if only and name not in only:
            continue
        LB_ORANGE, LB_CREAM, LB_CREAM_L, LB_CREAM_D = t["ORANGE"], t["CREAM"], t["CREAM_L"], t["CREAM_D"]
        LB_METAL, LB_RIVET, LB_GLOW = t["METAL"], t["RIVET"], t["GLOW"]
        emblem = t["emblem"]
        carrot = lambda bm, at, **k: emblem(bm, at)
        x = 1.6 * (i + 1)
        bm = bmesh.new()
        body(bm)
        base = finish(bm, f"SM_LootBox{name}_Base", coll, (x, 0, 0), mat)
        bm = bmesh.new()
        lid(bm)
        top = finish(bm, f"SM_LootBox{name}_Lid", coll, (x, D / 2, H), mat)
        for o in (base, top):
            o.data.materials.append(glow)
        made += [base.name, top.name]
    return made
