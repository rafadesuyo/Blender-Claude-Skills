# Player barn (sheet 54) in the NewLua pack style: red plank walls with cream corner trims and
# base, gambrel roof of purple shingle boards, cream gable trim, loft window with an X, side
# windows, a wide open front with a cream frame, and an orange timber frame + plank floor inside.
# Pivot at the bottom centre, front (the opening) -Y, ~6.6 m wide x 6.6 m deep x 6 m tall.
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/barn.py")).read())
#   build_barn()
#
# NO Z-FIGHTING RULE (Dante, 2026-10-24): no two parts may have faces in the same plane facing the
# same way where they overlap. Every part below is placed so its faces sit at their own depth
# (walls stop at the eaves, trims stand 4+ mm proud or recessed, frame bars butt instead of
# overlapping, neighbouring roof boards use different gaps). build_barn() runs zfight() and must
# report 0.
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/gates2.py")).read())
exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/zfight_check.py")).read())

RED = c0(6, 0.885, 0.93)
RED_DARK = c0(14, 0.88, 0.93)
ROOF_P = c1(3, 0.755, 0.785)
ROOF_P2 = c1(3, 0.74, 0.765)
TIMBER = c1(1, 0.77, 0.81)
FLOOR = c1(1, 0.79, 0.83)
TRIM = CREAM
WIN_PANEL = None        # None = dark wall colour; a colour (or glow) for lit windows
LOFT_WINDOW = True
SIDE_WINDOWS = True
DOOR_POST = None        # None = cream box posts; else fn(bm, x) builds one post
GABLE_HOLES = []        # (x0, x1, z0, z1) areas on the front gable kept clear of plank seams
SIDE_HOLES = []         # same on the side walls (y0, y1, z0, z1)
FRONT_HOLES = []        # same on the front wall beside the opening (x0, x1, z0, z1)

HW = 3.0          # half width (wall centre lines)
HD = 3.0          # half depth
WT = 0.2          # wall thickness: outer faces at HW + 0.1 / HD + 0.1
WALL = 3.2        # eave height (walls stop here, the gables start here)
OPEN_W = 2.0      # half width of the front opening
OPEN_H = 3.0
WALL_Z0 = 0.12    # walls start inside the base
PROFILE = [(-HW - 0.25, WALL), (-HW + 0.75, 4.75), (0.0, 5.75), (HW - 0.75, 4.75), (HW + 0.25, WALL)]
FACE = HW + WT / 2   # outer wall faces (x = +-FACE on the sides, y = +-FACE front / back)


def seam(bm, u, z0, z1, holes, at, axis, out):
    """One vertical plank seam at u (x on a front/back wall, y on a side wall) from z0 to z1, cut
    around holes (u0, u1, z0, z1). 'at' = the wall face; out = +1/-1, the side the seam stands on."""
    spans = [(z0, z1)]
    for hu0, hu1, hz0, hz1 in holes:
        if hu0 - 0.03 <= u <= hu1 + 0.03:
            spans = [p for a, b in spans for p in ((a, min(b, hz0)), (max(a, hz1), b)) if p[1] - p[0] > 0.12]
    c = at + out * 0.012   # 0.03 thick: 3 mm into the wall, 27 mm proud
    for a, b in spans:
        if axis == 'X':
            box(bm, (u, c, (a + b) / 2), (0.035, 0.03, b - a), RED_DARK)
        else:
            box(bm, (c, u, (a + b) / 2), (0.03, 0.035, b - a), RED_DARK)


def planks_x(bm, x0, x1, z0, z1, y, out, holes=(), step=0.38):
    """Seams on a front/back wall, mirrored about x = 0, strictly inside x0..x1."""
    x = step / 2
    while x < max(abs(x0), abs(x1)):
        for u in (x, -x):
            if x0 + 0.1 < u < x1 - 0.1:
                seam(bm, u, z0, z1, holes, y, 'X', out)
        x += step


