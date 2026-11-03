# gab villager: Walter the cat (2026-11-02), on the shared plush body of villager_base.py, from
# Dante's grumpy cat reference (1000 x 1044 px). Cat px are mapped onto the body box the penguin
# uses (centre x 510 -> 562, head top y 255 -> 308, x 1.103, y 1.158), so the body, the arm
# shoulders and the part IDs match the M_Villager material.
#   Body, half-lidded eyes (white, pupils looking in, a dark lid line), pink nose, the little
#   frown, pointed ears (brown, pink inside), stubby arms held out, brown paws.
# Atlas: Characters_tex/make_atlas.py cat -> T_Villager_Cat.png (column meanings there).
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/villager_cat.py")).read())
#   build_villager_cat(atlas_path)
exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/villager_base.py")).read())

PARTS.update({"Eyes": 7, "Ears": 5})
CAT_CX, CAT_TOP, CAT_SX, CAT_SY = 510, 255, 1.103, 1.158


def C(cx, cy):
    """cat reference px -> (x, z) metres on the shared body."""
    return X(562 + (cx - CAT_CX) * CAT_SX), Z(308 + (cy - CAT_TOP) * CAT_SY)


def cw(px):
    return px * CAT_SX * PX


def ch(px):
    return px * CAT_SY * PX


def hug(b, lift):
    """Moves every vert to sit on the body's front (its own depth kept), lift in front of it."""
    for v in b.verts:
        v.co.y += body_front_y(v.co.x, v.co.z) - lift


CAT_BACK_U = (972 + 22) / ATLAS_N   # make_atlas.py's 8th column: the back, brown fading to beige


def cat_body_uvs(b):
    """Like body_uvs, but the back uses the cat's own back column (no seam with the beige sides)."""
    uv = b.loops.layers.uv.get("UVMap") or b.loops.layers.uv.new("UVMap")
    for f in b.faces:
        for l in f.loops:
            x, z = l.vert.co.x, l.vert.co.z
            px, py = x / PX + CX, GROUND - z / PX
            t = min(max((py - BODY_Y0) / (BODY_Y1 - BODY_Y0), 0.0), 1.0)
            if f.normal.y > 0.2:
                l[uv].uv = (CAT_BACK_U, 1 - (0.01 + 0.98 * t))
            else:
                s = min(max((px - BODY_X0) / (BODY_X1 - BODY_X0), 0.002), 0.998)
                l[uv].uv = (s * ISL_W / ATLAS_N, 1 - (0.002 + 0.996 * t) * ISL_H / ATLAS_N)


