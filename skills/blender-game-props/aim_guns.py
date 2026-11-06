# Aim-trainer weapon set (Dante's card sheet): Revolver, Burst, SMG, Carbine, Shotgun, Rifle and the
# Blaster in 4 rarities. ONE material + ONE palette atlas (T_Weapons.png, 8x8 cells of 64 px, each
# cell a top-light -> bottom-dark gradient; alpha 0 = glow cell). All quads, built quad-first:
#   loft(sections)  chamfered octagon rings lofted along 2D side-view sections (boxes, grips, stocks)
#   bar(path)       the same along a bent path (trigger guards, levers)
#   lathe(profile)  revolved profile with grid caps (barrels, muzzles, scopes, cylinders)
# Side view in cm: X = muzzle direction, Z = up, Y = thickness. Each gun is turned to face -Y,
# scaled to metres and its origin put on the grip at the end.
#   exec(open(r"<skills>/blender-game-props/aim_guns.py").read())
#   build_guns(out_dir)   -> {object name: topo summary}
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

import bpy, bmesh, math
from mathutils import Vector, Matrix

_CT = _skill("blender-clean-topology")
for _f in ("quad_build.py", "topo_check.py", "topo_clean.py"):
    exec(open(_CT + "/" + _f).read())
exec(open(_skill("blender-game-props/zfight_check.py")).read())

# palette: key -> (cell index, top colour, bottom colour, glow)
PAL = {
    "W":  (0, "#F4F6FA", "#C3CAD6", False),   # blaster white
    "LG": (1, "#C8CED8", "#8E96A4", False),   # light grey metal
    "ST": (2, "#A9B2C0", "#5F6878", False),   # steel
    "DG": (3, "#4A5163", "#2A2F3B", False),   # gunmetal
    "BK": (4, "#30343F", "#16181E", False),   # near black
    "OR": (5, "#FFA43A", "#E06A10", False),   # orange
    "GL": (6, "#B8F2FF", "#1E8BFF", True),    # blue glow
    "GC": (7, "#F2FDFF", "#58D8FF", True),    # bright cyan glow (lenses)
    "WD": (8, "#B06A3A", "#7A4220", False),   # wood
    "DW": (9, "#6E3B1E", "#45230F", False),   # dark wood
    "TN": (10, "#D9B98A", "#A5835A", False),  # tan polymer
    "RD": (11, "#FF5A4A", "#C21E1E", False),  # red
    "YL": (12, "#FFE070", "#E8A80E", False),  # gold
    "DY": (13, "#D08A1A", "#8C5408", False),  # dark gold
    "BL": (14, "#5AA0FF", "#2350C8", False),  # blue paint
    "PU": (15, "#C07CFF", "#7A2FD0", False),  # purple
    "RG": (16, "#FFC2B8", "#FF3B30", True),   # red glow
}
CELL, GRID, TEX = 64, 8, 512
_COLS = list(PAL)


def make_atlas(path):
    """Writes the palette atlas PNG (RGBA, alpha 0 marks glow cells for the emission mask)."""
    old = bpy.data.images.get("T_Weapons")
    if old:
        bpy.data.images.remove(old)   # a file-backed image ignores new pixels on save: start fresh
    img = bpy.data.images.new("T_Weapons", TEX, TEX, alpha=True)
    px = [0.0] * (TEX * TEX * 4)
    def lin(h):
        return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]   # byte images store sRGB values
    for key, (idx, top, bot, glow) in PAL.items():
        cx, cy = idx % GRID, idx // GRID          # cy counts from the image top
        a, b = lin(top), lin(bot)
        for yy in range(CELL):
            t = yy / (CELL - 1)                    # 0 at cell top
            col = [a[i] + (b[i] - a[i]) * t for i in range(3)]
            row = TEX - 1 - (cy * CELL + yy)       # Blender pixel rows start at the bottom
            for xx in range(CELL):
                o = (row * TEX + cx * CELL + xx) * 4
                px[o:o + 4] = col + [0.0 if glow else 1.0]
    img.pixels.foreach_set(px)
    img.alpha_mode = "STRAIGHT"
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img


