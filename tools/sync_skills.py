"""Copy the Blender skills from a local Claude skills folder into this repo and make them portable.

Usage:  python tools/sync_skills.py [source_skills_dir]
        (default source: ~/.claude/skills)

What it changes in the copies:
- r"C:\\Users\\<you>\\.claude\\skills\\<skill>\\<file>" in code  ->  _skill("<skill>/<file>"), and a small
  _skill() helper is added to each script that needs it. _skill() finds the files for manual installs
  (~/.claude/skills) and plugin installs (~/.claude/plugins/...).
- the same path in "how to run" comments / SKILL.md  ->  <skills>/<skill>/<file>
- other C:\\Users\\<you>\\... paths  ->  ~/... (code) or ~\\... (text)
"""
import os
import re
import shutil
import sys

SKILLS = ("blender-game-props", "blender-clean-topology")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.claude/skills")

HELPER = '''# --- skill file finder: works for manual installs (~/.claude/skills) and plugin installs ---
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
'''

SKILL_PATH = re.compile(r'r"C:\\Users\\[^\\"]+\\\.claude\\skills\\([^"]+)"')
SKILL_PATH_BARE = re.compile(r'C:\\Users\\[^\\"`]+\\\.claude\\skills\\([^"`\s)]+)')
HOME_PATH = re.compile(r'r"C:\\Users\\[^\\"]+\\([^"]*)"')
HOME_PATH_BARE = re.compile(r'C:\\Users\\[^\\"`\s]+\\')


def fix_py(text):
    out = []
    for line in text.split("\n"):
        if line.lstrip().startswith("#"):
            line = SKILL_PATH.sub(lambda m: 'r"<skills>/%s"' % m.group(1).replace("\\", "/"), line)
        else:
            line = SKILL_PATH.sub(lambda m: '_skill("%s")' % m.group(1).replace("\\", "/"), line)
        line = HOME_PATH.sub(lambda m: '__import__("os").path.expanduser(r"~/%s")' % m.group(1).replace("\\", "/"), line)
        line = line.replace('+ "\\\\', '+ "/').replace('+ r"\\', '+ r"/')   # dir + "\\file" -> dir + "/file" (every OS)
        out.append(line)
    lines = out
    if any("_skill(" in l and not l.lstrip().startswith("#") for l in lines):
        i = 0   # insert after the leading comment block
        while i < len(lines) and (lines[i].startswith("#") or not lines[i].strip()):
            i += 1
        lines[i:i] = HELPER.rstrip("\n").split("\n") + [""]
    return "\n".join(lines)


PATHS_NOTE = '''
> **Paths:** `<skills>` in this file and in the script comments means the folder that holds the skill
> folders, i.e. the parent of this skill's base directory (`~/.claude/skills` for a manual install, the
> plugin's `skills` folder for a plugin install). Swap in the real absolute path when you run
> `exec(open(...).read())` in `execute_blender_code`. Scripts find their sibling files on their own.
'''


def fix_md(text):
    if text.startswith("---\n"):   # SKILL.md: explain <skills> right after the frontmatter
        end = text.index("\n---\n", 4) + 5
        text = text[:end] + PATHS_NOTE + text[end:]
    text = text.replace('D + "\\\\" + f', 'D + "/" + f')
    text = SKILL_PATH.sub(lambda m: 'r"<skills>/%s"' % m.group(1).replace("\\", "/"), text)
    text = SKILL_PATH_BARE.sub(lambda m: "<skills>/" + m.group(1).replace("\\", "/"), text)
    text = HOME_PATH.sub(lambda m: '__import__("os").path.expanduser(r"~/%s")' % m.group(1).replace("\\", "/"), text)
    return HOME_PATH_BARE.sub(lambda m: "~\\", text)


def main():
    for skill in SKILLS:
        src, dst = os.path.join(SRC, skill), os.path.join(REPO, "skills", skill)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        os.makedirs(dst)
        for name in sorted(os.listdir(src)):
            p = os.path.join(src, name)
            if not os.path.isfile(p):
                continue
            if name.endswith(".py") or name.endswith(".md"):
                text = open(p, encoding="utf-8").read().replace("\r\n", "\n")
                text = fix_py(text) if name.endswith(".py") else fix_md(text)
                if re.search(r"C:\\Users\\", text):
                    print("WARNING: personal path left in", skill, name)
                open(os.path.join(dst, name), "w", encoding="utf-8", newline="\n").write(text)
            else:
                shutil.copy2(p, dst)
            print("synced", skill + "/" + name)


if __name__ == "__main__":
    main()
