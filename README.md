# Blender Claude Skills

Two [Claude Code](https://claude.com/claude-code) skills for making game-ready, low-poly models in Blender through the Blender MCP.

| Skill | What it does |
|---|---|
| `blender-game-props` | Low-poly cartoon props for UEFN / Roblox / Unity: bmesh build recipe, flat-colour or gradient-atlas materials, z-fighting check, FBX export and UEFN import steps, plus a library of prop scripts (fences, gates, barns, trees, crops, decor, guns, villagers...). |
| `blender-clean-topology` | Clean quad topology: `topo_check` report (and selects the problems), `topo_clean` auto-fix, QuadriFlow / voxel remesh and a checklist for selling a model. |

## Before you start

Install Blender (made with 5.1) and turn on the **Blender MCP** add-on so Claude can connect to Blender. These skills run in **Claude Code** (the terminal app, or the Code tab of the Claude desktop app), because they control Blender on your own computer.

## Install (easiest: as a plugin)

In Claude Code, run:

```
/plugin install blender-skills --marketplace rafadesuyo/Blender-Claude-Skills
```

On older Claude Code versions, use two commands instead:

```
/plugin marketplace add rafadesuyo/Blender-Claude-Skills
/plugin install blender-skills@blender-claude-skills
```

Restart Claude Code. Then just ask for things like "make a low-poly wooden fence for my Roblox game" or "check this mesh's topology".

To get updates later: `/plugin marketplace update blender-claude-skills`.

## Install (manual)

1. Click **Code → Download ZIP** on this page and unzip it.
2. Copy both folders from `skills/` into your Claude skills folder:
   - Windows: `%USERPROFILE%\.claude\skills\`
   - macOS / Linux: `~/.claude/skills/`
3. Restart Claude Code.

Keep the folder names as they are. The scripts find each other in `~/.claude/skills` or in the plugin folder. If you put them somewhere else, set the `CLAUDE_BLENDER_SKILLS` environment variable to the folder that holds `blender-game-props`.

## Notes

- The farm / crop scripts (`dragon_fruit.py`, `premium_crops.py`, `gradient_trees.py`...) use a gradient-atlas material in the style of a paid asset pack. The atlas texture is **not** included. Use your own gradient texture: set the `GRADIENT_ATLAS` environment variable to its path, or swap in flat-colour materials (the default style in `blender-game-props`).
- `SKILL.md` in `blender-game-props` has a project log at the bottom with notes from Dante's own games. File paths there (`~\Desktop\...`) point to files you won't have; the rules and recipes still apply.
- `tools/sync_skills.py` is the maintainer's script that copies the skills in from a local `~/.claude/skills` and makes the paths portable. You don't need it to use the skills.
