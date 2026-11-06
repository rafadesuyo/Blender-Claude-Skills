---
name: blender-clean-topology
description: Use when a Blender model needs clean, quad topology, when Dante says a mesh "came out weird", has bad topology / n-gons / triangles, needs retopology or remeshing, or is meant to be SOLD (Fab, CGTrader, Sketchfab, itch). Covers quad-first modeling rules, the topo_check report (+ selecting problems), the topo_clean auto-fix, QuadriFlow / voxel remesh for organic meshes and a sellable-asset export checklist. Works through the Blender MCP; pairs with blender-game-props.
---

> **Paths:** `<skills>` in this file and in the script comments means the folder that holds the skill
> folders, i.e. the parent of this skill's base directory (`~/.claude/skills` for a manual install, the
> plugin's `skills` folder for a plugin install). Swap in the real absolute path when you run
> `exec(open(...).read())` in `execute_blender_code`. Scripts find their sibling files on their own.

# Clean topology in Blender (Dante's models)

Dante models with Claude through the Blender MCP and wants some models good enough to **sell**.
Buyers open the wireframe: n-gons, tri fans, doubled verts and flipped faces look amateur and
break subdivision, UVs and rigging. Rule: **build quads from the start, check before every
export, auto-clean what's left, remesh only organic shapes.**

Load the scripts (next to this file) inside `execute_blender_code`:

```python
D = r"<skills>/blender-clean-topology"
for f in ("quad_build.py", "topo_check.py", "topo_clean.py"):
    exec(open(D + "/" + f).read())
```

## 1. Decide the target first

| Target | When | Rules |
|---|---|---|
| `"quad"` | models to sell, anything that gets a Subdivision modifier, rigs/characters, sculpt bases | 0 n-gons, tris ≤ 2% and only on flat hidden spots, few 6+ poles, closed, UV'd |
| `"game"` | Dante's own UEFN/Roblox/Unity props (blender-game-props) | tris are fine (engines triangulate), still 0 n-gons, 0 holes, 0 doubles, normals out |

Sellable models usually get both: a quad "source" mesh plus the game-ready (triangulated or
low-poly) version, so check with `target="quad"`.

## 2. Build quad-first (prevents 90% of problems)

What made his meshes weird, and what to do instead:

| Don't | Do |
|---|---|
| Boolean cuts (`bmesh.ops` / Boolean modifier) → n-gons, slivers, stray verts | Cut holes from the topology: inset a face, then extrude/delete inward, or add loop cuts around the hole first. If a boolean is unavoidable, apply it then run `topo_clean` and fix by hand |
| `create_cone` / `create_circle` with n-gon or tri-fan caps | `quad_cylinder(r, h, sides=16, cap="grid")`, or `grid_cap(b, ring)` on any ring of 4k verts |
| `create_uvsphere` (tri fans at both poles, 16-valence poles) | `quad_sphere(r, cuts=3)` (subdivided cube) |
| Bevel with `segments=1` on boxes → corner triangles | `quad_box(size, cuts, bevel)` (2 segments: corners = 3 quads) |
| Inset/extrude on n-gons, fans of faces meeting in one vert | Keep sides as multiples of 4 so caps and insets can be quad-filled |
| Separate parts that overlap/intersect (z-fight, invisible faces) | Fine for game props (keep each part closed), but for "quad" models merge them properly or keep them as clearly separate closed parts |
| `dissolve_limit` / "Limited Dissolve" to reduce faces → huge n-gons | Remove edge LOOPS (`dissolve_edges` on a whole loop) or decimate a copy |
| Ring counts that don't match between joined parts → tris/n-gons at the seam | Plan matching vert counts (8 → 16 → 32) and use 2→1 / 3→1 reduction quads |

Good topology habits: edge loops follow the shape (around eyes, mouths, joints, rims), quads
roughly square, poles (3 or 5 edges) placed on flat areas not on curves, support loops near
hard edges when a Subdivision modifier is used (or `quad_cylinder(..., bevel=...)`).

## 3. Check: `topo_check`

```python
r = topo_check(obj, target="quad")       # full dict
r["verdict"], r["errors"], r["warnings"]  # "CLEAN" | "OK (warnings)" | "FIX"
topo_report(objs, target="game")          # short report for several objects
topo_check(obj, select=True)              # also selects every problem in Edit Mode
```

Reports: faces / tris / quads / n-gons / quad %, poles (5 and 6+), open, non-manifold and wire
edges, loose and doubled verts, flipped faces (edge-direction test) and inside-out parts,
zero-area faces, sliver triangles, folded quads, UV layers and collapsed UVs, unapplied
transforms and modifiers, empty material slots, and the tri count after triangulation (the
number to put on a store page). **Always report the verdict to Dante with the numbers**, and
with `select=True` take a viewport screenshot so he can see where the problems are.