def planks_y(bm, y0, y1, z0, z1, x, out, holes=(), step=0.38):
    y = step / 2
    while y < max(abs(y0), abs(y1)):
        for u in (y, -y):
            if y0 + 0.1 < u < y1 - 0.1:
                seam(bm, u, z0, z1, holes, x, 'Y', out)
        y += step


def window(bm, c, w, h, axis, out):
    """Cream window on a wall face: dark panel (3 cm proud), a frame whose bars butt (top/bottom
    full width, sides between them, at a different depth) and an X between them."""
    x, y, z = c          # centre ON the wall face
    t = 0.09

    def put(du, dz, su, sz, depth0, depth1, col):   # du along the wall, depth from the face outward
        dc = out * (depth0 + depth1) / 2
        if axis == 'X':
            box(bm, (x + dc, y + du, z + dz), (depth1 - depth0, su, sz), col)
        else:
            box(bm, (x + du, y + dc, z + dz), (su, depth1 - depth0, sz), col)

    put(0, 0, w - 0.02, h - 0.02, 0.0, 0.03, WIN_PANEL or RED_DARK)
    for dz in (-1, 1):
        put(0, dz * (h / 2 - t / 2), w, t, 0.008, 0.1, TRIM)
    for du in (-1, 1):
        put(du * (w / 2 - t / 2), 0, t, h - 2 * t, 0.012, 0.092, TRIM)
    a0, a1 = -w / 2 + t, w / 2 - t
    b0, b1 = -h / 2 + t, h / 2 - t
    for sgn, dd in ((1, 0.052), (-1, 0.062)):   # the two X bars at different depths (they cross)
        if axis == 'X':
            beam(bm, (x + out * dd, y + a0, z + sgn * b0), (x + out * dd, y + a1, z + sgn * b1), 0.045, 0.06, TRIM)
        else:
            beam(bm, (x + a0, y + out * dd, z + sgn * b0), (x + a1, y + out * dd, z + sgn * b1), 0.045, 0.06, TRIM)


def gable_top(x):
    """Height of the gable outline at x."""
    pts = [(-HW, WALL), (-HW + 0.72, 4.62), (0.0, 5.6), (HW - 0.72, 4.62), (HW, WALL)]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return WALL


def gable(bm, y, front):
    """The red end wall above the eaves (gambrel outline), WT thick, starting exactly at WALL."""
    pts = [(-HW - WT / 2, WALL), (0.0, WALL), (HW + WT / 2, WALL), (HW - 0.72, 4.62), (0.0, 5.6), (-HW + 0.72, 4.62)]
    slab(bm, pts, RED, WT, 0.0, 0.6, center=(0.0, 4.2), at=(0, y, 0))
    sy = -1 if front else 1
    edge = [(x, y + sy * 0.15, z + 0.02) for x, z in [(-HW - 0.14, WALL - 0.05), (-HW + 0.72, 4.68), (0.0, 5.68), (HW - 0.72, 4.68), (HW + 0.14, WALL - 0.05)]]
    band(bm, edge, 0.13, 0.24, TRIM)
    # seams on the gable, under the trim, around the loft window on the front
    holes = [(-0.52, 0.52, 3.9, 4.8)] if (front and LOFT_WINDOW) else list(GABLE_HOLES if front else [])
    x = 0.19
    while x < HW - 0.2:
        for u in (x, -x):
            top = gable_top(u) - 0.32
            if top > WALL + 0.35:
                seam(bm, u, WALL + (0.25 if front else 0.03), top, holes, y + sy * WT / 2, 'X', sy)
        x += 0.38