def make_material(img):
    m = bpy.data.materials.get("M_Weapons") or bpy.data.materials.new("M_Weapons")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 4.0
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    nt.links.new(tex.outputs["Alpha"], inv.inputs[1])
    nt.links.new(inv.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], bsdf.inputs["Emission Strength"])
    bsdf.inputs["Roughness"].default_value = 0.55
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m


def cell_uv(key, t):
    idx = PAL[key][0]
    cx, cy = idx % GRID, idx // GRID
    u = (cx * CELL + CELL / 2) / TEX
    y = cy * CELL + 6 + (CELL - 12) * min(max(t, 0.0), 1.0)   # 6 px margin against mip bleed
    return (u, 1 - y / TEX)


# ---------- part building: every part is a small bmesh with a per-face colour layer

class Gun:
    def __init__(self, cmap=None):
        self.bm = bmesh.new()
        self.cmap = cmap or {}

    def _new(self):
        b = bmesh.new()
        b.faces.layers.int.new("col")
        return b

    def _add(self, b, colfaces):
        """colfaces: list of (face, key). UV = colour cell, gradient t from the part's own height."""
        cl = b.faces.layers.int["col"]
        for f, k in colfaces:
            f[cl] = _COLS.index(self.cmap.get(k, k))
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        zs = [v.co.z for v in b.verts]
        z0, z1 = min(zs), max(zs)
        h = max(z1 - z0, 1e-6)
        ul = b.loops.layers.uv.new("UVMap")
        for f in b.faces:
            key = _COLS[f[cl]]
            for l in f.loops:
                l[ul].uv = cell_uv(key, (z1 - l.vert.co.z) / h)
        me = bpy.data.meshes.new("_tmp")
        b.to_mesh(me)
        b.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    @staticmethod
    def _oct(b, A, B, w, c, y):
        """8-vert chamfered ring across the side-view line A->B, thickness 2w along Y."""
        A, B = Vector((A[0], 0, A[1])), Vector((B[0], 0, B[1]))
        d = B - A
        L = d.length
        d.normalize()
        c = min(c, L * 0.3, w * 0.6)
        Y = Vector((0, 1, 0))
        pts = [(0, -w + c), (0, w - c), (c, w), (L - c, w), (L, w - c), (L, -w + c), (L - c, -w), (c, -w)]
        return [b.verts.new(A + d * s + Y * (yy + y)) for s, yy in pts]

    def loft(self, secs, w, key, cham=0.35, y=0.0, wscale=None):
        """secs: [((ax, az), (bx, bz)), ...] side-view lines; consecutive lines are lofted."""
        b = self._new()
        rings = [self._oct(b, A, B, w * (wscale[i] if wscale else 1), cham, y) for i, (A, B) in enumerate(secs)]
        faces = []
        for r0, r1 in zip(rings, rings[1:]):
            for k in range(8):
                j = (k + 1) % 8
                faces.append(b.faces.new((r0[k], r0[j], r1[j], r1[k])))
        faces += grid_cap(b, rings[0]) + grid_cap(b, rings[-1])
        self._add(b, [(f, key) for f in faces])

    def box(self, x0, x1, z0, z1, w, key, cham=0.35, y=0.0):
        self.loft([((x0, z0), (x0, z1)), ((x1, z0), (x1, z1))], w, key, cham, y)

    def bar(self, path, width, w, key, cham=0.25):
        """Loft along a bent 2D path: each section is perpendicular to the path."""
        P = [Vector(p) for p in path]
        secs = []
        for i, p in enumerate(P):
            t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
            n = Vector((-t.y, t.x)) * (width / 2)
            secs.append(((p - n).to_tuple(), (p + n).to_tuple()))
        self.loft(secs, w, key, cham)

    def lathe(self, prof, axis="x", c=(0, 0, 0), sides=16, cap0=None, cap1=None):
        """prof: [(pos, r, key), ...] along the axis; key = colour of the band ending at that point
        (first key colours the start cap). Grid caps on both ends, all quads."""
        b = self._new()
        C = Vector(c)
        if axis == "x":
            A, U, V = Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0))
        elif axis == "z":
            A, U, V = Vector((0, 0, 1)), Vector((1, 0, 0)), Vector((0, 1, 0))
        else:
            A, U, V = Vector((0, 1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))
        rings = []
        for pos, r, _ in prof:
            rings.append([b.verts.new(C + A * pos + (U * math.cos(2 * math.pi * k / sides) +
                                                    V * math.sin(2 * math.pi * k / sides)) * r)
                          for k in range(sides)])
        cf = []
        for i in range(len(rings) - 1):
            key = prof[i + 1][2]
            for k in range(sides):
                j = (k + 1) % sides
                cf.append((b.faces.new((rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k])), key))
        cf += [(f, cap0 or prof[0][2]) for f in grid_cap(b, rings[0])]
        cf += [(f, cap1 or prof[-1][2]) for f in grid_cap(b, rings[-1])]
        self._add(b, cf)

    def finish(self, name, grip, coll, mat, offset):
        """Turn to face -Y, cm -> m, origin on the grip, sharp edges by angle, one material."""
        b = self.bm
        bmesh.ops.remove_doubles(b, verts=b.verts, dist=0.0005)
        T = Matrix.Translation(Vector(offset)) @ Matrix.Rotation(-math.pi / 2, 4, "Z") @ \
            Matrix.Scale(0.01, 4) @ Matrix.Translation(-Vector((grip[0], 0, grip[1])))
        bmesh.ops.transform(b, matrix=T, verts=b.verts)
        orient_outward(b)
        for f in b.faces:
            f.smooth = True
        me = bpy.data.meshes.get(name)
        if me:
            bpy.data.meshes.remove(me)
        me = bpy.data.meshes.new(name)
        b.to_mesh(me)
        b.free()
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        me.materials.append(mat)
        # sharp edges by angle (hard-surface look; Unity reads them as split normals)
        bm2 = bmesh.new()
        bm2.from_mesh(me)
        for e in bm2.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle() > math.radians(36):
                e.smooth = False
        bm2.to_mesh(me)
        bm2.free()
        # origin stays at the grip: shift object location to offset, mesh back to local
        me.transform(Matrix.Translation(-Vector(offset)))
        ob.location = offset
        return ob