## 4. Fix: `topo_clean` (keeps shape and UVs)

```python
new, before, after = topo_clean(obj)            # works on a COPY "<name>_clean"; original hidden
topo_clean(obj, in_place=True)                  # only when Dante asked to change it directly
```

Steps: merge by distance (0.1 mm) → dissolve degenerate → delete loose → **tri fans → quad
caps** (`fix_fans`: UV-sphere poles, flat poked caps; steep points like cone tips are kept,
a sharp tip needs its pole) → **n-gons → quads** (`ngons_to_quads`: convex planar caps get a
grid cap if 4k verts, strips if even, else beauty-triangulate + join) → **tris → quads**
(`join_triangles`, 40°, respecting seams, sharp edges, UVs and materials) → normals outward per
part. Whatever stays in `after["errors"]` needs a hand fix (usually odd-count caps or boolean
leftovers): select it with `topo_check(..., select=True)` and fix it, or remesh if it's organic.

Tested 2026-10-29: n-gon capped cylinder + UV sphere + tri-capped cone + doubled face + flipped
face → 100% quads except the 12-tri cone point, shape and size unchanged.

## 5. Remesh: organic shapes only

```python
new, report = remesh(obj, "quadriflow", faces=4000)        # clean, manifold input
new, report = remesh(obj, "voxel+quadriflow", faces=4000)  # messy / AI / scan / sculpt input
```

Works on a copy (`<name>_retopo`). Throws away UVs, per-face materials and exact edges, so use it
for creatures, characters, rocks, food, plants, sculpts, AI-generated meshes. **Never** for
hard-surface props (crates, furniture, weapons, buildings): those get rebuilt quad-first or
cleaned. After remeshing: re-UV (Smart UV Project at minimum, real seams for sale), re-assign
materials, then `topo_check`. For detail, bake normals from the original onto the remesh.

QuadriFlow notes (found while testing): it refuses meshes that aren't perfectly manifold, and
sometimes a clean multi-part mesh; `remesh` falls back to remeshing each loose part and joining
them, and after a voxel pass merges the tiny edges voxels leave at sharp tips. It raises instead
of silently leaving the mesh unchanged.

**Better free remeshers** (installed by Dante, not by Claude): **QRemeshify** (free on
ksami.gumroad.com, QuadWild-based, edge flow guided by seams/sharp edges, N-panel, Blender 4.2+,
keep input < 100k tris) and **Instant Meshes** (standalone). QRemeshify was NOT installed on
2026-10-29; when it is, list its ops (`dir(bpy.ops.qremeshify)`, `get_rna_type()`) and wire the
call into `remesh(..., "qremeshify")`. Paid best-in-class: Quad Remesher (~$79).

## 6. Sellable export checklist

Before calling a model ready to sell, all of these:
1. `topo_check(obj, "quad")` verdict CLEAN or only justified warnings (state them).
2. Real-world scale in meters, transforms applied (`bpy.ops.object.transform_apply`), pivot
   at bottom center (or where it would be used), facing -Y (Blender front).
3. Non-overlapping UVs on every mesh, no collapsed UVs, sensible seams (hidden spots), texel
   density even. UVs unwrapped AFTER the final topology.
4. Clean names: `SM_<Name>` objects, `M_<Name>_<Part>` materials, no `Cube.003`, no empty slots,
   orphans purged (`bpy.data.orphans_purge()`).
5. Modifiers either applied or listed (a Subdivision level stays live in the .blend version).
6. Exports: .blend + FBX (+ OBJ / glTF if the store asks), each re-opened to confirm.
7. Store-page numbers from the report: quads/faces, verts, `tris_if_triangulated`.
8. Preview renders: beauty shot + wireframe shot (buyers check the wireframe).
9. Run `zfight_check.py` (blender-game-props) too: 0 overlapping faces.

## Lessons log (add new ones here)

- 2026-10-29: skill created and tested on a scratch scene. `hasattr(bpy.ops, "x")` is always
  True (use `dir(bpy.ops.x)`); QuadriFlow rejects voxel output with sub-mm edges at sharp tips.
- 2026-10-29 dragon fruit crop (blender-game-props/dragon_fruit.py) was the first real use: 9
  models, 100% quads. Spikes/thorns as tapered boxes (tiny quad tip) instead of pyramids keep the
  quad target clean. Helpers are exec'd into ONE namespace: private names must be unique per file
  (topo_check's `_islands` was overwritten by zfight_check's; it is `_tc_islands` now).
