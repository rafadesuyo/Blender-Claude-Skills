---
name: blender-game-props
description: Use when making a 3D model / prop / mesh for one of Dante's games (UEFN / Fortnite, Roblox, Unity) through the Blender MCP, or when importing a Blender model into a game project. Covers his low-poly cartoon style, the bmesh build recipe, flat color materials, FBX export settings and the UEFN import and placement steps.
---

> **Paths:** `<skills>` in this file and in the script comments means the folder that holds the skill
> folders, i.e. the parent of this skill's base directory (`~/.claude/skills` for a manual install, the
> plugin's `skills` folder for a plugin install). Swap in the real absolute path when you run
> `exec(open(...).read())` in `execute_blender_code`. Scripts find their sibling files on their own.

# Game props in Blender (Dante's projects)

Dante builds bright, cartoony, stylized games (Fortnite UEFN tycoons, Roblox, Unity). Props are made
in Blender through the Blender MCP (`execute_blender_code`), exported to FBX and imported into the
game. Follow this recipe so every model matches the game's look and arrives at the right size.

## 1. Look before you build

- If the prop is based on something that exists in the game (a UI icon, another model), look at it
  first. For UEFN textures: `EditorAppToolset.OpenEditorForAsset` + `CaptureEditorImage`; icon PNG
  sources are often in the session scratchpad. Copy its palette and shapes (the gab cash stacks
  copied the cash icon: green bill bricks, a yellow band, dark edges).
- `get_objects_summary` first. Never delete or change what's already in his scene: put new work in
  its own collection (e.g. `CashStacks`), hide (don't delete) the default cube.

## 2. Style rules

- **Low poly, but not blocky.** Box shapes with a 1-segment chamfer (`bmesh.ops.bevel`, offset
  ~1-2% of the size) catch light and read as "toy-like". Small detail by insets
  (`inset_individual`), not by subdividing. Budgets that looked right: a small prop 150-700 faces,
  a big pile ~2000, a 7.6 m table ~1100.
- **Flat shading** (`use_smooth = False`), **flat colors**, one material per color slot, no
  textures unless asked. Bright saturated colors; a darker shade of the same hue for sides /
  undersides; an almost-black shade on chamfers works like a cartoon outline.
- **Charm through irregularity:** small random yaw (±3-10°) and offset jitter when stacking
  repeated pieces, slightly uneven plank lengths/heights. Seed `random` so rebuilds are stable.
- **Sizes tell the story:** variants of one item (small / medium / huge) should differ clearly in
  silhouette (a few pieces / a pyramid / a tall heap), not just in scale.
- **Pivot at bottom center**, model standing on Z = 0, so it sits on floors and spins around its
  own center in game.
- Build in meters in Blender at real-world size (a bill brick 0.6 x 0.28 x 0.12, a counter 0.9 m
  high).

## 3. Build with bmesh

Use the helpers in `blender_helpers.py` (next to this file): load them with
`exec(open(r"<skills>/blender-game-props/blender_helpers.py").read())` inside
`execute_blender_code`, then:

```python
M = flat_materials({"Top": "5BE84A", "Side": "1E9C3A", "Edge": "0E4A2A"})  # name -> hex (sRGB)
bm = bmesh.new()
add_box(bm, center=(0, 0, 0.06), size=(0.6, 0.28, 0.12), mat=0, bevel=0.014)
# or build one piece (piece_mesh) and stamp copies with stamp(bm, piece, [(x, y, z, yaw), ...])
ob = bm_to_object(bm, "SM_MyProp", M, collection="MyProps")
```

`add_box` can color faces by normal (`top_mat`, `side_mat`, `edge_mat`) so chamfers get the
outline color. After building, set the viewport to Material Preview and take a
`get_screenshot_of_area_as_image("VIEW_3D")` to check the look before exporting. Show Dante a
screenshot when the look is a judgment call.

## 4. Export to FBX

`export_fbx(ob, path)` from the helpers. It zeroes the object's location, **scales it x100 for
the export** and restores it. Settings: `use_selection=True`, `apply_unit_scale=True`,
`apply_scale_options='FBX_SCALE_ALL'`, `axis_forward='-Y'`, `axis_up='Z'`, `mesh_smooth_type='FACE'`,
no leaf bones, no animation. Put files in the session scratchpad (e.g. `scratchpad/<thing>/`).

Why x100: exported at plain meters, UEFN imported the gab cash stacks 100x too small (0.37 cm
tall). With the x100 they came in at the right centimeters. **Always check bounds after import**
(below); if a project's scene units differ, adjust.

## 5. Import into UEFN

From the UEFN programmatic toolset (see `uefn_import.py` for a ready script):

1. `StaticMeshTools.import_file(folder_path, asset_name, source_file, import_materials=True)`.
   Each Blender material becomes a slot and a flat-color material asset with the same name.
2. `StaticMeshTools.get_bounds` must show centimeters at the intended size, and
   `get_material_slots` the expected slot names.
3. `import_file` can't overwrite. To redo a mesh, delete the old asset (only if nothing references
   it) and import under a **new name** (re-importing the same name after a delete fails).
