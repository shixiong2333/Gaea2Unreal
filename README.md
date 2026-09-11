![Gaea2Unreal](screenshots/gaea2Unreal.jpg)

# Gaea2Unreal

## UE 5.8 branch

This branch contains the **UE 5.8 compatibility candidate (2.2.0.8-rc1)**.
UE 5.8 compilation and editor smoke tests are still pending. See
[build, install, and validation instructions](docs/UE-5.8.md).

```powershell
# Clean source archive (no precompiled binaries)
py -3 scripts/package_plugin.py --source
# Compile and package with your installed UE 5.8 on Windows
py -3 scripts/package_plugin.py --engine "C:\Program Files\Epic Games\UE_5.8"
```

Outputs are written to `dist/`. The source ZIP includes the build scripts; the
Win64 ZIP is created only after Unreal Automation Tool succeeds and the editor
module files are checked. The upstream download below is separate from this
branch's UE 5.8 candidate.

Use Gaea2Unreal, specifically the Gaea Landscape Importer, to easily import a [Gaea terrain](https://quadspinner.com), color maps, weight maps, and masks in Unreal Engine 5 with a single click.

![Unreal Export](screenshots/ue_export.png)
![Unreal Import](screenshots/ue_import.png)

Importing terrains into Unreal Engine can be a complicated process, especially when dealing with various scales. Gaea2Unreal aims to make this an easy, seamless experience for you.

# Download 
The compiled version of the plugin can found in the [Releases](https://github.com/QuadSpinner/Gaea2Unreal/releases).

# Source Code
The source code for Gaea2Unreal can be found in this repository. The `main` branch contains the latest version. Any work-in-progress can be found in a `dev` branch while, past releases can be found in numbered version branches such as `UE-5.3`.

Issues should be opened only for the source code. For usage or other issues, you should contact [QuadSpinner Tech Support](https://quadspinner.com/support).

# Documentation and Usage Instructions
For usage instructions: https://docs.gaea.app/plugins/gaea2unreal/importing-terrains

# Website
Download Gaea Community Edition for free at https://quadspinner.com 