def bore(x, r_out, r_in, depth, key="BK"):
    """Recessed bore behind a muzzle's front annulus (which ends at (x, r_in))."""
    return [(x - depth, r_in, key)]


# ---------- the guns (side view, cm)

def trigger(g, x, z):
    g.loft([((x, z), (x + 0.9, z)), ((x - 0.2, z - 2.6), (x + 0.5, z - 2.6))], 0.35, "BK", 0.15)


def revolver(g):
    g.lathe([(5, 1.6, "ST"), (21.5, 1.6, "ST"), (21.8, 1.95, "ST"), (24, 1.95, "ST"), (24, 0.8, "ST")]
            + bore(24, 1.95, 0.8, 1.2), c=(0, 0, 1.0))
    g.box(6, 21.5, -1.9, -0.2, 1.25, "LG")              # ejector lug under the barrel
    g.box(5, 23, 2.3, 3.0, 0.7, "ST", 0.2)               # top rib
    g.box(21.6, 23.2, 2.6, 4.0, 0.45, "BK", 0.15)        # front sight
    g.box(-3.5, 7, -3, 3.4, 1.55, "LG", 0.5)             # frame
    g.lathe([(-1.2, 2.4, "DG"), (-0.8, 3.2, "ST"), (1.4, 3.2, "ST"), (1.6, 3.3, "OR"), (3.8, 3.3, "OR"),
             (4.0, 3.2, "ST"), (6.0, 3.2, "ST"), (6.4, 2.4, "ST")], c=(0, 0, 0.2))   # cylinder
    g.lathe([(6.2, 0.7, "BK"), (7.4, 0.7, "BK")], c=(0, 0, 0.2), sides=8)            # centre pin
    g.loft([((-5.5, 3.0), (-3.2, 3.0)), ((-6.5, 6.0), (-4.8, 6.4))], 0.6, "BK", 0.2)  # hammer
    g.loft([((-5.6, -0.6), (0.6, -0.6)), ((-7.0, -5.5), (-1.0, -5.5)),
            ((-8.6, -10.5), (-2.6, -10.5)), ((-9.0, -12.2), (-3.4, -12.2))], 1.75, "BK", 0.7)  # grip
    g.box(-9.2, -3.2, -12.9, -12.0, 1.6, "ST", 0.3)      # grip cap
    g.bar([(-1.6, -2.8), (-1.2, -6.0), (2.0, -7.2), (5.2, -5.6), (6.0, -2.8)], 0.8, 0.55, "ST")
    trigger(g, 1.4, -2.6)


