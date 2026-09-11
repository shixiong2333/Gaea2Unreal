# UE 5.8 compatibility candidate

This community port targets **UE 5.8**, plugin version **2.2.0.8-rc1**. It is based
on QuadSpinner's plugin and is not an official QuadSpinner release. Both Win64
editor modules, `GaeaUnrealTools` and `GaeaUEToolsEditor`, were compiled and loaded
with installed **UE 5.8.2**, module **BuildId 55116800**. The verified **Fix3** build
passed the editor checks listed below, including weighted reimport after map
reload and final verification after an editor restart. All **6 packaging unit
tests passed**. Validation is limited to the stated cases and platforms.
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

## Reimport height datum correction

An editor test reproduced a height-range regression in the previous reimport
code: changing Gaea's height range from **A = 847.2 m** to **B = 899.0 m** changed
Z scale without adjusting the landscape location. The raw-height-zero datum
therefore moved down to **-25.9 m**, equal to `(847.2 - 899.0) / 2` for a landscape
originally imported with its datum at world Z = 0. This is an observed failure of
the previous implementation, not a passing result for the correction.

Landscape raw height 0 is local Z = -256. Reimport now adds
`256 * (newScaleZ - oldScaleZ)` along the landscape's rotated local Z axis to its
translation before applying the new scale. This keeps the existing raw-zero
world datum fixed and preserves manual translation and rotation. Repeated
reimport at an unchanged scale adds no translation.

The root landscape applies this transform once. Its `ULandscapeInfo::DrawScale`
is updated, and `FixupProxiesTransform(true)` derives transforms for the loaded
streaming proxies from the root and their section offsets. Changed scale also
recreates heightfield collision on the root and loaded proxies. Texture edits
are flushed before this step in a normal level; in the WP path all per-proxy
edit interfaces have left scope before the shared transform/collision update.
The landscape then requests a complete edit-layer content update.

The correction preserves the datum that exists when reimport starts. A landscape
already displaced by the old bug cannot be repaired automatically because its
unintended displacement cannot be distinguished from a deliberate user offset.
Repair such a landscape separately using a known original datum or baseline;
reimport does not automatically reset its location to zero.

## Visibility layer and reimport after reopening

A separate saved-map test reproduced a weightmap failure: height reimport was
correct, but Base, Rock, and Snow became zero and the material rendered black.
UE 5.8 `ALandscapeProxy::PostLoad()` automatically adds a Visibility target layer;
`ULandscapeInfo::UpdateLayerInfoMapInternal()` gives it the engine Visibility
layer-info object. The plugin previously included that object in the material
paint-layer list. Three paint layers therefore became four counted layers after
reopening. With two Gaea weightmap files, the normal reimport cleared the paint
layers, then failed its `2 >= 4 - 1` count check and skipped every weight write,
including the solid base fill. Valid input paths did not prevent this failure.

Both normal and WP reimport now exclude `ALandscapeProxy::VisibilityLayer` from
the paint-layer list and file pairing. When weightmap reimport is requested,
they check for a base paint layer and enough files for the remaining paint
layers before clearing any layer; a failed count check returns with the terrain
unchanged. This also prevents the WP path from pairing Gaea files with the
engine's Visibility layer. The existing clear operation preserves Visibility.
The correction passed weighted reimport after map reload in the verified Fix3 build.

## Verified behavior (2026-09-12)

The 12-stage height-only matrix and its 60 collision samples were completed on
the height-datum correction build **before the Visibility fix**. Fix3 retains
the same height/transform/collision implementation and passed **7 additional
checks plus verification of six saved maps after an actual editor restart**,
rechecking the key height-code paths. The full 12-stage matrix was not rerun on
the Fix3 binary.

- Both editor modules compiled and loaded with UE 5.8.2 on Win64. The installed
  DLLs match the verified Fix3 package byte for byte; all 6 packaging tests passed.
- Height-only import/reimport passed **12 stages across two 505-resolution maps**,
  one normal level and one World Partition level. A-to-B height-range changes,
  repeated reimport, and reimport after manual translation preserved the expected
  locations/scales; height-data hashes matched their references.
- **60 collision samples passed**, with maximum world-height error below
  **0.336 cm**.
- The WP test used **4 loaded streaming proxies and 64 landscape components**.
  It verified transforms, section offsets, component world positions, and
  **112 shared component edges, including 16 edges between proxies**.
- Rotated A/B reimport preserved rotation and the raw-zero datum with **0 cm
  measured datum error**. WP XY resizing and restoring the original scale passed
  the root-anchor, proxy-transform, and shared-edge checks.
- Weighted reimport after map reload passed in **three maps**, covering normal,
  WP, and an independently created weighted case. Base, Rock, and Snow readbacks
  matched the previously verified correct buffers exactly, including repeated
  reimport.
- After a real editor restart, **all six saved maps passed** the applicable
  height, weightmap, transform, and loaded-WP geometry/collision checks.

## Untested scope

- Manual upper edit-layer sculpt/paint overrides and import orientation/flip
  options have not been validated in this test set.
- Large landscapes and tiled imports need separate checks for memory use,
  boundaries, and import behavior; the tests above use small, loaded maps.
- Runtime World Partition streaming and unloaded regions have not been
  validated. Reimport operates on loaded/registered proxies and does not load
  every region automatically.
- Material-without-matching-weightmaps behavior and the no-selection,
  non-landscape-selection, missing-base-layer, and insufficient-file guards
  still require dedicated negative tests.

These items are outside the reported passing results. Existing tiled import,
proxy loading, and material workflows have not been expanded in this port.

## Verified archive and validation metadata

The tested archive is `Gaea2Unreal-UE5.8-Win64-ReimportFix3.zip`.
Its SHA256 is
`7fa947797ba504cf773d8de437f9cf80a0abb5917bdb685f1d534a99ad303272`.

This archive was generated **before its editor verification**. Its bundled guide
and `BUILD_INFO.json` describe the state at packaging time, so
`editor_smoke_tested: false` is a historical packaging record, not a failure of
the later tests documented above. The archive contains the source snapshot used
for its compiled DLLs.

A later release archive may include this updated guide and a dated validation
record while retaining the exact verified DLL bytes. Any such repackaging must
update the affected per-file hashes and the archive SHA256; its validation record
should identify the tested engine/build ID and the limited scope above. It must
not imply that a different binary or an untested workflow was verified.
