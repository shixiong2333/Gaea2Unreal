![Gaea2Unreal](screenshots/gaea2Unreal.jpg)

# Gaea2Unreal

## Community UE 5.8 port

This fork provides a **community UE 5.8 compatibility candidate
(2.2.0.8-rc1)** based on [QuadSpinner's Gaea2Unreal](https://github.com/QuadSpinner/Gaea2Unreal).
It is not an official QuadSpinner release.

The Win64 plugin has been compiled and loaded with **UE 5.8.2**. The verified
Fix3 build passed height reimport, manual translation/rotation, loaded World
Partition proxy alignment and collision, weighted reimport after map reload,
and final editor restart checks. See the
[build, install, and validation guide](docs/UE-5.8.md) for the exact tested scope
and remaining limits.

```powershell
# Clean source archive (no precompiled binaries)
py -3 scripts/package_plugin.py --source
# Compile and package with your installed UE 5.8 on Windows
py -3 scripts/package_plugin.py --engine "C:\Program Files\Epic Games\UE_5.8"
```

Outputs are written to `dist/`. The source ZIP includes the build scripts; the
Win64 ZIP is created only after Unreal Automation Tool succeeds and the editor
module files are checked.

Use Gaea2Unreal, specifically the Gaea Landscape Importer, to import a
[Gaea terrain](https://quadspinner.com), color maps, weight maps, and masks into
Unreal Engine 5.

![Unreal Export](screenshots/ue_export.png)
![Unreal Import](screenshots/ue_import.png)

## Download

For this community UE 5.8 port's packages and release status, see
[this fork's Releases](https://github.com/shixiong2333/Gaea2Unreal/releases).
Select a compiled Win64 package when you need a plugin ready to load; a source
archive does not contain compiled DLLs.

Original upstream packages remain available from
[QuadSpinner's Releases](https://github.com/QuadSpinner/Gaea2Unreal/releases).
Those releases are separate from this fork's UE 5.8 candidate.

## Source and support

The `UE-5.8` branch contains this community port. Original upstream development
is maintained in [QuadSpinner/Gaea2Unreal](https://github.com/QuadSpinner/Gaea2Unreal).
Report source issues specific to this port in this fork. For upstream usage
support, see [QuadSpinner Tech Support](https://quadspinner.com/support).

The original [LICENSE](LICENSE) applies, including its attribution requirement
and restriction on selling derivative plugins as standalone products.

## Documentation and usage

See [Gaea2Unreal terrain import documentation](https://docs.gaea.app/plugins/gaea2unreal/importing-terrains).

## Website

Download Gaea Community Edition from [QuadSpinner](https://quadspinner.com).