def roof(bm):
    depth = 2 * HD + 0.5
    # one continuous deck under the boards (closed roof), a little shorter so its ends stay hidden
    band(bm, [(x, 0, z + 0.07) for x, z in PROFILE], depth - 0.12, 0.12, ROOF_P2)
    n = 9
    for i in range(len(PROFILE) - 1):
        (x0, z0), (x1, z1) = PROFILE[i], PROFILE[i + 1]
        ln = math.hypot(x1 - x0, z1 - z0)
        ux, uz = (x1 - x0) / ln * 0.07, (z1 - z0) / ln * 0.07
        for r in range(2):
            a = (x0 + (x1 - x0) * r / 2 - ux, z0 + (z1 - z0) * r / 2 - uz)
            b = (x0 + (x1 - x0) * (r + 1) / 2 + ux, z0 + (z1 - z0) * (r + 1) / 2 + uz)
            # neighbouring rows (they overlap at their ends) use different gaps, so their board
            # sides never share a plane
            gap = 0.012 if (2 * i + r) % 2 == 0 else 0.032
            lift = 0.07 if r == 0 else 0.0
            for k in range(n):
                y0 = -depth / 2 + depth * k / n
                y1 = -depth / 2 + depth * (k + 1) / n
                band(bm, [(a[0], (y0 + y1) / 2, a[1] + 0.12 + lift), (b[0], (y0 + y1) / 2, b[1] + 0.12 + lift)], (y1 - y0) - gap, 0.14,
                     ROOF_P if (k + r) % 2 == 0 else ROOF_P2)
    beam(bm, (0, -depth / 2 - 0.02, 5.95), (0, depth / 2 + 0.02, 5.95), 0.3, 0.16, ROOF_P2)