def burst(g):
    g.box(-7, 9, 0, 4.4, 1.8, "LG", 0.6)                 # slide
    g.box(8.6, 13.4, -0.4, 4.6, 2.0, "W", 0.6)           # front block
    g.box(9.6, 10.9, -0.7, 4.85, 2.25, "OR", 0.4)        # orange band
    g.box(11.4, 12.2, -0.7, 4.85, 2.25, "BK", 0.3)       # black band
    g.box(-1.0, 3.0, 2.0, 3.4, 1.95, "BK", 0.3)          # ejection port
    for i in range(4):                                   # slide serrations
        g.box(-6.2 + i * 1.0, -5.7 + i * 1.0, 0.6, 3.8, 1.95, "DG", 0.15)
    g.lathe([(12, 1.1, "DG"), (14.4, 1.1, "DG"), (14.4, 0.55, "DG")] + bore(14.4, 1.1, 0.55, 0.8), c=(0, 0, 2.0))
    g.box(-6.6, -5.0, 4.2, 5.4, 1.4, "BK", 0.25)         # rear sight
    g.box(11.0, 12.0, 4.4, 5.4, 0.45, "BK", 0.15)        # front sight
    g.box(-5, 11.5, -2.4, 0.4, 1.6, "BK", 0.5)           # frame
    g.loft([((-6.8, -1.0), (0.4, -1.0)), ((-8.2, -6.5), (-1.0, -6.5)), ((-8.8, -11.6), (-1.6, -11.6))],
           1.75, "BK", 0.7)                              # grip
    g.box(-9.2, -1.2, -12.8, -11.2, 1.9, "DG", 0.35)     # mag base
    g.box(-8.0, -1.8, -9.5, -4.0, 1.92, "DG", 0.4)       # grip texture panel
    g.bar([(0.6, -2.2), (0.8, -5.6), (4.0, -6.4), (6.6, -4.6), (7.0, -2.2)], 0.8, 0.55, "BK")
    trigger(g, 2.6, -2.2)


def smg(g):
    g.box(-9, 11, -2.2, 3.2, 2.2, "DG", 0.6)             # receiver
    g.box(-7, 11, 3.0, 3.9, 1.4, "BK", 0.25)             # top rail
    for i in range(7):
        g.box(-6.4 + i * 2.4, -5.4 + i * 2.4, 3.7, 4.4, 1.25, "BK", 0.15)   # rail teeth
    g.box(-1.5, 4.5, 4.2, 7.6, 1.7, "BK", 0.6)           # red-dot body
    g.lathe([(4.2, 1.2, "DG"), (5.0, 1.2, "DG"), (5.0, 0.8, "DG"), (4.7, 0.8, "RG")], c=(0, 0, 6.0), cap1="RG")
    g.box(10.5, 20.5, -2.0, 2.8, 2.6, "BL", 0.8)         # blue handguard
    for i in range(3):
        g.box(12.0 + i * 2.6, 13.3 + i * 2.6, -0.8, 1.8, 2.75, "BK", 0.3)   # vents
    g.lathe([(20, 1.0, "ST"), (24.5, 1.0, "ST"), (24.5, 1.3, "BK"), (26, 1.3, "BK"), (26, 0.6, "BK")]
            + bore(26, 1.3, 0.6, 1.0), c=(0, 0, 0.6))
    g.loft([((-6.0, -1.5), (-0.6, -1.5)), ((-7.6, -7), (-2.0, -7)), ((-8.4, -10.6), (-2.8, -10.6))],
           1.7, "BK", 0.7)                               # grip
    g.loft([((3.0, -1.5), (7.2, -1.5)), ((2.6, -8), (6.8, -8)), ((2.2, -12.4), (6.4, -12.4))],
           1.5, "RD", 0.6)                               # magazine
    g.box(2.0, 6.6, -13.2, -12.0, 1.7, "OR", 0.3)        # mag base
    g.box(-13, -8.5, -1.0, 2.6, 1.6, "BK", 0.4)          # stock stub
    g.box(-14.4, -12.6, -3.4, 3.4, 1.8, "DG", 0.5)       # butt plate
    g.box(6.0, 9.0, 1.6, 2.6, 2.45, "OR", 0.2)           # charging handle
    g.bar([(-0.8, -2.0), (-0.6, -5.4), (2.0, -6.0)], 0.8, 0.55, "BK")
    trigger(g, 0.6, -2.0)


