# Season symbols (spring flower, summer sun, autumn maple leaf, winter snowflake) in the NewLua
# pack's gradient-atlas style, chunky + faceted like Dante's icon sheet: flat shading, quads only,
# closed shells, front faces -Y, pivot at the symbol's centre.
#   exec(open(r"<skills>/blender-game-props/seasons.py").read())
#   build_seasons()
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

exec(open(_skill("blender-game-props/daily_trees.py")).read())   # atlas + tree helpers

# Season colours: canopy-band columns 30-35 (the daily trees use 0-29)
SEASON_STRIPS = {30: ("#E85A86", "#FFC4D4"),   # petal pink
                 31: ("#1E7A1A", "#7AD84A"),   # leaf green
                 32: ("#FFB000", "#FFF06A"),   # sun yellow
                 33: ("#C8240E", "#FF9A2E"),   # maple red -> orange
                 34: ("#4A2008", "#9A5A2E"),   # stem brown
                 35: ("#5A9AE8", "#E4F6FF")}   # ice blue
PINK, GREEN, SUN, MAPLE, STEM, ICE = (strip_uv(CANOPY_BAND, k) for k in range(30, 36))


def add_season_strips():
    img = [i for i in bpy.data.images if i.name.startswith("GradientTexture")][0]
    W, H = img.size
    px = np.empty(W * H * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    orig = px.copy()
    px = px.reshape(H, W, 4)
    touched = np.zeros((H, W), bool)
    y0, y1 = CANOPY_BAND
    for k, spec in SEASON_STRIPS.items():
        x0, x1 = int(k * CW * W) + 3, int((k + 1) * CW * W) - 3
        stops = _stops(spec)
        for y in range(y0, y1):
            t = (y - y0) / (y1 - y0 - 1)
            px[y, x0:x1, :3] = stops[0] + (stops[1] - stops[0]) * t
            px[y, x0:x1, 3] = 1.0
        touched[y0:y1, x0:x1] = True
    flat = px.ravel()
    changed = (np.abs(flat - orig) > 1e-7).reshape(H, W, 4).any(axis=2)
    img.pixels.foreach_set(flat)
    img.update()
    img.pack()
    return int((changed & ~touched).sum())


def slab(bm, outline, col, thick=0.1, bulge=0.06, inner=0.5, center=None, at=(0, 0, 0), rot=0.0, depth=0.0):
    """Faceted chunky 2D shape: outline (x, z) points (even count, star-shaped around `center`)
    extruded along Y, front and back domed toward the centre (outline ring -> inner ring -> quad
    fan to a centre point), all quads and closed. rot turns it in its plane (degrees), depth moves
    it back (+Y)."""
    n = len(outline)
    assert n % 2 == 0
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
        b.faces.new((fr[i], fr[j], br[j], br[i]))          # rim
        b.faces.new((fr[i], fi[i], fi[j], fr[j]))          # front bevel ring
        b.faces.new((br[j], bi[j], bi[i], br[i]))          # back bevel ring
    for i in range(0, n, 2):                               # quad fans to the centres
        b.faces.new((fm, fi[(i + 2) % n], fi[i + 1], fi[i]))
        b.faces.new((bmid, bi[i], bi[i + 1], bi[(i + 2) % n]))
    uv_part(b, col)
    bmesh.ops.rotate(b, cent=Vector(), matrix=Matrix.Rotation(math.radians(rot), 3, 'Y'), verts=b.verts)
    bmesh.ops.translate(b, vec=Vector(at) + Vector((0, depth, 0)), verts=b.verts)
    merge(bm, b)


def ellipse(rx, rz, n=12, z0=0.0, pinch=0.0):
    """Even-count oval outline; pinch narrows the bottom (petal / leaf base)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        x, z = rx * math.cos(a), rz * math.sin(a)
        if z < 0:
            x *= 1 - pinch * (-z / rz)
        pts.append((x, z + z0))
    return pts


def spring(bm):
    for rot in (62, 118):   # two leaves behind the flower, peeking out on the right
        leaf_pts = ellipse(0.17, 0.3, 12, 0.42, 0.6)
        slab(bm, leaf_pts, GREEN, 0.07, 0.05, 0.45, center=(0, 0.42), at=(0, 0.07, 0), rot=rot)
    for k in range(5):   # petals
        pet = ellipse(0.22, 0.27, 12, 0.3, 0.55)
        slab(bm, pet, PINK, 0.09, 0.07, 0.45, center=(0, 0.3), rot=k * 72 + 36)
    b = quad_sphere(0.11, 1, (1, 0.7, 1), 0, 1)   # yellow centre
    bmesh.ops.translate(b, vec=Vector((0, -0.11, 0)), verts=b.verts)
    uv_part(b, SUN)
    merge(bm, b)
    for k in range(7):   # stamens
        a = 2 * math.pi * k / 7
        tip = Vector((0.17 * math.cos(a), -0.15, 0.17 * math.sin(a)))
        tube(bm, [(0, -0.12, 0), tip], [0.015, 0.012], SUN, 6)
        b = quad_sphere(0.032, 1, (1, 1, 1), 0, k)
        bmesh.ops.translate(b, vec=tip, verts=b.verts)
        uv_part(b, SUN)
        merge(bm, b)


def summer(bm):
    disc = [(0.4 * math.cos(2 * math.pi * i / 16), 0.4 * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    slab(bm, disc, SUN, 0.14, 0.1, 0.55, center=(0, 0))
    for k in range(8):   # rays: little faceted triangles
        ray = [(-0.13, 0.48), (0.0, 0.47), (0.13, 0.48), (0.07, 0.62), (0.0, 0.76), (-0.07, 0.62)]
        slab(bm, ray, SUN, 0.1, 0.05, 0.4, center=(0, 0.58), rot=k * 45)


def autumn(bm):
    leaf_pts = [(0, 1.05), (0.1, 0.86), (0.22, 0.9), (0.2, 0.7), (0.42, 0.82), (0.4, 0.62), (0.58, 0.6), (0.5, 0.46), (0.66, 0.36),
                (0.44, 0.3), (0.4, 0.14), (0.16, 0.18), (0.05, 0.04), (0.0, 0.02), (-0.05, 0.04), (-0.16, 0.18), (-0.4, 0.14),
                (-0.44, 0.3), (-0.66, 0.36), (-0.5, 0.46), (-0.58, 0.6), (-0.4, 0.62), (-0.42, 0.82), (-0.2, 0.7), (-0.22, 0.9), (-0.1, 0.86)]
    s = 1.05
    pts = [(x * s, (z - 0.5) * s) for x, z in leaf_pts]
    slab(bm, pts, MAPLE, 0.1, 0.08, 0.35, center=(0, 0))
    tube(bm, curve_pts((0, 0, -0.48), (0.02, 0, -0.64), (0.15, 0, -0.8), 5), [0.04, 0.036, 0.032, 0.028, 0.024], STEM, 6)


def winter(bm):
    hexa = [(0.17 * math.cos(math.pi / 6 + 2 * math.pi * i / 6), 0.17 * math.sin(math.pi / 6 + 2 * math.pi * i / 6)) for i in range(6)]
    slab(bm, hexa, ICE, 0.14, 0.09, 0.5, center=(0, 0))
    w, L, t = 0.075, 0.6, 0.12
    arm = [(-w, 0.08), (w, 0.08), (w, L), (w * 0.4, L + t), (-w * 0.4, L + t), (-w, L)]
    br_ = [(-0.045, 0.0), (0.045, 0.0), (0.045, 0.2), (0.0, 0.26), (-0.045, 0.2), (-0.045, 0.1)]
    for k in range(6):
        rot = k * 60
        slab(bm, arm, ICE, 0.1, 0.05, 0.4, center=(0, (0.08 + L) / 2), rot=rot)
        for sgn in (-1, 1):   # side branches, pointing up and out along the arm
            pts = [(x, z) for x, z in br_]
            b_rot = rot + sgn * 48
            base = Matrix.Rotation(math.radians(rot), 3, 'Y') @ Vector((0, 0, 0.36))
            slab(bm, pts, ICE, 0.08, 0.04, 0.4, center=(0, 0.12), at=(base.x, 0, base.z), rot=b_rot)
    for k in range(6):   # little floating crystals between the arms
        a = math.radians(30 + 60 * k)
        dia = [(0.0, -0.11), (0.08, 0.0), (0.0, 0.11), (-0.08, 0.0)]
        slab(bm, dia, ICE, 0.08, 0.04, 0.4, center=(0, 0), at=(0.74 * math.cos(a), 0, 0.74 * math.sin(a)), rot=-math.degrees(a) + 90)


SEASONS = [("Spring", spring), ("Summer", summer), ("Autumn", autumn), ("Winter", winter)]


def build_seasons():
    outside = add_season_strips()
    atlas = bpy.data.materials["M_GradientTexture"]
    coll = bpy.data.collections.get("Seasons") or bpy.data.collections.new("Seasons")
    if coll.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(coll)
    objs = []
    for i, (name, fn) in enumerate(SEASONS):
        nm = "SM_Season_" + name
        o = bpy.data.objects.get(nm)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
        bm = bmesh.new()
        fn(bm)
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(atlas)
        for p in me.polygons:
            p.use_smooth = False   # faceted, like the icon sheet
        o = bpy.data.objects.new(nm, me)
        coll.objects.link(o)
        o.location = (i * 2.0, -200, 1.0)
        objs.append(o)
    rep = check_closed(objs)
    rep["_atlas_pixels_changed_outside"] = outside
    return rep
