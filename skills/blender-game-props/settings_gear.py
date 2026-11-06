# gab Settings station (2026-10-30): a big cartoon silver gear standing on a post and a wooden base;
# clicking it opens the Settings menu (music / rain volume). The 3D "SETTINGS" title above it is a
# separate textify mesh (SM_SettingsTitle). Same style as decor.py: one atlas material, rounded
# boxes and lathed parts, closed shells, pivot at the bottom centre, the gear's face towards -Y.
#   exec(open(r"<skills>/blender-game-props/settings_gear.py").read())
#   build_settings_gear(out_dir)
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

exec(open(_skill("blender-game-props/decor.py")).read())

SILVER = S("r3", 24, 0.12, 0.4)       # silver grey
SILVER_D = S("r3", 24, 0.55, 0.9)     # dark steel
GEAR_R = 0.5          # disc radius (m)
GEAR_Z = 1.25         # gear centre height
TEETH = 12


def settings_gear(bm):
    # wooden base + metal post
    rbox(bm, (0, 0, 0.06), (0.8, 0.55, 0.12), WOOD_D, r=0.03)
    rbox(bm, (0, 0, 0.15), (0.62, 0.42, 0.08), WOOD, r=0.025)
    cyl(bm, (0, 0, 0.18), 0.075, GEAR_Z - 0.18, SILVER_D, segs=14)
    cyl(bm, (0, 0, 0.18), 0.12, 0.06, SILVER_D, segs=16)
    # the gear: built facing +Z, then turned to face -Y
    b = bmesh.new()
    cyl(b, (0, 0, -0.08), GEAR_R, 0.16, SILVER, segs=40, bevel=0.35)
    for k in range(TEETH):
        a = 2 * math.pi * k / TEETH
        # a tapered tooth: wide at the rim, narrower at the tip
        t = bmesh.new()
        rbox(t, (0, 0, 0), (0.2, 0.2, 0.16), SILVER, r=0.035)
        for v in t.verts:
            if v.co.x > 0:
                v.co.y *= 0.7
        _merge(b, t, (0, 0, math.degrees(a)), (math.cos(a) * (GEAR_R + 0.04), math.sin(a) * (GEAR_R + 0.04), 0))
    # a raised ring and a gold hub on both faces, six dark holes between them
    for side in (-1, 1):
        rot = None if side > 0 else (180, 0, 0)
        c = bmesh.new()
        ring(c, (0, 0, 0.08), 0.36, 0.035, SILVER_D, segs=36, rsegs=8)
        cyl(c, (0, 0, 0.05), 0.15, 0.06, GOLD, segs=24, bevel=0.5)
        cyl(c, (0, 0, 0.1), 0.06, 0.025, SILVER_D, segs=16, bevel=0.5)
        for k in range(6):
            a = 2 * math.pi * (k + 0.5) / 6
            cyl(c, (math.cos(a) * 0.255, math.sin(a) * 0.255, 0.075), 0.07, 0.012, SILVER_D, segs=16, bevel=0.3)
        _merge(b, c, rot)
    _merge(bm, b, (90, 0, 0), (0, 0, GEAR_Z))


def build_settings_gear(out_dir=None):
    mat = bpy.data.materials["M_GradientTexture"]
    coll = bpy.data.collections.get("SettingsStation") or bpy.data.collections.new("SettingsStation")
    if coll.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(coll)
    old = bpy.data.objects.get("SM_SettingsGear")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    bm = bmesh.new()
    settings_gear(bm)
    me = bpy.data.meshes.new("SM_SettingsGear")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new("SM_SettingsGear", me)
    coll.objects.link(o)
    o.location = (0, -320, 0)
    res = {"faces": len(me.polygons), "open": _open_edges(o), "dims": [round(d, 2) for d in o.dimensions]}
    if out_dir:
        exec(open(_skill("blender-game-props/blender_helpers.py")).read(), globals())
        export_fbx(o, out_dir + "/SM_SettingsGear.fbx")
    return res