def carbine(g):
    g.box(-9, 9, -2, 3, 2.0, "DG", 0.6)                  # upper receiver
    g.box(-3, 7, -4.2, -1.2, 1.8, "DG", 0.5)             # magwell
    g.box(8.5, 23, -1.6, 2.7, 2.5, "TN", 0.8)            # handguard
    for i in range(5):
        g.box(10.4 + i * 2.4, 11.6 + i * 2.4, -0.4, 1.6, 2.62, "BK", 0.3)   # slots
    g.lathe([(22, 0.8, "BK"), (30, 0.8, "BK"), (30, 1.25, "DG"), (33.5, 1.25, "DG"), (33.5, 0.55, "DG")]
            + bore(33.5, 1.25, 0.55, 1.0), c=(0, 0, 0.6))
    g.box(20.5, 22, 2.4, 5.4, 0.55, "BK", 0.2)           # front sight post
    g.box(-7, 21, 2.8, 3.7, 1.4, "BK", 0.25)             # top rail
    g.box(-3, 2.6, 3.5, 6.6, 1.8, "BK", 0.6)             # red-dot body
    g.lathe([(2.4, 1.3, "DG"), (3.2, 1.3, "DG"), (3.2, 0.85, "DG"), (2.9, 0.85, "RG")], c=(0, 0, 5.0), cap1="RG")
    g.loft([((0.2, -3.6), (5.0, -3.6)), ((0.8, -9.0), (5.6, -9.0)), ((2.2, -13.4), (7.0, -13.4))],
           1.5, "DG", 0.6)                               # magazine
    g.loft([((-7.4, -1.6), (-2.6, -1.6)), ((-9.0, -7.5), (-4.6, -7.5)), ((-9.8, -10.6), (-5.6, -10.6))],
           1.6, "BK", 0.7)                               # grip
    g.lathe([(-15, 1.2, "BK"), (-8.5, 1.2, "BK")], c=(0, 0, 1.0))                  # buffer tube
    g.loft([((-21, -4.6), (-21, 3.2)), ((-14, -1.2), (-14, 3.0))], 1.9, "BK", 0.6)  # stock
    g.box(-22.4, -20.6, -5.0, 3.5, 2.05, "DG", 0.5)      # butt pad
    g.bar([(-2.2, -3.0), (-2.0, -5.6), (1.0, -6.2)], 0.8, 0.5, "BK")
    trigger(g, -0.6, -3.0)