def material_for(img, name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.8
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.5
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UVMap"
    nt.links.new(uvn.outputs[0], tex.inputs[0])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m


def build_villager_cat(atlas_path, name="Villager_Cat", detail=0.65, offset=(1.6, 0.0, 0.0)):
    global DETAIL
    DETAIL = detail
    coll = bpy.data.collections.get(name)
    if coll:
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    img = bpy.data.images.load(atlas_path, check_existing=True)
    img.reload()
    M = material_for(img, "M_Villager_Cat")
    objs = []

    # --- body (the shared one)
    b = superellipsoid(None, (0, 0, BZ), (BA, BB, BC), (BP, 2.6, BP), cuts=18)
    cat_body_uvs(b)
    objs.append(finish(b, "Body", coll, M, "Body"))

    # --- grumpy eyes: whites flattened under a straight lid, big pupils looking inward, lid line
    for side, s in (("L", -1), ("R", 1)):
        ecx = CAT_CX + s * 140          # 370 / 650
        ex, ez = C(ecx, 512)
        _, lid_z = C(ecx, 486)
        # white: an oval whose top is cut flat by the lid (the half-shut grumpy look)
        b = superellipsoid(None, (ex, 0, ez), (cw(86), 0.02, ch(50)), (2.3, 2.0, 2.3), cuts=7)
        for v in b.verts:
            if v.co.z > lid_z:
                v.co.z = lid_z + (v.co.z - lid_z) * 0.08
        hug(b, 0.004)
        objs.append(finish(b, "EyeWhite" + side, coll, M, "Eyes", "shine"))
        # pupil (in front of the white, shifted toward the nose)
        px_, pz = C(ecx - s * 20, 512)
        b = superellipsoid(None, (px_, 0, pz), (cw(56), 0.012, ch(44)), (2.2, 2.0, 2.2), cuts=6)
        for v in b.verts:
            if v.co.z > lid_z - 0.002:
                v.co.z = lid_z - 0.002 + (v.co.z - (lid_z - 0.002)) * 0.08
        hug(b, 0.017)
        objs.append(finish(b, "Pupil" + side, coll, M, "Eyes", "eye"))
        # lid line across the top of the eye
        x0, z0 = C(ecx - 96, 486)
        x1, z1 = C(ecx + 96, 486)
        steps = 8
        path = []
        for i in range(steps + 1):
            t = i / steps
            x, z = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
            path.append(Vector((x, body_front_y(x, z) - 0.022, z)))
        b = tube(path, 0.009, max(6, int(round(8 * DETAIL))))
        objs.append(finish(b, "Lid" + side, coll, M, "Eyes", "blush"))

    # --- nose: a soft pink triangle pointing down
    nx, nz = C(512, 510)
    b = superellipsoid(None, (nx, 0, nz), (cw(28), 0.016, ch(17)), (2.6, 2.0, 2.4), cuts=6)
    for v in b.verts:
        t = (nz + ch(17) - v.co.z) / (2 * ch(17))
        v.co.x *= 1.0 - 0.5 * max(0.0, min(1.0, t))
    hug(b, 0.012)
    objs.append(finish(b, "Nose", coll, M, "Face", "accent"))

    # --- the frown: a short line down from the nose and a little upside-down V
    def line(pts):
        path = []
        for (ax, az), (bx, bz) in zip(pts, pts[1:]):
            for i in range(5):
                t = i / 5
                x, z = ax + (bx - ax) * t, az + (bz - az) * t
                path.append(Vector((x, body_front_y(x, z) - 0.006, z)))
        x, z = pts[-1]
        path.append(Vector((x, body_front_y(x, z) - 0.006, z)))
        return tube(path, 0.0055, 6)
    b = line([C(512, 527), C(512, 547)])
    add(b, line([C(475, 575), C(512, 547), C(549, 575)]))
    objs.append(finish(b, "Mouth", coll, M, "Face", "blush"))

    # --- ears: rounded triangles on the head, tips leaning out, pink inside
    def ear_shape(half, taper=0.86):
        e = superellipsoid(None, (0, 0, 0), half, (2.6, 2.0, 2.6), cuts=8)
        for v in e.verts:
            t = (v.co.z + half[2]) / (2 * half[2])
            v.co.x *= 1.0 - taper * t
            v.co.y *= 1.0 - 0.45 * t
            v.co.y += 0.03 * t * t
        return e
    # big wide-based ears at the head's corners (reference: x 210..470, tips at y 125), their base
    # sunk into the head; the pink inside is a thin shell ON the ear's front face (same curve)
    EH = (0.165, 0.055, 0.155)
    ETAPER = 0.8

    def ear_front(x, z):
        """y of the outer ear's front at local (x, z) (before tilt), matching ear_shape."""
        # the untapered blob is |x/a|^2.6 + |y/b|^2 + |z/c|^2.6 = 1; ear_shape then tapers x and y
        t = min(max((z + EH[2]) / (2 * EH[2]), 0.0), 1.0)
        x0 = x / max(1.0 - ETAPER * t, 1e-4)
        inside = 1.0 - abs(x0 / EH[0]) ** 2.6 - abs(z / EH[2]) ** 2.6
        return -EH[1] * math.sqrt(max(0.0, inside)) * (1.0 - 0.45 * t) + 0.03 * t * t
    for side, s in (("L", -1), ("R", 1)):
        bx, bz = C(CAT_CX + s * 195, 255)
        bz -= 0.045
        tilt = Matrix.Rotation(math.radians(16 * s), 3, 'Y')
        at = Vector((bx, -0.04, bz))
        outer = ear_shape(EH, ETAPER)
        bmesh.ops.rotate(outer, cent=Vector(), matrix=tilt, verts=outer.verts)
        bmesh.ops.translate(outer, vec=at, verts=outer.verts)
        objs.append(finish(outer, "Ear" + side, coll, M, "Ears", "body"))
        inner = ear_shape(EH, ETAPER)
        for v in inner.verts:
            t = (v.co.z + EH[2]) / (2 * EH[2])
            hy = EH[1] * (1.0 - 0.45 * t)
            rel = (v.co.y - 0.03 * t * t) / max(hy, 1e-4)      # -1 front .. 1 back
            v.co.x *= 0.66
            v.co.z = v.co.z * 0.74 + 0.03
            v.co.y = ear_front(v.co.x, v.co.z) - 0.004 + (rel + 1) * 0.5 * 0.012
        bmesh.ops.rotate(inner, cent=Vector(), matrix=tilt, verts=inner.verts)
        bmesh.ops.translate(inner, vec=at, verts=inner.verts)
        objs.append(finish(inner, "EarInner" + side, coll, M, "Ears", "mouth", True))

    # --- stubby arms held out a little below level (shoulders where the penguin's flippers are)
    for side, s in (("L", -1), ("R", 1)):
        cz = Z(742)
        b = superellipsoid(None, (0, 0, 0), (0.115, 0.06, 0.078), (2.4, 2.0, 2.4), cuts=9)
        for v in b.verts:
            t = (v.co.x + 0.115) / 0.23
            v.co.z *= 1.0 - 0.12 * t
        if s < 0:
            bmesh.ops.scale(b, vec=Vector((-1, 1, 1)), verts=b.verts)
            bmesh.ops.reverse_faces(b, faces=b.faces)
        bmesh.ops.translate(b, vec=Vector((s * (BA + 0.06), 0.0, cz)), verts=b.verts)
        piv = Vector((s * BA, 0.02, cz))
        bmesh.ops.rotate(b, cent=piv, matrix=Matrix.Rotation(math.radians(12 * s), 3, 'Y'), verts=b.verts)
        part = "Flipper" + side
        objs.append(finish(b, "Arm" + side, coll, M, part, "body"))

    # --- paws: rounded blocks like the penguin's feet, brown
    for side, px in (("L", 394), ("R", 730)):
        fx = X(px)
        b = superellipsoid(None, (fx, -0.16, 0.058), (0.092, 0.088, 0.058), (2.7, 2.4, 2.6), cuts=8)
        part = "Foot" + side
        objs.append(finish(b, "Paw" + side, coll, M, part, "body", True))

    for o in objs:
        o.location = Vector(offset)
    return [o.name for o in objs]