4. `save_assets`, and `BuildAll` before the mesh is used from Verse. Meshes in a nested folder
   (e.g. `Meshes/Store`) need `Store<public> := module{}` in a `.verse` file in the parent folder
   (`Meshes/module_access.verse`) before Verse can see `Meshes.Store.SM_X`.
5. In Verse each slot is a field named after the Blender material (`set Mesh.M_CashTop = ...`), so
   name materials meaningfully. To tint or highlight a model at runtime, give it materials with
   parameters (gab: `M_StoreTint` with `Color` + `Highlight`) and set the slots from Verse.
6. Collision: imported meshes may block players. `remove_collisions` for decor that should not be
   solid (titles, props on tables); `generate_convex_collisions` if a raycast must hit it.

**Placing it:** a scene-graph entity (`EntityToolset.CreateEntity` + `AddComponent` with
`/<project>/_Verse/Assets.Meshes-<Folder>-<Mesh>`) when Verse needs to drive it, or a plain actor
(`SceneTools.add_to_scene_from_asset` + `ActorTools.set_label`) for static scenery. Check the result
with `EditorAppToolset.CaptureViewport` from where a player would stand, and fix overlaps (titles,
rocks, fences) before calling it done. FBX front (Blender -Y) ended up facing the opposite way in
UEFN once; check which side faces the player and rotate 180° if needed.

Then follow the project's own rules (for Dante's UEFN projects: build, then a FULL push).

## 6. Other engines

- **Roblox:** import FBX/OBJ through Studio; 1 stud ≈ 28 cm (0.28 m), so scale accordingly and
  check the part size after import. Keep props as MeshParts with flat colors.
- **Unity:** FBX at meters imports 1:1 (scale factor 1 with "Apply Transform"); no x100 needed.
These two are not yet verified in his projects: check the size after the first import and update
this section.

## 7. Always: closed shapes + outward normals (Dante: "be careful with face orientation")

Engines hide back faces, so an open tube end, a single-sided leaf or an inside-out piece shows as
a hole or vanishes from one side. Every piece must be a CLOSED shell with normals pointing out:
cap tube/lathe ends with quads (`quad_cap`: strips across an even ring, no n-gon or fan), build
leaves/fronds as thin closed slabs (bmesh.ops.solidify silently did nothing on them), and before
merging each piece run `orient_outward` (recalc normals, then flip if the signed volume is
negative). Finish with `check_closed(objs)` from gradient_trees.py: 0 open edges and 0 inside-out
parts on every model, and report the numbers. Flat single-sided cards are only OK if the engine
material is two-sided, and then say so.

## 8. Topology

For quad topology, n-gon/tri cleanup, remeshing, or models Dante wants to SELL, use the
`blender-clean-topology` skill (topo_check / topo_clean / quad_cylinder / grid_cap).

## Lessons log (add new ones here)

- 2026-10-23 gab: cash stacks (small/medium/large) and a 7.6 m market counter built this way; x100
  export fix; front of the counter faced away once (rotated yaw -90 instead of 90).
- 2026-10-23 gab: market stall from a reference image (counter with plank front, 3 tilted empty
  crate trays, posts, sloped cream canvas awning with a scalloped edge), 1,196 faces, 3 x 2.7 m.
  Built to match the reference first, then one mesh reused at different scales (0.95 / 1.05 /
  1.25) for variety. Posts that poke through a sloped roof: clamp their top verts under it.
  Placed as entities (mesh + area_gate) so they can be hidden until unlocked; yaw -90 faces the
  front (Blender -Y) toward world -Y.
