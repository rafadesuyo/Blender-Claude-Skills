# UEFN programmatic-toolset script (editor_toolset.toolsets.programmatic.ProgrammaticToolset /
# execute_tool_script): imports FBX files exported by blender_helpers.export_fbx and reports their
# size and material slots. Edit PROJECT, FOLDER, SOURCE_DIR and MESHES, then run it.
import json

PROJECT = 'gab'                 # the UEFN project's mount name (/gab/...)
FOLDER = 'Meshes/Store'         # where the meshes go (nested folders need module_access.verse)
SOURCE_DIR = 'C:/path/to/scratchpad/props/'
MESHES = ['SM_MyProp']          # FBX file names without .fbx; also the asset names
REMOVE_COLLISION = False        # True for decor players should walk through

ERRS = []


def T(name, args):
    try:
        return execute_tool(name, json.dumps(args))['returnValue']
    except Exception as e:
        ERRS.append(name.split('.')[-1] + ': ' + str(e)[:300])
        return None


S = 'editor_toolset.toolsets.static_mesh.StaticMeshTools.'
A = 'editor_toolset.toolsets.asset.AssetTools.'


def run():
    out = {}
    folder = '/%s/%s' % (PROJECT, FOLDER)
    for n in MESHES:
        if T(A + 'exists', {'path': folder + '/' + n}):
            out[n] = 'exists (import_file cannot overwrite: use a new name)'
            continue
        T(S + 'import_file', {'folder_path': folder, 'asset_name': n,
                              'source_file': SOURCE_DIR + n + '.fbx', 'import_materials': True})
        mesh = {'refPath': '%s/%s.%s' % (folder, n, n)}
        if REMOVE_COLLISION:
            T(S + 'remove_collisions', {'mesh': mesh})
        # Bounds are in cm: a 1 m tall prop should read ~100 on Z
        out[n] = {'bounds': T(S + 'get_bounds', {'mesh': mesh}),
                  'slots': T(S + 'get_material_slots', {'mesh': mesh})}
    out['save'] = T(A + 'save_assets', {'asset_paths': []})
    out['errs'] = ERRS
    return out