def shotgun(g):
    g.box(-7, 9, -2.4, 3.4, 2.2, "DG", 0.7)              # receiver
    g.lathe([(8, 1.15, "DG"), (35, 1.15, "DG"), (35, 0.65, "DG")] + bore(35, 1.15, 0.65, 1.2), c=(0, 0, 1.8))
    g.lathe([(8, 1.0, "BK"), (31, 1.0, "BK"), (31.6, 0.8, "DG")], c=(0, 0, -0.6))  # mag tube
    g.box(29.6, 31.2, -1.9, 3.2, 1.3, "BK", 0.3)         # barrel clamp
    g.lathe([(34.0, 0.3, "ST"), (34.4, 0.3, "ST")], axis="z", c=(0, 0, 2.7), sides=8)  # bead
    g.box(13, 25, -2.8, 1.1, 2.6, "WD", 0.9)             # pump
    for i in range(5):
        g.box(14.4 + i * 2.2, 15.2 + i * 2.2, -3.0, 1.3, 2.75, "DW", 0.3)   # grooves
    for i in range(3):
        g.lathe([(-0.2, 0.75, "RD"), (2.2, 0.75, "RD"), (2.2, 0.8, "OR"), (2.9, 0.8, "OR")],
                axis="y", c=(-3.6 + i * 2.0, 0, 0.6), sides=8)   # side shells (through the receiver)
    g.loft([((-7, 3.0), (-7, -2.4)), ((-13, 1.6), (-13, -4.6)), ((-26, 2.0), (-26, -8.2))],
           1.9, "WD", 0.8)                               # stock
    g.box(-27.5, -25.6, -8.6, 2.4, 2.15, "BK", 0.5)       # butt pad
    g.bar([(-2.2, -2.4), (-2.0, -5.6), (1.6, -6.6), (4.4, -5.0), (5.0, -2.4)], 0.8, 0.55, "BK")
    trigger(g, 0.8, -2.4)


def rifle(g):
    g.box(-6, 7, -2.8, 2.8, 2.0, "DG", 0.6)              # receiver
    g.lathe([(6, 0.95, "DG"), (40, 0.95, "DG"), (40, 0.5, "DG")] + bore(40, 0.95, 0.5, 1.0), c=(0, 0, 1.4))
    g.lathe([(6, 0.75, "DG"), (35, 0.75, "DG"), (35.4, 0.6, "ST")], c=(0, 0, -0.6))  # mag tube
    g.box(6.5, 21, -2.2, 1.0, 2.3, "WD", 0.8)            # forend
    g.box(33.4, 34.6, -1.6, 2.6, 1.2, "BK", 0.3)         # barrel band
    g.box(37.6, 38.6, 2.0, 3.6, 0.4, "BK", 0.15)         # front sight
    g.box(9, 11, 2.0, 3.2, 0.9, "BK", 0.2)               # rear sight
    g.loft([((-6, 2.6), (-6, -2.6)), ((-12, 1.6), (-12, -4.2)), ((-28, 2.2), (-28, -8.4))],
           1.85, "WD", 0.8)                              # stock
    g.box(-29.4, -27.6, -8.8, 2.6, 2.1, "BK", 0.5)      # butt plate
    g.loft([((-6.8, 2.4), (-5.4, 2.4)), ((-8.0, 4.6), (-6.8, 5.0))], 0.6, "BK", 0.2)  # hammer
    g.bar([(2.6, -2.6), (2.0, -5.2), (-1.2, -6.8), (-5.4, -6.6), (-7.6, -5.2), (-7.0, -3.4)],
          0.9, 0.55, "DG")                               # lever loop
    trigger(g, -0.4, -2.6)


