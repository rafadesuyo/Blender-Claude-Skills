# Cute mailbox in the NewLua pack style (gradient atlas, smooth shading, quads, closed shells).
# Run inside the pack .blend (Blender MCP execute_blender_code):
#   exec(open(r"<skills>/blender-game-props/gradient_trees.py").read())
#   exec(open(r"<skills>/blender-game-props/mailbox.py").read())
#   build_mailbox()
# Makes SM_Mailbox in collection Mailbox: an arched red box (door on the front, -Y) with a gold
# knob, a raised yellow flag on its right side, a love letter peeking out of the door, on a round
# wooden post standing in a grassy mound with two pebbles. Chunky toy proportions (short thick
# post, big box). Pivot at the bottom centre, ~1.3 m.

MB_RED = c0(14, 0.86, 0.99)        # dark -> bright red
MB_RED_DARK = c0(14, 0.86, 0.90)   # the door, a shade darker
MB_GOLD = c0(23, 0.90, 0.99)
MB_IRON = c1(7, 0.70, 0.80)
MB_CREAM = c1(9, 0.70, 0.82)
MB_PINK = c0(29, 0.86, 0.95)
MB_GRASS = c0(9)
MB_STONE = c1(6, 0.70, 0.82)


def arch_profile(w, wall, n_arch=10):
    """Mailbox cross-section (x, z): flat bottom with soft corners, straight walls, round top.
    Mirrored, even count, ordered so quad_cap zips it from the top down."""
    r = w / 2
    right = []
    for i in range(1, n_arch // 2 + 1):                        # top arch, right half
        a = math.pi / 2 - (math.pi / 2) * i / (n_arch // 2)
        right.append((r * math.cos(a), wall + r * math.sin(a)))
    right += [(r, wall * 0.5), (r, 0.025), (r - 0.025, 0.0), (0.04, 0.0)]
    left = [(-x, z) for x, z in reversed(right)]
    return right + left


def arch_body(bm, w, wall, length, col, y0=0.0, bevel=0.018, z0=0.0, n_arch=10):
    """The tunnel-shaped box along Y: rings from the profile, with a soft rim at both ends."""
    prof = arch_profile(w, wall, n_arch)
    cx, cz = 0.0, (wall + w / 2) / 2
    def ring(y, s):
        return [b.verts.new((cx + x * s, y0 + y, z0 + cz + (z - cz) * s)) for x, z in prof]
    b = bmesh.new()
    s_in = 1 - 2 * bevel / w
    rings = [ring(-length / 2, s_in), ring(-length / 2 + bevel, 1.0), ring(0.0, 1.0),
             ring(length / 2 - bevel, 1.0), ring(length / 2, s_in)]
    n = len(prof)
    for j in range(len(rings) - 1):
        for k in range(n):
            b.faces.new((rings[j][k], rings[j][(k + 1) % n], rings[j + 1][(k + 1) % n], rings[j + 1][k]))
    quad_cap(b, rings[0])
    quad_cap(b, rings[-1])
    uv_part(b, col)
    merge(bm, b)


def rbox(bm, center, size, col, cuts=3, power=5.0):
    """Rounded box (superellipsoid of a subdivided cube): soft toy edges, all quads."""
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=2.0)
    bmesh.ops.subdivide_edges(b, edges=b.edges[:], cuts=cuts, use_grid_fill=True)
    for v in b.verts:
        x, y, z = v.co
        d = (abs(x) ** power + abs(y) ** power + abs(z) ** power) ** (1 / power)
        v.co = Vector((x / d * size[0] / 2, y / d * size[1] / 2, z / d * size[2] / 2)) + Vector(center)
    uv_part(b, col)
    merge(bm, b)


def heart(n=16, s=1.0):
    """Even-count heart outline (x, z) around (0, 0)."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        z = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * s / 17, z * s / 17))
    return pts


def build_mailbox(name="SM_Mailbox"):
    mat = bpy.data.materials["M_GradientTexture"]
    coll = bpy.data.collections.get("Mailbox")
    if coll is None:
        coll = bpy.data.collections.new("Mailbox")
        bpy.context.scene.collection.children.link(coll)
    bm = bmesh.new()
    post_top = 0.72
    # grassy mound + pebbles
    blob(bm, (0, 0, 0.0), 0.26, MB_GRASS, 11, scale=(1.0, 1.0, 0.32))
    blob(bm, (0.2, -0.13, 0.03), 0.06, MB_STONE, 12, scale=(1.0, 0.9, 0.7))
    blob(bm, (-0.17, 0.12, 0.03), 0.045, MB_STONE, 13, scale=(1.0, 0.9, 0.7))
    # round wooden post, a touch thicker at the bottom, with a little cap plank under the box
    tube(bm, [(0, 0, 0.02), (0, 0, 0.36), (0, 0, post_top)], [0.085, 0.078, 0.074], BARK, sides=10)
    rbox(bm, (0, 0, post_top + 0.025), (0.32, 0.5, 0.06), BARK)
    # the box
    w, wall, length = 0.4, 0.2, 0.62
    zb = post_top + 0.05
    arch_body(bm, w, wall, length, MB_RED, z0=zb)
    # door: a slightly smaller arch slab on the front, a shade darker, with a gold knob
    arch_body(bm, w * 0.86, wall * 0.86, 0.035, MB_RED_DARK, y0=-length / 2 - 0.006, bevel=0.01, z0=zb + 0.022)
    blob(bm, (0, -length / 2 - 0.05, zb + 0.13), 0.034, MB_GOLD, 21, scale=(1, 0.8, 1), cuts=1)
    # flag on the right side, raised: arm + flag plate + pivot bolt
    fx = w / 2 + 0.02
    tube(bm, [(fx, 0.16, zb + 0.16), (fx, 0.15, zb + 0.5)], [0.017, 0.017], MB_IRON, sides=6)
    rbox(bm, (fx + 0.004, 0.07, zb + 0.44), (0.03, 0.17, 0.12), MB_GOLD, cuts=2)
    blob(bm, (fx, 0.16, zb + 0.16), 0.03, MB_IRON, 22, cuts=1)
    # love letter peeking out of the door top, tilted, with a pink heart seal
    let = bmesh.new()
    rbox(let, (0, 0, 0), (0.22, 0.014, 0.15), MB_CREAM, cuts=2, power=8.0)
    slab(let, heart(16, 0.055), MB_PINK, thick=0.012, bulge=0.007, at=(0, -0.013, 0.0))
    bmesh.ops.rotate(let, cent=Vector(), matrix=Matrix.Rotation(math.radians(-14), 3, 'X') @ Matrix.Rotation(math.radians(9), 3, 'Y'), verts=let.verts)
    bmesh.ops.translate(let, vec=Vector((0.03, -length / 2 - 0.035, zb + wall + 0.2)), verts=let.verts)
    t = bpy.data.meshes.new("_l")
    let.to_mesh(t)
    let.free()
    bm.from_mesh(t)
    bpy.data.meshes.remove(t)
    o = finish(bm, name, coll, (0, 0, 0), mat)
    return o
