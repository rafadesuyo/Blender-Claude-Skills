# Z-fighting check: finds faces of DIFFERENT parts (islands) of a mesh that lie in the same plane
# (within TOL) and overlap. Those flicker in game (Dante: "don't let it happen ever").
#   exec(open(r"<skills>/blender-game-props/zfight_check.py").read())
#   zfight(obj)  -> list of (partA, partB, centre, area); [] = clean
# Run it on every model before export, next to check_closed.
import bmesh, math
from mathutils import Vector

ZF_TOL = 0.004      # m: planes closer than this fight
ZF_MIN_AREA = 1e-4  # m2: ignore slivers under 1 cm2 (invisible at any game distance)


def _islands(b):
    b.faces.ensure_lookup_table()
    part = {}
    n = 0
    for f in b.faces:
        if f.index in part:
            continue
        stack = [f]
        part[f.index] = n
        while stack:
            g = stack.pop()
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in part:
                        part[h.index] = n
                        stack.append(h)
        n += 1
    return part


def _clip(poly, a, b):
    """Sutherland-Hodgman: keep the part of poly left of edge a->b (2D)."""
    out = []
    def side(p):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        sp, sq = side(p), side(q)
        if sp >= 0:
            out.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def _area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))) / 2


def _ccw(poly):
    s = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return poly if s > 0 else poly[::-1]


def zfight(obj, tol=ZF_TOL, min_area=ZF_MIN_AREA, ground=True):
    """ground=True skips downward faces lying on the model's floor (z = its lowest point): they
    sit on the ground and can never be seen."""
    b = bmesh.new()
    b.from_mesh(obj.data)
    part = _islands(b)
    planes = {}
    zmin = min(v.co.z for v in b.verts)
    for f in b.faces:
        if f.calc_area() < 1e-7:
            continue
        if ground and f.normal.z < -0.999 and all(v.co.z < 0.002 or abs(v.co.z - zmin) < 0.002 for v in f.verts):
            continue
        nrm = f.normal.copy()
        orig = f.normal.copy()
        # canonical direction so opposite-facing coplanar faces meet in the same bucket
        if (nrm.x, nrm.y, nrm.z) < (0, 0, 0) and (abs(nrm.x) > 1e-6 or abs(nrm.y) > 1e-6 or abs(nrm.z) > 1e-6):
            for c in (nrm.x, nrm.y, nrm.z):
                if abs(c) > 1e-6:
                    if c < 0:
                        nrm = -nrm
                    break
        d = nrm.dot(f.verts[0].co)
        key = (round(nrm.x, 2), round(nrm.y, 2), round(nrm.z, 2))
        planes.setdefault(key, []).append((d, f, nrm, orig))
    hits = {}
    for key, lst in planes.items():
        lst.sort(key=lambda t: t[0])
        for i in range(len(lst)):
            d1, f1, n1, o1 = lst[i]
            j = i + 1
            while j < len(lst) and lst[j][0] - d1 <= tol:
                d2, f2, n2, o2 = lst[j]
                j += 1
                # faces of two parts in one plane, facing the SAME way, flicker; back-to-back faces
                # (two solids touching) are hidden and are fine
                if part[f1.index] == part[f2.index] or o1.dot(o2) < 0.999:
                    continue
                # 2D overlap in the plane
                u = n1.orthogonal().normalized()
                v = n1.cross(u)
                p1 = _ccw([(x.co.dot(u), x.co.dot(v)) for x in f1.verts])
                p2 = _ccw([(x.co.dot(u), x.co.dot(v)) for x in f2.verts])
                poly = p1
                for k in range(len(p2)):
                    poly = _clip(poly, p2[k], p2[(k + 1) % len(p2)])
                    if not poly:
                        break
                if poly and len(poly) >= 3:
                    a = _area(poly)
                    if a > min_area:
                        pk = (min(part[f1.index], part[f2.index]), max(part[f1.index], part[f2.index]))
                        c = f1.calc_center_median()
                        if pk not in hits or hits[pk][1] < a:
                            hits[pk] = (tuple(round(x, 3) for x in c), round(a, 5))
    b.free()
    return [(k[0], k[1], v[0], v[1]) for k, v in sorted(hits.items(), key=lambda kv: -kv[1][1])]