def blaster(g):
    g.loft([((-18, -4), (-18, 6)), ((-10, -6), (-10, 7.2)), ((10, -5.4), (10, 7.2)), ((18, -4), (18, 6))],
           3.0, "W", 1.0)                                # main body
    g.box(-6.5, 10.5, 0.2, 4.4, 3.2, "DG", 0.4)          # window frame
    g.box(-5.5, 9.5, 1.0, 3.6, 3.4, "GL", 0.3)           # glow window
    g.box(-16.5, -8.5, -3.6, 2.6, 3.2, "DG", 0.5)        # rear side panel
    g.box(-15.0, -10.0, -2.4, 1.4, 3.4, "OR", 0.4)       # orange inset
    g.lathe([(17, 3.0, "W"), (19.5, 3.0, "W"), (19.7, 3.4, "W"), (20.6, 3.4, "W"), (20.8, 3.2, "GL"),
             (26.2, 3.2, "GL"), (26.4, 3.4, "W"), (27.4, 3.4, "W"), (27.8, 4.4, "DG"), (29.6, 4.6, "DG"),
             (29.8, 4.75, "OR"), (31.6, 4.75, "OR"), (31.8, 4.6, "DG"), (34, 4.6, "DG"), (34.4, 4.1, "DG"),
             (34.4, 3.2, "DG"), (33.2, 3.2, "BK")], c=(0, 0, 1.2), sides=24, cap1="GC")   # barrel + muzzle
    for zz in (-1.6, 4.0):                               # cage rails over the glow coil
        g.box(19.8, 27.0, zz - 0.5, zz + 0.5, 2.0, "W", 0.3)
    g.box(-6, 4, 6.8, 9.0, 1.6, "OR", 0.5)               # scope mount
    g.lathe([(-9, 1.6, "DG"), (-8.6, 2.2, "DG"), (-6.4, 2.2, "DG"), (-6.2, 2.0, "BK"), (4.4, 2.0, "BK"),
             (4.6, 2.3, "OR"), (6.4, 2.3, "OR"), (6.6, 1.9, "DG")], c=(0, 0, 10.6), cap0="GL", cap1="GC")  # scope
    g.box(-15, -6, 6.6, 8.4, 2.4, "DG", 0.5)             # rear top block
    g.box(12, 16, 6.6, 8.0, 1.2, "DG", 0.4)              # front sight
    g.loft([((-9.0, -4.6), (-1.6, -4.6)), ((-10.4, -11), (-3.4, -11)), ((-11.2, -16.2), (-4.4, -16.2))],
           2.1, "DG", 0.8)                               # grip
    g.box(-11.8, -3.8, -17.4, -15.6, 2.3, "BK", 0.4)     # grip cap
    g.box(2.0, 10.0, -9.2, -4.6, 2.6, "DG", 0.6)         # energy cell
    g.box(1.4, 10.6, -10.4, -8.8, 2.8, "OR", 0.4)        # cell base
    g.box(3.6, 8.4, -8.0, -6.6, 2.75, "GL", 0.3)         # cell glow
    g.loft([((-18, -3.4), (-18, 5.2)), ((-27, -4.2), (-27, 3.6))], 2.6, "W", 0.8)  # stock
    g.box(-32, -26.6, -6.2, 4.4, 3.0, "OR", 0.9)         # stock pad
    g.box(-33.6, -31.4, -6.8, 5.0, 2.7, "DG", 0.6)       # butt plate
    g.bar([(-1.4, -5.2), (-1.0, -8.6), (1.6, -9.0)], 0.9, 0.6, "LG")
    trigger(g, 0.0, -5.0)


BLASTERS = {
    "Common":    {},
    "Rare":      {"OR": "BL"},
    "Epic":      {"OR": "RD", "GL": "RG", "GC": "RG"},
    "Legendary": {"W": "YL", "OR": "DY", "DG": "BK"},
}

GUNS = [  # name, builder, grip point (cm, side view), cmap
    ("SM_Revolver", revolver, (-5.0, -5.0), None),
    ("SM_Burst", burst, (-4.6, -5.0), None),
    ("SM_SMG", smg, (-4.4, -5.0), None),
    ("SM_Carbine", carbine, (-5.8, -5.0), None),
    ("SM_Shotgun", shotgun, (-3.0, -4.0), None),
    ("SM_Rifle", rifle, (-4.0, -4.0), None),
] + [("SM_Blaster_" + k, blaster, (-6.8, -9.0), v) for k, v in BLASTERS.items()]


def build_guns(out_dir):
    coll = bpy.data.collections.get("AimGuns") or bpy.data.collections.new("AimGuns")
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    img = make_atlas(out_dir + "/T_Weapons.png")
    mat = make_material(img)
    res = {}
    for i, (name, fn, grip, cmap) in enumerate(GUNS):
        g = Gun(cmap)
        fn(g)
        ob = g.finish(name, grip, coll, mat, (0, (i % 5) * -0.9, (i // 5) * -0.45))
        r = topo_check(ob, target="quad")
        res[name] = {"verdict": r["verdict"], "faces": r.get("faces"), "quad_pct": r.get("quad_pct"),
                     "errors": r["errors"], "zfight": len(zfight(ob, tol=0.001))}
    return res
