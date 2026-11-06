# Wooden chair (gab, the market villager's seat) matching tables.py: a plank seat, tapered legs on
# feet, an apron and low stretchers, and a back of two posts, a top rail and three slats.
# Sized for a villager (~0.7 m wide plush body): wide seat, low. Pivot at the bottom centre,
# width along X, front -Y (the back is at +Y). check_closed + zfight must be 0.
#   exec(open(r"<skills>/blender-game-props/chairs.py").read())
#   build_chairs()
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

exec(open(_skill("blender-game-props/tables.py")).read())

# name: (width, depth, seat height, back height above the seat, seat planks, leg width)
CHAIRS = {
    "Market": (0.82, 0.72, 0.42, 0.62, 4, 0.08),
}


def g_chair(bm, W, D, H, BH, n, lw, seed):
    rnd = random.Random(seed)
    under = H - TOP_T
    # seat planks run across (along X), side by side front to back
    pd = (D - GAP * (n - 1)) / n
    for k in range(n):
        y = -D / 2 + pd / 2 + k * (pd + GAP)
        h = TOP_T + 0.004 * (k % 2)
        box(bm, (rnd.uniform(-0.008, 0.008), y, under + h / 2), (W - rnd.uniform(0, 0.02), pd, h), T_WOOD_LIGHT if k % 2 else T_WOOD)
    lx, ly = W / 2 - 0.04 - lw / 2, D / 2 - 0.04 - lw / 2
    for sx in (-1, 1):
        # front legs end under the seat; the back legs go on up as the back posts
        box(bm, (sx * lx, -ly, 0.02 + (under + 0.02) / 2), (lw * 0.82, lw * 0.82, under + 0.02), T_WOOD_DARK, taper=1.2)
        box(bm, (sx * lx, -ly, 0.03), (lw * 1.15, lw * 1.15, 0.06), T_WOOD, taper=0.85)
        top = H + BH
        box(bm, (sx * lx, ly, 0.02 + (top - 0.02) / 2), (lw * 0.82, lw * 0.82, top - 0.02), T_WOOD_DARK, taper=1.08)
        box(bm, (sx * lx, ly, 0.03), (lw * 1.15, lw * 1.15, 0.06), T_WOOD, taper=0.85)
        # rounded-ish post caps
        box(bm, (sx * lx, ly, top + 0.025), (lw * 1.05, lw * 1.05, 0.05), T_WOOD_LIGHT, taper=0.7)
    # apron under the seat
    ah, at = 0.08, 0.03
    for sy in (-1, 1):
        box(bm, (0.0, sy * (ly - lw * 0.1), under - ah / 2 + 0.006), (2 * lx - lw * 0.8, at, ah), T_WOOD)
    for sx in (-1, 1):
        box(bm, (sx * (lx - lw * 0.1), 0.0, under - (ah - 0.02) / 2), (at, 2 * ly - lw * 0.8, ah - 0.02), T_WOOD)
    # stretchers low between the legs (side ones, and one across at the front)
    sz = 0.13
    for sx in (-1, 1):
        box(bm, (sx * lx, 0.0, sz), (lw * 0.45, 2 * ly - lw * 0.8, lw * 0.45), T_WOOD)
    box(bm, (0.0, -ly, sz + 0.05), (2 * lx - lw * 0.8, lw * 0.42, lw * 0.42), T_WOOD_LIGHT)
    # back: a wide top rail, a lower rail and three slats between them (between the posts)
    inner = 2 * lx - lw * 0.82
    rail_z = H + BH - 0.09
    box(bm, (0.0, ly, rail_z), (inner, 0.05, 0.14), T_WOOD)
    box(bm, (0.0, ly, H + 0.12), (inner, 0.04, 0.05), T_WOOD)
    s_lo, s_hi = H + 0.12 + 0.025, rail_z - 0.07
    for k in (-1, 0, 1):
        box(bm, (k * inner * 0.28, ly, (s_lo + s_hi) / 2), (0.07, 0.03, s_hi - s_lo), T_WOOD_LIGHT if k else T_WOOD)


def build_chairs(only=None):
    root = bpy.data.collections.get("Chairs") or bpy.data.collections.new("Chairs")
    if root.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    out = {}
    for i, (name, (W, D, H, BH, n, lw)) in enumerate(CHAIRS.items()):
        if only and name not in only:
            continue
        old = bpy.data.objects.get("SM_Chair_" + name)
        if old:
            bpy.data.objects.remove(old)
        bm = bmesh.new()
        g_chair(bm, W, D, H, BH, n, lw, 700 + i)
        o = finish_lamp(bm, "SM_Chair_" + name, root, (i * 3.0, -262.0, 0))
        out[o.name] = (check_closed([o])[o.name], zfight(o)[:6], [round(d, 2) for d in o.dimensions], len(o.data.polygons))
    return out