- 2026-10-23 gab, feedback on that stall: "colors look dull, the top is just white, it looks
  dead". Big surfaces must not be plain white/cream: use bold alternating stripes (color + cream).
  Hanging decorations (scalloped valance) must read as ONE connected piece: build each scallop as
  an extruded outline (rectangle + half circle, radius = half its width so neighbours touch),
  flush under the edge, plus a trim strip where it's sewn on. Give the accent color its own
  material slot (M_StallStripe) and let a Verse component pick it from an enum per placed copy
  (gab market_stall.StripeColor: Red / Green / Blue ...), so colors are easy to change.
- 2026-10-23: his props live in `~\Desktop\farm tools.blend`. Keep it organized:
  numbered top collections (`01 Crops` > `Tree (5 growth stages)`, `02 Premium Store` > `Cash
  Packs` / `Market Stall`, `99 Archive (old, not in game)` hidden), each set in its own row, then
  `bpy.data.orphans_purge()` and save. Put new props in the right numbered collection.
- 2026-10-23 tree (special crop, 5 stages like the other crops = CropGrowthStages): sprout in a
  soil mound -> sapling -> young tree -> grown tree -> fruiting tree with red apples. Canopy =
  jittered icospheres (subdivisions=2; 1 is too faceted), two greens by face height; tapered
  bent 7-8 sided trunk in one bark color (alternating bark colors per face looked patchy) +
  tetra root flares. 44 -> 1,742 faces across the stages.
