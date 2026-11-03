# Blender Claude Skills

Two [Claude Code](https://claude.com/claude-code) skills for making game-ready, low-poly models in Blender through the Blender MCP.

| Skill | What it does |
|---|---|
| `blender-game-props` | Low-poly cartoon props for UEFN / Roblox / Unity: bmesh build recipe, flat-colour or gradient-atlas materials, z-fighting check, FBX export and UEFN import steps, plus a library of prop scripts (fences, gates, barns, trees, crops, decor, guns, villagers...). |
| `blender-clean-topology` | Clean quad topology: `topo_check` report (and selects the problems), `topo_clean` auto-fix, QuadriFlow / voxel remesh and a checklist for selling a model. |

## Install

1. Install Blender (made with 5.1) and enable the **Blender MCP** add-on so Claude can connect to Blender.
2. Copy both folders from `skills/` into your Claude skills folder:
   - Windows: `%USERPROFILE%\.claude\skills\`
   - macOS / Linux: `~/.claude/skills/`
3. Restart Claude Code. Then just ask for things like "make a low-poly wooden fence for my Roblox game" or "check this mesh's topology".

The scripts load each other from `~/.claude/skills/...`, so keep the folder names as they are.

## Notes

- The farm / crop scripts (`dragon_fruit.py`, `premium_crops.py`, `gradient_trees.py`...) use a gradient-atlas material in the style of a paid asset pack. The atlas texture is **not** included. Use your own gradient texture: set the `GRADIENT_ATLAS` environment variable to its path, or swap in flat-colour materials (the default style in `blender-game-props`).
- `SKILL.md` in `blender-game-props` has a project log at the bottom with notes from Dante's own games. File paths there (`~\Desktop\...`) point to files you won't have; the rules and recipes still apply.
