# gab (2026-11-04): two props in the barn style (barn.py helpers, gradient atlas, closed shells):
#  - SM_BarnNameSign: a cute hanging wooden board over the barn door ("YOUR BARN" 3D text from
#    Textify sits on it in game). Built in BARN-LOCAL coordinates (same pivot as the barns), so in
#    UEFN it goes on the barn's entity at the identity transform and fits every barn design (it
#    stays under the gable decorations: hung from iron arms just above the door trim).
#  - SM_QuestBooth: Walter's thin little quest stall: plank counter, slim posts, a striped green /
#    cream awning with scallops, a notice board full of quest notes at the back and an arched title
#    board on top ("QUESTS" text in game) with a gold "!" on it. Pivot bottom centre, front -Y.
#   exec(open(r"<skills>/blender-game-props/quest_booth.py").read())
#   build_quest_props()      # -> checks; place_preview() puts a sign copy on every barn design
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

exec(open(_skill("blender-game-props/barn_shop.py")).read())

Q_GREEN = c0(13, 0.86, 0.92)
Q_PAPER = CREAM
Q_PAPER2 = c0(16, 0.86, 0.91)     # pale yellow
Q_PAPER3 = canopy(14, 1220, 1330) # pale pink
CORK = c0(35, 0.86, 0.92)

# ---- the barn's name board (barn-local) ----
NS_W, NS_H = 2.7, 0.72            # board (inside the frame)
NS_C = (0.0, 2.96)                # board centre (x, z)
NS_Y = -HD - 0.62                 # board centre depth (in front of the door trim)
NS_ARM_Z = 3.58                   # iron arms from the wall above the trim
NS_HOOK_X = 1.0