def g_barn(bm):
    # base + floor
    box(bm, (0, 0, 0.1), (2 * HW + 0.3, 2 * HD + 0.3, 0.2), TRIM)
    span = 2 * HD - 0.6
    for i in range(10):
        box(bm, (0, -HD + 0.3 + span * (i + 0.5) / 10, 0.22), (2 * HW - 0.3, span / 10 - 0.03, 0.04), FLOOR if i % 2 else TIMBER)
    # walls, no overlaps: front/back run the full width, the sides fit between them
    zc, zh = (WALL_Z0 + WALL) / 2, WALL - WALL_Z0
    box(bm, (0, HD, zc), (2 * FACE, WT, zh), RED)
    for sx in (-1, 1):
        box(bm, (sx * HW, 0, zc), (WT, 2 * HD - WT, zh), RED)
        box(bm, (sx * (OPEN_W + FACE) / 2, -HD, zc), (FACE - OPEN_W, WT, zh), RED)
    box(bm, (0, -HD, (OPEN_H + WALL) / 2), (2 * OPEN_W, WT, WALL - OPEN_H), RED)
    # seams: sides around the windows, front beside the frame, back all over
    win_y, win_z, win_w, win_h = -0.6, 1.7, 0.75, 0.95
    for sx in (-1, 1):
        planks_y(bm, -FACE + 0.17, FACE - 0.17, 0.25, WALL - 0.02, sx * FACE, sx,
                 ([(win_y - win_w / 2, win_y + win_w / 2, win_z - win_h / 2, win_z + win_h / 2)] if SIDE_WINDOWS else []) + list(SIDE_HOLES))
    for x0, x1 in ((-FACE + 0.17, -OPEN_W - 0.27), (OPEN_W + 0.27, FACE - 0.17)):
        planks_x(bm, x0, x1, 0.25, WALL - 0.02, -FACE, -1, FRONT_HOLES)
    planks_x(bm, -FACE + 0.17, FACE - 0.17, 0.25, WALL - 0.02, FACE, 1)
    # gables front and back (with their trim and seams)
    gable(bm, -HD, True)
    gable(bm, HD, False)
    # corner trims (proud of both walls), their base blocks, eave boards
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(bm, (sx * HW, sy * HD, (0.3 + WALL + 0.06) / 2), (0.34, 0.34, WALL + 0.06 - 0.3), TRIM)
            box(bm, (sx * HW, sy * HD, (0.05 + 0.42) / 2), (0.42, 0.42, 0.37), TRIM)
        box(bm, (sx * (FACE + 0.03), 0, WALL + 0.08), (0.1, 2 * HD + 0.32, 0.2), TRIM)
    # the opening frame: posts + a top band with angled corners (own depths, never the wall's)
    for sx in (-1, 1):
        if DOOR_POST:
            DOOR_POST(bm, sx * (OPEN_W + 0.1))
        else:
            box(bm, (sx * (OPEN_W + 0.1), -HD - 0.05, (0.15 + OPEN_H + 0.15) / 2), (0.3, 0.38, OPEN_H + 0.15 - 0.15), TRIM)
    band(bm, [(-OPEN_W - 0.25, -HD - 0.05, OPEN_H - 0.1), (-OPEN_W + 0.25, -HD - 0.05, OPEN_H + 0.25),
              (OPEN_W - 0.25, -HD - 0.05, OPEN_H + 0.25), (OPEN_W + 0.25, -HD - 0.05, OPEN_H - 0.1)], 0.42, 0.3, TRIM)
    # loft window (front gable) + side windows
    if LOFT_WINDOW:
        window(bm, (0, -FACE, 4.35), 0.9, 0.75, 'Y', -1)
    if SIDE_WINDOWS:
        for sx in (-1, 1):
            window(bm, (sx * FACE, win_y, win_z), win_w, win_h, 'X', sx)
    # timber frame inside: posts 0.22, rails 0.26 (top) / 0.12 (low), each at its own depth
    by = HD - WT / 2 - 0.15        # back row centre line
    for x in (-OPEN_W + 0.2, 0.0, OPEN_W - 0.2):
        box(bm, (x, by, (0.24 + OPEN_H) / 2), (0.22, 0.22, OPEN_H - 0.24), TIMBER)
        for sx in (-1, 1):
            if (x < 0 and sx < 0) or (x > 0 and sx > 0):
                continue
            beam(bm, (x + sx * 0.1, by, OPEN_H - 0.75), (x + sx * 0.6, by, OPEN_H - 0.08), 0.16, 0.16, TIMBER)
    box(bm, (0, by, OPEN_H + 0.02), (2 * HW - 0.5, 0.26, 0.24), TIMBER)
    box(bm, (0, by + 0.05, 1.0), (2 * HW - 0.5, 0.1, 0.16), TIMBER)
    sxl = HW - WT / 2 - 0.15
    for sx in (-1, 1):
        box(bm, (sx * sxl, 0, (0.24 + OPEN_H) / 2), (0.22, 0.22, OPEN_H - 0.24), TIMBER)
        box(bm, (sx * sxl, 0, OPEN_H - 0.02), (0.26, 2 * HD - 0.9, 0.2), TIMBER)
        box(bm, (sx * (sxl + 0.05), 0, 1.0), (0.1, 2 * HD - 0.9, 0.16), TIMBER)
        for sy in (-1, 1):
            beam(bm, (sx * sxl, sy * 0.1, OPEN_H - 0.8), (sx * sxl, sy * 0.7, OPEN_H - 0.1), 0.16, 0.16, TIMBER)
    box(bm, (0, -HD + WT / 2 + 0.13, OPEN_H + 0.03), (2 * OPEN_W + 0.2, 0.22, 0.2), TIMBER)
    roof(bm)


def build_barn(name="SM_Barn_Default", y=-100.0, extras=None):
    """The barn (flat shaded: boxes and flat slabs) + optional extras(bm) decorations, whose round
    parts (islands of more than 6 faces) are smooth shaded."""
    root = bpy.data.collections.get("Barn") or bpy.data.collections.new("Barn")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    bm = bmesh.new()
    g_barn(bm)
    flags = [False] * len(bm.faces)
    if extras:
        ext = bmesh.new()
        extras(ext)
        part = _islands(ext)
        sizes = {}
        for f in ext.faces:
            sizes[part[f.index]] = sizes.get(part[f.index], 0) + 1
        flags += [sizes[part[f.index]] > 6 for f in ext.faces]
        merge(bm, ext)
    o = finish_lamp(bm, name, root, (0, y, 0))
    for p, sm in zip(o.data.polygons, flags):
        p.use_smooth = sm
    return check_closed([o]), zfight(o), [round(d, 2) for d in o.dimensions]
