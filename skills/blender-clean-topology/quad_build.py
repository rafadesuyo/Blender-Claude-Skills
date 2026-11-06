# Quad-first building blocks: shapes that are all quads from the start, so nothing needs fixing.
#   exec(open(r"<skills>/blender-clean-topology/quad_build.py").read())
# All functions take/return a bmesh; finish with orient_outward(b) (from topo_clean.py) or
# bmesh.ops.recalc_face_normals before converting to a mesh.
import bmesh, math, random
from mathutils import Vector


def _ring_frame(ring):
    c = sum((v.co for v in ring), Vector()) / len(ring)
    n = Vector()
    for i in range(len(ring)):  # Newell normal: robust for any ring shape
        n += (ring[i - 1].co - c).cross(ring[i].co - c)
    n.normalize()
    ax = (ring[0].co - c)
    ax = (ax - n * ax.dot(n)).normalized()
    return c, n, ax, n.cross(ax)


def grid_cap(b, ring, inner=0.55):
    """Closes a ring of 4k verts with quads only: a k x k grid in the middle plus one ring of quads
    around it (the classic "circle to square" cap). No n-gon, no fan, no 6+ poles; poles are only
    the 4 grid corners (valence 3). Returns the new faces."""
    n = len(ring)
    if n % 4 or n < 4:
        raise ValueError(f"grid_cap needs 4k ring verts, got {n}")
    k = n // 4
    c, nrm, ax, ay = _ring_frame(ring)
    rad = sum((v.co - c).length for v in ring) / n * inner
    def disk(u, w):  # square -> disk (elliptical grid mapping), keeps the inner grid rounded
        return u * math.sqrt(max(0.0, 1 - w * w / 2)), w * math.sqrt(max(0.0, 1 - u * u / 2))
    g = {}
    for i in range(k + 1):
        for j in range(k + 1):
            u, w = -1 + 2 * i / k, -1 + 2 * j / k
            x, y = disk(u, w)
            g[i, j] = b.verts.new(c + ax * (x * rad) + ay * (y * rad))
    faces = [b.faces.new((g[i, j], g[i + 1, j], g[i + 1, j + 1], g[i, j + 1])) for i in range(k) for j in range(k)]
    # Grid boundary counter-clockwise (in ax/ay), 4k verts, starting at corner (0, 0).
    border = [g[i, 0] for i in range(k)] + [g[k, j] for j in range(k)] + \
             [g[i, k] for i in range(k, 0, -1)] + [g[0, j] for j in range(k, 0, -1)]
    def ang(co):
        d = co - c
        return math.atan2(d.dot(ay), d.dot(ax))
    # Ring may run either way round: make it counter-clockwise too.
    if (ang(ring[1].co) - ang(ring[0].co)) % (2 * math.pi) > math.pi:
        ring = ring[::-1]
    ba, ra = [ang(v.co) for v in border], [ang(v.co) for v in ring]
    def cost(off):
        return sum(abs((ba[(m + off) % n] - ra[m] + math.pi) % (2 * math.pi) - math.pi) for m in range(n))
    off = min(range(n), key=cost)
    for m in range(n):
        faces.append(b.faces.new((ring[m], ring[(m + 1) % n], border[(m + 1 + off) % n], border[(m + off) % n])))
    return faces


def strip_cap(b, ring):
    """Closes a ring of an even vert count with strips of quads (fine for small or long thin caps;
    use grid_cap for round caps of 8+ verts)."""
    n = len(ring)
    return [b.faces.new((ring[i], ring[i + 1], ring[n - 2 - i], ring[n - 1 - i])) for i in range(n // 2 - 1)]


def quad_sphere(r, cuts=3, scale=(1, 1, 1), jitter=0.0, seed=0):
    """Sphere from a subdivided cube pushed out: all quads, 8 valence-3 poles, no triangle caps
    (a UV sphere has tri fans at both poles)."""
    rnd = random.Random(seed)
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=2.0)
    if cuts:
        bmesh.ops.subdivide_edges(b, edges=b.edges[:], cuts=cuts, use_grid_fill=True)
    for v in b.verts:
        p = v.co.normalized() * r * (1 + rnd.uniform(-jitter, jitter))
        v.co = Vector((p.x * scale[0], p.y * scale[1], p.z * scale[2]))
    return b


def quad_cylinder(r, h, sides=16, segments=1, cap="grid", bevel=0.0):
    """Cylinder standing on Z=0, all quads. sides is rounded up to a multiple of 4 for grid caps
    (even for strip caps). cap: "grid" | "strip" | None (open tube). bevel adds one chamfer loop
    at each rim (offset in m), which also acts as a support loop for subdivision."""
    step = 4 if cap == "grid" else 2
    sides += (-sides) % step
    b = bmesh.new()
    zs = [h * s / segments for s in range(segments + 1)]
    rings = []
    def ring(z, rr):
        return [b.verts.new((rr * math.cos(2 * math.pi * i / sides), rr * math.sin(2 * math.pi * i / sides), z)) for i in range(sides)]
    if bevel:
        rings.append(ring(0.0, r - bevel))
        zs = [min(max(z, bevel), h - bevel) for z in zs]
    rings += [ring(z, r) for z in zs]
    if bevel:
        rings.append(ring(h, r - bevel))
    for s in range(len(rings) - 1):
        for i in range(sides):
            j = (i + 1) % sides
            b.faces.new((rings[s][i], rings[s][j], rings[s + 1][j], rings[s + 1][i]))
    if cap:
        fill = grid_cap if cap == "grid" else strip_cap
        fill(b, rings[0])
        fill(b, rings[-1])
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    return b


def quad_box(size, cuts=(1, 1, 1), bevel=0.0):
    """Box centered at the origin with an even grid on every side (cuts per axis) and an optional
    chamfer. The bevel uses segments=2: each corner becomes 3 quads around a valence-3 vert.
    (segments=1 leaves a triangle on every corner.)"""
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=1.0)
    bmesh.ops.scale(b, vec=Vector(size), verts=b.verts)
    for axis, n in enumerate(cuts):
        if n > 1:
            for t in range(1, n):
                co = -size[axis] / 2 + size[axis] * t / n
                no = Vector((0, 0, 0)); no[axis] = 1
                bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=no * co, plane_no=no)
    if bevel:
        outer = [e for e in b.edges if e.calc_face_angle(0) > math.radians(60)]
        bmesh.ops.bevel(b, geom=outer, offset=bevel, segments=2, profile=0.5, affect='EDGES', clamp_overlap=True)
    return b