def round_rect(cx, cz, w, h, r, n=4):
    """Rounded rectangle outline (x, z), n segments per corner: even count, star-shaped."""
    pts = []
    for (sx, sz, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oz = cx + sx * (w / 2 - r), cz + sz * (h / 2 - r)
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((ox + r * math.cos(a), oz + r * math.sin(a)))
    return pts


def name_sign(bm, cx, cz, y, w, h, flowers=True):
    """Frame + board + plank seams + nails + heart on top + flowers at the bottom corners, facing -Y."""
    slab(bm, round_rect(cx, cz, w + 0.14, h + 0.14, 0.12), DARKWOOD, 0.08, 0.0, 0.7, center=(cx, cz), at=(0, y + 0.01, 0))
    slab(bm, round_rect(cx, cz, w, h, 0.07), WOOD, 0.05, 0.012, 0.8, center=(cx, cz), at=(0, y - 0.045, 0))
    for k in (-1, 1):   # two plank seams across the board (just proud of its front)
        box(bm, (cx, y - 0.093, cz + k * h / 6), (w - 0.14, 0.012, 0.022), RUSTIC)
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(bm, (cx + sx * (w / 2 - 0.07), y - 0.086, cz + sz * (h / 2 - 0.07)), (0.04, 0.02, 0.04), IRON)
    heart(bm, (cx, y - 0.055, cz + h / 2 + 0.08), 0.3, XRED, 0.06)
    if flowers:
        for sx in (-1, 1):
            bx = cx + sx * (w / 2 + 0.02)
            for k in range(3):
                leaf(bm, (bx, y - 0.07, cz - h / 2 + 0.04), -90 + sx * (35 + k * 28), 0.2, 0.07, 50, LEAF, droop=-0.1)
            flat_flower(bm, (bx, y - 0.11, cz - h / 2 + 0.06), 0.085, SNOWW)
            flat_flower(bm, (bx - sx * 0.14, y - 0.1, cz - h / 2 - 0.02), 0.06, Q_PAPER3)


def barn_name_sign(bm):
    cx, cz = NS_C
    name_sign(bm, cx, cz, NS_Y, NS_W, NS_H)
    top = cz + NS_H / 2 + 0.07
    for sx in (-1, 1):
        x = sx * NS_HOOK_X
        # iron arm from the wall (behind the trim band) out over the board, a curl under it, a ring
        beam(bm, (x, -FACE + 0.02, NS_ARM_Z), (x, NS_Y - 0.08, NS_ARM_Z), 0.05, 0.05, IRON)
        box(bm, (x, -FACE - 0.02, NS_ARM_Z - 0.04), (0.12, 0.04, 0.22), IRON)
        curl = [(x, -FACE - 0.05 - 0.22 * (1 - math.cos(math.pi * t / 8)), NS_ARM_Z - 0.03 - 0.18 * math.sin(math.pi * t / 8)) for t in range(9)]
        tube(bm, curl, [0.016] * len(curl), IRON, 6)
        # two links of chain down to the frame
        for k, z in enumerate((NS_ARM_Z - 0.09, top + 0.07)):
            ring = [(x + 0.035 * math.cos(2 * math.pi * i / 10) * (k % 2 == 0), NS_Y + 0.035 * math.cos(2 * math.pi * i / 10) * (k % 2 == 1),
                     z + 0.05 * math.sin(2 * math.pi * i / 10)) for i in range(11)]
            tube(bm, ring, [0.009] * len(ring), IRON, 5)
        tube(bm, [(x, NS_Y, NS_ARM_Z - 0.03), (x, NS_Y, top + 0.12)], [0.008, 0.008], IRON, 5)
        tube(bm, [(x, NS_Y, top + 0.02), (x, NS_Y, top - 0.06)], [0.012, 0.012], IRON, 6)


# ---- Walter's quest booth ----
B_W, B_D = 2.5, 1.15              # posts' outer footprint
B_FRONT_H, B_BACK_H = 2.35, 2.6
C_H, C_D = 0.95, 0.5              # counter height / depth
POST = 0.11
BOOTH_MARK = False


def notice(bm, x, z, w, h, col, rot, y, seed):
    """A paper note pinned to the board (thin box, a red pin), slightly turned."""
    box(bm, (x, y, z), (w, 0.012, h), col, pitch=rot)
    rnd = random.Random(seed)
    for k in range(2):   # two 'lines' of writing
        box(bm, (x + rnd.uniform(-0.01, 0.01), y - 0.008, z + h * (0.12 - 0.22 * k)), (w * 0.62, 0.006, 0.018), IRON, pitch=rot)
    ball2(bm, (x - math.sin(math.radians(rot)) * h * 0.38, y - 0.02, z + h * 0.4), 0.022, XRED, (1, 1, 1), 1, 0.0, seed)


def quest_booth(bm):
    hx, hy = B_W / 2 - POST / 2, B_D / 2 - POST / 2
    # base boards
    box(bm, (0, 0, 0.04), (B_W + 0.1, B_D + 0.1, 0.08), DARKWOOD)
    # posts (front lower than back: the awning slopes down to the front)
    for sx in (-1, 1):
        box(bm, (sx * hx, -hy, (0.08 + B_FRONT_H) / 2), (POST, POST, B_FRONT_H - 0.08), WOOD)
        box(bm, (sx * hx, hy, (0.08 + B_BACK_H) / 2), (POST, POST, B_BACK_H - 0.08), WOOD)
    # counter across the front, between the front posts: plank front, light top
    cy = -hy + C_D / 2 - POST / 2
    cw = 2 * hx - POST
    box(bm, (0, cy, (0.08 + C_H - 0.06) / 2), (cw, C_D - 0.04, C_H - 0.06 - 0.08), WOOD)
    box(bm, (0, cy - 0.01, C_H - 0.03), (cw + 0.16, C_D + 0.06, 0.06), LIGHT_WOOD)
    n = 7
    for i in range(n):   # plank seams on the counter front
        x = -cw / 2 + cw * (i + 0.5) / n
        box(bm, (x, cy - (C_D - 0.04) / 2 - 0.01, (0.08 + C_H - 0.06) / 2), (cw / n - 0.03, 0.02, C_H - 0.06 - 0.1), LIGHT_WOOD if i % 2 else WOOD)
    box(bm, (0, cy - (C_D - 0.04) / 2 - 0.03, C_H - 0.2), (cw - 0.02, 0.03, 0.07), Q_GREEN)   # green trim strip
    # counter top: a stack of scrolls, an ink pot with a quill, a little bell
    top = C_H
    for k, (x, col) in enumerate(((-0.75, Q_PAPER), (-0.6, Q_PAPER2), (-0.68, Q_PAPER))):
        tube(bm, [(x - 0.12, cy + 0.02 * k, top + 0.04 + 0.07 * (k // 2)), (x + 0.12, cy + 0.02 * k - 0.02, top + 0.04 + 0.07 * (k // 2))], [0.035, 0.035], col, 8)
    revolve(bm, [(0.05, top), (0.06, top + 0.02), (0.06, top + 0.08), (0.035, top + 0.1), (0.03, top + 0.12)], IRON, (0.7, cy, 0), 10)
    leaf(bm, (0.71, cy, top + 0.1), 0, 0.28, 0.06, 70, SNOWW, droop=-0.05)
    revolve(bm, [(0.08, top), (0.075, top + 0.03), (0.055, top + 0.08), (0.02, top + 0.12)], GOLD, (0.2, cy + 0.05, 0), 10)
    ball2(bm, (0.2, cy + 0.05, top + 0.135), 0.022, GOLD, (1, 1, 1), 1, 0.0, 77)
    # back: the notice board between the back posts, full of quest notes
    by = hy - 0.02
    bw = 2 * hx - POST
    box(bm, (0, by, 1.62), (bw, 0.05, 1.12), CORK)
    for z in (1.04, 2.2):
        box(bm, (0, by - 0.005, z), (bw + 0.02, 0.07, 0.07), DARKWOOD)
    box(bm, (0, by, 0.56), (bw, 0.04, 0.9), RUSTIC)   # plank back wall under the board
    rnd = random.Random(42)
    cols = (Q_PAPER, Q_PAPER2, Q_PAPER3, Q_PAPER, Q_PAPER2, Q_PAPER, Q_PAPER3, Q_PAPER2)
    for i, (x, z) in enumerate(((-0.82, 1.78), (-0.45, 1.52), (-0.12, 1.85), (0.2, 1.48), (0.52, 1.8), (0.85, 1.5), (-0.8, 1.32), (0.55, 1.28))):
        notice(bm, x, z, rnd.uniform(0.22, 0.28), rnd.uniform(0.26, 0.32), cols[i], rnd.uniform(-9, 9), by - 0.032 - 0.004 * (i % 3), 300 + i)
    # side rails (thin: a top rail and a low rail on each side)
    for sx in (-1, 1):
        for z in (0.5, C_H - 0.05):
            box(bm, (sx * hx, 0, z), (POST * 0.7, 2 * hy - POST, 0.07), LIGHT_WOOD)
    # awning: sloped stripes green / cream from the back posts' tops over the front with scallops
    n = 8
    x0, x1 = -B_W / 2 - 0.18, B_W / 2 + 0.18
    zt, zb, d0, d1 = B_BACK_H + 0.03, B_FRONT_H - 0.02, hy + 0.12, -hy - 0.45
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n
        xb = x0 + (x1 - x0) * (i + 1) / n
        col = Q_GREEN if i % 2 == 0 else SNOW
        beam(bm, ((xa + xb) / 2, d0, zt + 0.004 * (i % 2)), ((xa + xb) / 2, d1, zb + 0.004 * (i % 2)), (xb - xa) - 0.004, 0.05, col)
        slab(bm, ellipse_pts((xb - xa) / 2 - 0.01, 0.11, 12, ((xa + xb) / 2, zb - 0.06)), col, 0.035, 0.01, at=(0, d1 - 0.02 - 0.006 * (i % 2), 0))
    # title board standing on the awning's front edge: arched sign (sign_outline) + gold "!"
    tz = zb + 0.52
    ty = d1 + 0.12
    for sx in (-1, 1):
        box(bm, (sx * 0.7, ty + 0.06, (zb + tz) / 2), (0.07, 0.07, tz - zb), DARKWOOD)
    slab(bm, sign_outline(0.0, tz, 2.2, 0.62, 0.07), DARKWOOD, 0.06, 0.0, 0.7, center=(0.0, tz + 0.05), at=(0, ty, 0))
    slab(bm, sign_outline(0.0, tz, 2.2, 0.62), WOOD, 0.05, 0.012, 0.7, center=(0.0, tz + 0.05), at=(0, ty - 0.05, 0))
    if BOOTH_MARK:   # off since 2026-11-04: the big floating SM_QuestMark_* shows the state in game
        ex, ez = 0.0, tz + 0.62 / 2 + 0.36
        slab(bm, round_rect(ex, ez + 0.06, 0.11, 0.3, 0.05), GOLD, 0.06, 0.015, 0.7, center=(ex, ez + 0.06), at=(0, ty - 0.08, 0))
        slab(bm, ellipse_pts(0.06, 0.06, 12, (ex, ez - 0.17)), GOLD, 0.06, 0.015, at=(0, ty - 0.08, 0))
    for sx in (-1, 1):   # leaves + flowers on the board's shoulders
        for k in range(3):
            leaf(bm, (sx * 0.95, ty - 0.1, tz - 0.22), -90 + sx * (40 + k * 25), 0.18, 0.06, 50, LEAF, droop=-0.1)
        flat_flower(bm, (sx * 1.0, ty - 0.13, tz - 0.2), 0.08, SNOWW)
    # a lantern hanging from the front-left corner, a crate of scrolls beside the counter
    tube(bm, [(-hx, -hy - 0.12, B_FRONT_H - 0.2), (-hx, -hy - 0.12, B_FRONT_H - 0.42)], [0.01, 0.01], IRON, 6)
    beam(bm, (-hx, -hy + 0.04, B_FRONT_H - 0.2), (-hx, -hy - 0.16, B_FRONT_H - 0.2), 0.035, 0.035, IRON)
    lantern(bm, (-hx, -hy - 0.12, B_FRONT_H - 0.42), 0.45)
    box(bm, (hx + 0.42, -hy + 0.1, 0.2), (0.48, 0.42, 0.4), WOOD)
    for sx in (-1, 1):
        box(bm, (hx + 0.42 + sx * 0.225, -hy + 0.1, 0.2), (0.06, 0.44, 0.42), LIGHT_WOOD)
    for k in range(3):
        tube(bm, [(hx + 0.28 + 0.13 * k, -hy - 0.02, 0.44), (hx + 0.3 + 0.13 * k, -hy + 0.22, 0.47)], [0.04, 0.04], (Q_PAPER, Q_PAPER2, Q_PAPER3)[k], 8)


# ---- the floating quest marks (spin + bob in game over the booth), pivot bottom centre ----
def quest_exclaim(bm):
    """Chunky round gold "!": a tapered capsule over a ball."""
    prof = [(0.0, 0.36), (0.05, 0.37), (0.08, 0.42), (0.13, 0.75), (0.16, 1.0), (0.155, 1.06), (0.12, 1.11), (0.06, 1.14), (0.0, 1.15)]
    revolve(bm, prof, GOLD, (0, 0, 0), 16)
    ball2(bm, (0, 0, 0.14), 0.13, GOLD, (1, 1, 1), 2, 0.0, 501)


def quest_question(bm):
    """Chunky round gold "?": a thick tube hook + a stem, over a ball."""
    cx, cz, r = 0.0, 0.84, 0.25
    pts = [(cx + r * math.cos(math.radians(a)), 0.0, cz + r * math.sin(math.radians(a))) for a in range(165, -60, -15)]
    pts += [(0.06, 0.0, 0.58), (0.02, 0.0, 0.5), (0.0, 0.0, 0.42)]
    tube(bm, pts, [0.085] * len(pts), GOLD, 12)
    ball2(bm, (pts[0][0], 0.0, pts[0][2]), 0.085, GOLD, (1, 1, 1), 2, 0.0, 502)
    ball2(bm, (0.0, 0.0, 0.42), 0.085, GOLD, (1, 1, 1), 2, 0.0, 503)
    ball2(bm, (0, 0, 0.14), 0.12, GOLD, (1, 1, 1), 2, 0.0, 504)


def build_quest_marks():
    coll = bpy.data.collections["QuestBooth"]
    made = [_finish("SM_QuestMark_Exclaim", quest_exclaim, (14, -350, 0), coll),
            _finish("SM_QuestMark_Question", quest_question, (16, -350, 0), coll)]
    for o in made:
        for p in o.data.polygons:
            p.use_smooth = True
    return {"closed": check_closed(made), "dims": {o.name: [round(d, 2) for d in o.dimensions] for o in made},
            "faces": {o.name: len(o.data.polygons) for o in made}}


def _finish(name, fn, loc, coll):
    bm = bmesh.new()
    fn(bm)
    part = _islands(bm)
    sizes = {}
    for f in bm.faces:
        sizes[part[f.index]] = sizes.get(part[f.index], 0) + 1
    flags = [sizes[part[f.index]] > 6 for f in bm.faces]
    o = finish_lamp(bm, name, coll, loc)
    for p, sm in zip(o.data.polygons, flags):
        p.use_smooth = sm
    return o


def build_quest_props():
    coll = bpy.data.collections.get("QuestBooth")
    if coll is None:
        coll = bpy.data.collections.new("QuestBooth")
        bpy.context.scene.collection.children.link(coll)
    made = [_finish("SM_BarnNameSign", barn_name_sign, (0, -350, 0), coll),
            _finish("SM_QuestBooth", quest_booth, (10, -350, 0), coll)]
    return {"closed": check_closed(made), "zfight": {o.name: zfight(o) for o in made},
            "dims": {o.name: [round(d, 2) for d in o.dimensions] for o in made},
            "faces": {o.name: len(o.data.polygons) for o in made}}
