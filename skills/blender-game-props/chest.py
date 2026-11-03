# Storage chest (gab, player's barn) in the NewLua pack style: a flat, boxy wooden chest (Dante: no
# round / domed shapes, no purple) with three planks a side, flat dark-wood corner boards and plinth,
# black iron straps running up the front and over the flat lid, and a small iron handle (opened by
# hand: no lock). Two meshes so the game can swing the lid open:
#   SM_Chest_Base  pivot at the bottom centre, front -Y, ~1.0 x 0.6 x 0.48 m
#   SM_Chest_Lid   pivot ON THE HINGE (the body's back top edge), so rotating it around its
#                         X axis opens it; closed it sits exactly on the body
#   exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/chest.py")).read())
#   build_chest()
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/gates2.py")).read())
exec(open(__import__("os").path.expanduser(r"~/.claude/skills/blender-game-props/mailbox.py")).read())

CH_WOOD = c1(1, 0.71, 0.775)        # warm orange-brown planks
CH_WOOD_L = c1(1, 0.73, 0.785)      # lighter planks (lid)
CH_TRIM = c1(2, 0.69, 0.75)         # darker wood corner boards
CH_SEAM = c1(2, 0.69, 0.71)         # plank seams
CH_IRON = c1(7, 0.70, 0.80)         # black iron straps and handle
CH_INSIDE = BARK_DARK               # the dark inside

W, D, H = 1.0, 0.6, 0.48            # body
LID_T = 0.1                          # lid thickness (flat lid)
FLAT = dict(cuts=1, power=16.0)     # crisp boxes with just a hint of a soft edge


def chest_body(bm):
    # the plank box
    rbox(bm, (0, 0, H / 2), (W - 0.03, D - 0.03, H), CH_WOOD, **FLAT)
    # three planks: thin grooves on every side
    for k in (1, 2):
        z = k * H / 3
        for sy in (-1, 1):
            rbox(bm, (0, sy * (D / 2 - 0.012), z), (W - 0.12, 0.012, 0.012), CH_SEAM, **FLAT)
        for sx in (-1, 1):
            rbox(bm, (sx * (W / 2 - 0.012), 0, z), (0.012, D - 0.12, 0.012), CH_SEAM, **FLAT)
    # flat corner boards, a plinth round the bottom
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(bm, (sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), H / 2), (0.075, 0.075, H + 0.004), CH_TRIM, **FLAT)
    rbox(bm, (0, 0, 0.03), (W + 0.02, D + 0.02, 0.06), CH_TRIM, **FLAT)
    # two iron straps up the front and the back
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(bm, (sx * W * 0.27, sy * (D / 2 + 0.002), H / 2 + 0.02), (0.07, 0.016, H - 0.04), CH_IRON, **FLAT)
    # the dark inside, seen when the lid is open
    rbox(bm, (0, 0, H - 0.004), (W - 0.12, D - 0.12, 0.012), CH_INSIDE, **FLAT)


def chest_lid(bm):
    # built with the hinge at the origin: the lid reaches forward (-Y) by D, its bottom at z = 0
    yc = -D / 2
    rbox(bm, (0, yc, LID_T / 2), (W + 0.02, D + 0.02, LID_T), CH_WOOD_L, **FLAT)
    # planks across the top
    for k in (-1, 1):
        rbox(bm, (k * W / 6, yc, LID_T + 0.001), (0.012, D - 0.04, 0.008), CH_SEAM, **FLAT)
    # dark wood edge band round the lid
    rbox(bm, (0, yc, 0.025), (W + 0.035, D + 0.035, 0.05), CH_TRIM, **FLAT)
    # the iron straps carry on over the top and down the front edge
    for sx in (-1, 1):
        rbox(bm, (sx * W * 0.27, yc, LID_T + 0.004), (0.07, D + 0.035, 0.012), CH_IRON, **FLAT)
        rbox(bm, (sx * W * 0.27, -D - 0.02, LID_T / 2), (0.07, 0.014, LID_T + 0.012), CH_IRON, **FLAT)
    # a small iron handle on the front, to lift it by hand
    hy = -D - 0.04
    rbox(bm, (0, hy - 0.012, 0.045), (0.2, 0.022, 0.026), CH_IRON, **FLAT)
    for sx in (-1, 1):
        rbox(bm, (sx * 0.09, hy + 0.006, 0.045), (0.024, 0.04, 0.04), CH_IRON, **FLAT)


def build_chest():
    mat = bpy.data.materials["M_GradientTexture"]
    coll = bpy.data.collections.get("StorageChest")
    if coll is None:
        coll = bpy.data.collections.new("StorageChest")
        bpy.context.scene.collection.children.link(coll)
    bm = bmesh.new()
    chest_body(bm)
    base = finish(bm, "SM_Chest_Base", coll, (0, 0, 0), mat)
    bm = bmesh.new()
    chest_lid(bm)
    # hinge = the body's back top edge
    lid = finish(bm, "SM_Chest_Lid", coll, (0, D / 2, H), mat)
    # flat shaded: crisp, carpentered edges (smooth shading made the boxes look puffy)
    for o in (base, lid):
        for p in o.data.polygons:
            p.use_smooth = False
    return base, lid