- 2026-10-23 CROP STYLE (gab crops come from `~\Desktop\Farm\Crops\
  NewLuaStudios_StylizedFarmPack01_Blender.blend`): crops must match that pack, NOT the flat-color
  style above. One material for everything, `M_GradientTexture` = a packed 2048 gradient atlas
  (`GradientTexture.png`): 36 vertical gradient columns 57 px wide in the top row (v 0.845-0.998)
  plus 6 in a second row (v 0.69-0.842). Each part is UV'd into ONE column (u = column center,
  v = the part's height mapped onto the column) so it fades along its length; SMOOTH shading;
  mostly quads (Dante wants quads, not triangle-capped spheres: use quad-spheres = subdivided cube
  normalized, open tubes without caps). Naming: `SM_X_Seed` (the shared seed-dots mesh),
  `SM_X_Stage1..4`, `SM_X` = harvested item. Sizes: Stage4 0.5-1.9 m tall, item 0.2-0.8 m.
  Useful columns: bark row2 col2 (u 0.0418) v 0.69-0.79; leaf green col9 (u 0.2644) v 0.85-0.995;
  red col6 (u 0.1809); dark brown col35 (u 0.988). Get the real material by
  `bpy.data.libraries.load(pack)` of an object (mesh datablock names differ from object names).
  Background Blender: "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b file
  --python script.py (the MCP _for_cli tools can't find blender). The MCP connects to ONE Blender
  window; another open window can't be driven, and writing to a file open+dirty there gets lost.
- 2026-10-23 trees in that pack: `gradient_trees.py` (next to this file) builds 8 fruit-tree types
  (Apple, Orange, Lemon, Cherry, Pear, Coconut palm, Plum, Peach) x Stage1-4 + fruit item, all
  quads, into `Trees > Tree_<Type>`; any fruit function works on any shape (swap in TYPES).
  Dante: trees must be clearly BIGGER than the plants (Stage4 ~3 m vs plants <= 1.9 m) because
  they take a big slot in game; final-stage fruit radius 0.15 m (small fruit read as "tiny and
  shiny"). Palm fronds: positive tilt + negative droop so they hang. Preview with an ortho
  camera render of just the Stage4s (viewport shots from far away are useless).
- 2026-10-23 seasonal trees in gradient_trees.py: Halloween (gnarled twisting near-black purple
  trunk + roots + clawed branches, hanging jack-o'-lanterns whose face is carved by picking cells
  on the cube grid BEFORE spherifying, UV'd to the bright yellow end of col23) and Christmas
  (lathe-built pine tiers with spiky skirts, two crossed quad-kite gold stars so it reads from any
  side, gift-box "fruit" in 6 colors with gold/white ribbons + bow, some under the tree).
- 2026-10-23 lamp posts (`lamp_posts.py`, collection `LampPosts` in the pack file): built from his
  reference sheet. Boxes stay flat-shaded, round parts smooth (`smooth_round_parts`: islands of
  6 faces = boxes). Glowing parts go in a 2nd material slot `M_LanternGlow` (emissive) so the
  engine can light them; keep EEVEE emission ~2.5 or it renders white. Decorations that read
  from one side (jack-o'-lantern face, banners) must face the FRONT (-Y), check in a render.
- 2026-10-23 fences (`fences.py`, collection `Fences > Fence_<Name>`): 14 designs from his sheet
  (no rope ones; he didn't want them). MODULAR RULE for barn customisation: `SM_Fence_<Name>` =
  2 m segment with its post at x=0 and rails/wall to x=2 (ends exactly where the next post
  starts, walls fill exactly 0..2 so neighbours meet flush), `SM_Fence_<Name>_Post` closes the
  run; pivot at the start post base, runs +X, front -Y, so every design swaps onto the same
  spots and corners work by rotating 90 deg around a post. Preview = 2 segments + end post + a
  90 deg corner per design.
- ATLAS EXTENDED 2026-10-23 (the pack had no neutral grey / black / cream): added 4 strips in
  EMPTY space of the second row, columns 6-9, v 0.680-0.830 (existing strips end at v 0.8335 —
  measure before writing; my first try overlapped 3 px rows and I had to restore from a copy of
  the saved .blend): col6 grey stone, col7 black iron, col8 light warm stone, col9 cream paint.
  Use v 0.685-0.825 for them. Verify 0 pixels changed outside the new strips. A PNG copy is in
  the session scratchpad (GradientTexture_v2.png); UEFN's copy of the atlas must be replaced
  before importing anything that uses these strips. You can't libraries.load from the open file
  itself: copy the .blend first.
- 2026-10-23 daily-reward trees (`daily_trees.py`, `DailyRewards > DR_<nn>_<Name>`): 30 from his
  sheet, one lush shape (chunky trunk + roots, round canopy of puffs covered in `surface_leaf`
  scales, grassy mound with rocks) + per-tree canopy colour and fruit kind. Each tree has its own
  canopy + fruit gradient strip in reserved atlas bands (rows 1040-1340 canopy, 712-1012 fruit,
  column = tree index; rainbow / galaxy = multi-stop). Glowing fruit = slot 1 `M_GradientGlow`
  (same atlas, emissive) so each glows in its own colour. Lessons from his reference: canopies
  round and leafy (not flat mushroom puffs), leaves must LIE ON the puffs (radial blades read as
  whiskers), fruit big (r 0.24) on the outside facing the front, every flat fruit built facing -Y
  then turned to face outward (`add_fruit(..., facing)`). Stage4 is 3-7k faces.
- 2026-10-23 his follow-up on those trees: NO leaf cards/petals on the canopy blobs ("look so
  weird"), smooth blobs only. Trunks must CURVE (one smooth bend, ~10 rings), never zig-zag; the
  corkscrew look came from tube() re-aiming every ring with to_track_quat — tube() now carries the
  ring frame along the path (parallel transport), so rebuild old tube-made models to get it.
  Fruit must contrast with its canopy: darken the canopy / brighten the fruit, and run the
  lightness + colour-distance check in the session (flag dL < 0.15 and dRGB < 0.35).
- 2026-10-23 season symbols (`seasons.py`, collection `Seasons`, SM_Season_Spring/Summer/Autumn/
  Winter): chunky faceted icons from his sheet. `slab(outline)` = 2D even-count outline extruded
  along Y with a domed front/back (rim -> inner ring -> quad fan to a centre point): all quads,
  closed, FLAT shaded (faceted icon look, unlike the smooth crops). Colours in canopy-band columns
  30-35 of the atlas (pink, leaf green, sun yellow, maple, stem brown, ice).
- 2026-10-24 pack props into gab: everything lives in `/gab/FarmProps/{Trees/<Type>, DailyRewards/
  <DR_xx_Name>, Fences/<Name>, LampPosts, Seasons, Materials}`, with a `module_access.verse` per
  folder that has subfolders. Import with `import_materials=False`, then `set_material` per slot:
  M_GradientTexture -> `/gab/Crops/M_Crops` (now samples `/gab/Crops/GradientTexture_v3`; a new
  atlas = import under a new name + repoint M_Crops' TextureSample_0), M_GradientGlow /
  M_LanternGlow -> `/gab/FarmProps/Materials/`. Export the whole set from the open pack window in
  one `execute_blender_code` call (manifest.json of folder + name), then import in batches of
  <=100 meshes (~2 s each). Fence segments run along UE +Y after import (FBX -Y forward).
- 2026-10-24 cute fences set 2 (`fences2.py`, same `Fences` collection + convention): 20 designs
  from sheet 48 (hearts, bows, tulips, roses, stars, wisteria, hydrangea, mushrooms, log stumps,
  balustrade, rainbow cloud...). New helpers there: `slab` (domed 2D outline), `heart_pts`,
  `star_pts`, `holed` (plate with a real cut-out: rays from the hole centre pair hole and outer
  points, outer corners added, all quads), `band` (rect bar along an XZ path: arches, scrollwork
  spirals), `revolve`, `torus` (rope wraps), `lattice` (clipped diagonals), `ivy`, `flat_flower`,
  `glow(fn)` (marks a part slot 1). Lessons: holes hidden behind a rail don't read (keep cut-outs
  above the rails); vivid atlas purples/reds look harsh, use the pale ends (col29 v .965+ lavender,
  col15 v .955+ pale blue-grey); LIGHT_STONE reads grey in renders, use CREAM for "cream" posts.
  Icons: scratchpad fence/render_icons2.py (only.txt list) also writes a contact sheet.
- 2026-10-24 entrance gates (`gates.py`, collection `Gates`): 9 arches from sheet 49, pivot at the
  CENTRE of the opening (not the fence start-post rule), front -Y, pillars at x = +-1.7, ~4.4 m
  wide x 2.5-4.3 m tall before the game's x1.5. Imported flat into /gab/FarmProps/Gates. The
  name-sign gate keeps a blank board: gab writes "<owner>'s Farm" with a billboard device placed
  in front of it (show border off, transparent background, two-sided, outline Thick); the editor
  viewport does not draw billboard text, so it can only be checked in game.
- 2026-10-24 gates set 2 (`gates2.py`): Christmas x3, Halloween x2, blossom heart, ranch skull,
  nautical, torii. The sheet's gates have CLOSED double doors; an entrance must stay walkable, so
  `open_doors` builds the two leaves swung back 72 deg into the base (+Y). Seasonal gates are
  tagged in gab's gates.verse (GetGateSpecial) for a later index / event unlock.
- 2026-10-24 NO Z-FIGHTING, EVER (Dante: "don't let it happen ever"). Every model must pass
  `zfight(obj)` from `zfight_check.py` (0 hits) next to `check_closed` BEFORE export: it finds faces
  of different parts in one plane facing the same way that overlap (> 1 cm2; ground faces skipped).
  Rules that keep it at 0: walls stop where gables/roofs start (never overlap them); trims, frames,
  posts sit 4+ mm proud or recessed of the surface they are on; frame bars BUTT (top/bottom full
  width, sides between them, different depths); crossing beams / X braces / spokes each at their
  own depth; parts that touch end to end (arch stones, roof halves, neighbouring rows) alternate
  depth or width by >= 6 mm; rails end inside stiles, not flush with them; same-height tops of
  neighbouring boxes are offset; flat buildings are flat-shaded (smooth shading made dark
  gradients on big slabs). Replacing an asset already in UEFN (import_file can't overwrite):
  import into /gab/_Reimport/<same sub-path>, set materials, delete the originals, save, then move
  each back to its original path (in batches of ~30; a call over 10 min times out), BuildAll,
  re-add any level entity mesh component that the delete dropped, delete /gab/_Reimport.
- 2026-10-25 COLLISION for enterable models (barns, shops, gates, arches): UEFN's import gives one
  convex hull around the whole mesh, which seals doorways ("i cant enter"). Right after import set
  the mesh's BodySetup `collisionTraceFlag` = `CTF_UseComplexAsSimple` (ObjectTools.set_properties
  on `<mesh>.<mesh>:BodySetup_0`; it passes push validation). Check with SceneTools.trace_world
  through the doorway (should reach the back wall) and beside it (should hit the front wall).
- 2026-10-26 Meccha2 lobby shop signs (`Meccha2/SourceArt/ShopSigns.blend`, collection `ShopSigns`):
  curved wooden plank plaque (dark frame board + 2-3 planks at alternating depths + nails) bent on
  the SAME cylinder radius as the 3DTextify text lines (bisect every 10 cm, then wrap), a themed
  prop on top (backpack, shield + trophy + crown, gears + wrench, crown, coin + coin stacks,
  t-shirt on a hanger, gift box), text joined in front, one mesh per sign. Props are built at
  1x and scaled about the plaque's top edge per sign (1.0-1.5) so they read from the lobby.
  Brown letters vanished on brown planks: give that sign pale birch planks. Stacked/side-by-side
  repeats (coin stacks, crossing hanger arms, ribbon strips, bow loops) were the z-fight sources.
  In UEFN the front faced local +X; remove_collisions for floating signs.
- 2026-10-29 dragon fruit (`dragon_fruit.py`, `build_dragon_fruit()`, saved in `Desktop\Farm\Crops\
  DragonFruit.blend`, collection `DragonFruit`): from his 7-stage sheet. SM_DragonFruit_Seed,
  Stage1 sprout .. Stage6 full grown (1.7 m, 4,438 faces; his budget "3-5k poly max"), item
  SM_DragonFruit + SM_DragonFruit_Half (cut face -Y). ONE material M_GradientTexture (atlas v3),
  100% quads, 0 z-fight. Builds on blender-clean-topology (grid_cap / quad_sphere / topo_check).
  Tricks: mature stems = flat 8-sided "pad" tubes (2 wings + ridge, scalloped radius, spines at
  the scallops) that arch out and droop; spines = tapered quad boxes (no tris); two colours on one
  part (pink bract with a lime tip) = `uv_split`: each FACE samples one strip, so no face spans two
  atlas columns (per-vertex mixing smears the whole atlas between). Fine-tune colours in Material
  Preview: the stake looked orange with r2 col1, soil looked pale until t 0.55-1.0.
- 2026-11-02 premium candy crops (`premium_crops.py`, `build_premium()`, in `Desktop\Farm\Crops\
  DragonFruit.blend` > `PremiumCrops` > one collection per crop): ChocolateBar, WhiteChocolate,
  Truffle, Lollipop, CandyCane, LavaPlant, CottonCandy, PinkCloud, RainbowTruffle, each
  `SM_<Crop>_Seed`, `_Stage1..6` + item `SM_<Crop>`; 72 models, 100% quads, closed, 0 z-fight,
  Stage6 2.9-4.9k faces. Builds on dragon_fruit.py. New tricks: `tube2(..., twist)` turns each
  ring so faces follow a helix, so colouring by side index gives smooth candy stripes (canes,
  swirl-rope lollipops, paper sticks); `uv_pick` / `stripes` pick a strip per face. Lessons:
  bevel bigger than half a box's depth doubles verts; two parts starting at (0,0,0) (trunk cap +
  mound cap) double verts, so start stems inside the mound; a trim's top level with a
  neighbouring box top z-fights, so end it in a gap; side stems at yaw 2.1 and 4.3 both land on
  the LEFT in a front view (use ~2.5 and ~5.5); neighbouring petals need different tilts.
  Preview without lights is black: temp sun + ortho camera, then remove them and restore world.
- 2026-11-04 gab: `quest_booth.py` builds SM_BarnNameSign and SM_QuestBooth. SM_BarnNameSign is a hanging sign in BARN-LOCAL coordinates, so one mesh fits all 9 barn designs. It's placed at the identity transform as a child of the barn entity and stays under the gable decorations. SM_QuestBooth is a thin stall with a notice board, a striped awning and a title board. Textify titles go on top as separate meshes (front +X after import).
- 2026-11-04 grass (UEFN): `grass/SourceArt/grass_kit.py` = flat-colour low-poly map kit (cottage, picket + wood fences, road, cone, round/pine trees, bushes, flowers, mailbox, bench, step stone, 2 m grass tuft of 3-sided two-tone blades, burlap grass bag). UEFN import gives 3 auto LODs AND per-quality Min LOD 2 on Low/Medium: thin blades vanished and a tree LOD dropped a material section (canopy went brown). For small low-poly kits: StaticMeshToolset.RemoveLods + SetQualityLevelMinLod {Low,Medium,High,Epic: -1} + default 0 (validation only warns). Import axes: Blender +X -> UE -Y, Blender -Y (front) -> UE +X.
