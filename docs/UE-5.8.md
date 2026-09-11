# UE 5.8 compatibility candidate

This branch targets **UE 5.8**, plugin version **2.2.0.8-rc1**. Source changes and
packaging checks have been reviewed without an installed Unreal Engine.
**UE 5.8 compilation and editor import/reimport smoke tests remain pending.**
A source ZIP is not a precompiled plugin. Do not copy a DLL or `.modules` file
from a UE 5.7 installation and rename it for 5.8.

## Build a Win64 plugin

Prerequisites: Windows, Python 3.9 or newer (with the `py` launcher), UE 5.8, and
the Visual Studio C++ toolchain and Windows SDK required by that UE installation.
Close Unreal Editor before installing the result.

Run from the repository root, or the extracted `GaeaUnrealTools` source folder:

```powershell
py -3 scripts/package_plugin.py --engine "C:\Program Files\Epic Games\UE_5.8"
```

Alternatively, double-click `scripts/Build-UE5.8.cmd` for the default engine path,
or pass a custom engine directory as its first argument. Python can also be
invoked as `python` if the `py` launcher is unavailable.

The script checks `Build.version` for UE 5.8 and invokes Unreal Automation Tool:
`BuildPlugin -TargetPlatforms=Win64 -StrictIncludes`. It stages only clean source,
resources, configuration and content in a temporary directory. It verifies both
editor module DLLs and the UAT-generated module manifest before creating
`dist/Gaea2Unreal-UE5.8-Win64.zip`. The adjacent `.build.log` captures compiler
output, including failures. A failed build produces no installable archive.
Existing archives/logs are not overwritten: choose a fresh `--output` path for a
repeat build. `BUILD_INFO.json` records the engine/build ID and per-file hashes;
successful compilation does not mark editor smoke tests as passed.

## Install

Extract the **compiled Win64 ZIP** so the descriptor is at:

`YourProject/Plugins/GaeaUnrealTools/GaeaUnrealTools.uplugin`

Use a separate test project first and avoid loading another copy of this plugin
from the engine Plugins directory. The source ZIP has the same plugin folder
layout but requires a C++ project/toolchain to compile before it can be loaded.
For a Blueprint-only project, build the Win64 package using the command above.

## Make a source package

```powershell
py -3 scripts/package_plugin.py --source
# Run tests from the repository checkout (tests are not in the plugin ZIP):
py -3 -m unittest discover -s tests -v
```

The source archive includes the plugin, original license, this guide, and build
scripts. It excludes old `Binaries`, `Intermediate`, PDBs and generated headers.
`BUILD_INFO.json` explicitly reports `engine_compiled: false`.

## Changes and reference

Baseline: QuadSpinner UE 5.7 merge `7447d4ed470bf69f8e359ac3e56048bdbd491509`.
Reference: [AIptegin's UE 5.8 commit](https://github.com/AIptegin/Gaea2Unreal/commit/8bd2a52dde43293f7fa1e64a2f39482b48bce892).

- Target UE 5.8 without downgrading the plugin version.
- Include `AppStyle` directly and declare the modules used by public headers,
  file dialogs, property widgets and asset creation.
- Pass the painting restriction explicitly in the WP base weightmap write.
- Reject empty/non-landscape selections and missing base edit layers before
  dereferencing them during reimport.
- Clear weightmaps only on the base edit layer being reimported. Material target
  layer indices are not edit layer indices; preserve upper sculpt/paint layers.
- Register only the material layers actually imported, avoiding an out-of-bounds
  access when a material is set but weightmap import is skipped.

The UE 5.7 baseline already uses most APIs found in the reference's UE 5.8 path:
`GetEditLayer`, `GetSectionBase`, `GetLayerName`, `AddTargetLayer`, and the explicit
`FLandscapeLayer` array view in `Import`. Those calls are retained. The reference's
older-engine fallback paths, removed UI/GC/editor-only safeguards, generated
files, and license replacement are not included. The original QuadSpinner license
and attribution requirements are retained in `LICENSE`.

## Editor validation required before merging

- Build with UE 5.8 and verify plugin discovery and the importer window.
- Import a heightmap with its Gaea definition JSON in a normal level. Check XY
  scale, height, orientation, and landscape collision.
- Import with a material but no matching weightmaps; it must not crash.
- Import a base material layer plus at least two weightmaps; check layer names,
  assignments and blending. Reimport twice and check for accumulating weights.
- Repeat height-only and weighted imports/reimports in a World Partition level.
  Check loaded proxy boundaries and collision.
- Add a manual upper edit layer; base reimport must preserve its sculpt/paint.
- Exercise reimport with no selection, a non-landscape actor, and a missing base
  edit layer; verify safe early return.
- Save, restart the editor, reload the map, and check the imported terrain.

These are validation requirements, not claimed test results. Existing tiled
import, proxy loading, and material workflows have not been expanded in this port.
