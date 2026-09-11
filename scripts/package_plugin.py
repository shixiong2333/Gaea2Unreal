#!/usr/bin/env python3
"""Create a clean source ZIP or build a Win64 plugin with an installed UE 5.8."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


PLUGIN = "GaeaUnrealTools"
DESCRIPTOR = PLUGIN + ".uplugin"
EXCLUDED_DIRS = {"Binaries", "Intermediate", "Saved", "DerivedDataCache", "__pycache__"}
EXCLUDED_SUFFIXES = {".dll", ".pdb", ".obj", ".modules", ".pyc"}


def source_files(root):
    """Allowlist plugin inputs, never copy cached build products."""
    source = root / "src" if (root / "src" / DESCRIPTOR).is_file() else root
    descriptor = json.loads((source / DESCRIPTOR).read_text(encoding="utf-8-sig"))
    if descriptor.get("EngineVersion") != "5.8.0":
        raise ValueError("Expected an Unreal Engine 5.8 plugin descriptor")
    files = {DESCRIPTOR: source / DESCRIPTOR, "LICENSE": root / "LICENSE"}
    for directory in ("Source", "Resources", "Config", "Content"):
        for path in sorted((source / directory).rglob("*")):
            relative = path.relative_to(source)
            if path.is_file() and not EXCLUDED_DIRS.intersection(relative.parts) and path.suffix.lower() not in EXCLUDED_SUFFIXES:
                if path.is_symlink():
                    raise ValueError("Symbolic links are not supported: " + str(path))
                files[relative.as_posix()] = path
    for relative in ("docs/UE-5.8.md", "scripts/package_plugin.py", "scripts/Build-UE5.8.cmd"):
        files[relative] = root / relative
    for path in files.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    return files


def stage_source(root, destination):
    for relative, path in source_files(root).items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def validate_engine(engine):
    version = json.loads((engine / "Engine/Build/Build.version").read_text(encoding="utf-8-sig"))
    if (version.get("MajorVersion"), version.get("MinorVersion")) != (5, 8):
        raise ValueError("Binary packaging requires UE 5.8; refusing to relabel another engine build")
    uat = engine / "Engine/Build/BatchFiles/RunUAT.bat"
    if not uat.is_file():
        raise FileNotFoundError(uat)
    return version, uat


def validate_binaries(package):
    manifest = json.loads((package / "Binaries/Win64/UnrealEditor.modules").read_text(encoding="utf-8-sig"))
    descriptor = json.loads((package / DESCRIPTOR).read_text(encoding="utf-8-sig"))
    if not manifest.get("BuildId"):
        raise ValueError("Build output is missing the Unreal build ID")
    for module in descriptor["Modules"]:
        filename = manifest.get("Modules", {}).get(module["Name"], "")
        if not filename or Path(filename).name != filename or not filename.endswith(".dll"):
            raise ValueError("Missing/invalid module entry: " + module["Name"])
        binary = package / "Binaries/Win64" / filename
        if not binary.is_file() or binary.stat().st_size == 0:
            raise ValueError("Missing/empty compiled module: " + str(binary))
    return manifest["BuildId"]


def archive_tree(package, archive, metadata):
    files = {p.relative_to(package).as_posix(): p.read_bytes() for p in package.rglob("*") if p.is_file()}
    metadata = dict(metadata, files_sha256={name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())})
    files["BUILD_INFO.json"] = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode()
    archive.parent.mkdir(parents=True, exist_ok=True)
    # Use exclusive creation, so a previous successful package cannot be overwritten.
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as output:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(PLUGIN + "/" + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, data)
    return archive


def package_plugin(root, output, engine=None):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError("Choose a new output path: " + str(output))
    version = None
    if engine is not None:
        if os.name != "nt":
            raise RuntimeError("Win64 binary packaging must run on Windows with UE 5.8 installed")
        version, uat = validate_engine(Path(engine).resolve())
    with tempfile.TemporaryDirectory(prefix="GaeaUE58-") as temporary:
        stage = Path(temporary) / "SourcePlugin"
        stage_source(root, stage)
        metadata = {"engine_target": "5.8", "package_type": "source", "engine_compiled": False, "editor_smoke_tested": False}
        package = stage
        if engine is not None:
            package = Path(temporary) / PLUGIN
            output.parent.mkdir(parents=True, exist_ok=True)
            log = output.with_suffix(".build.log")
            print("Running UE 5.8 BuildPlugin. Log:", log, flush=True)
            with log.open("x", encoding="utf-8") as stream:
                subprocess.run([str(uat), "BuildPlugin", "-Plugin=" + str(stage / DESCRIPTOR),
                                "-Package=" + str(package), "-TargetPlatforms=Win64", "-StrictIncludes"],
                               check=True, stdout=stream, stderr=subprocess.STDOUT)
            build_id = validate_binaries(package)
            for relative in ("LICENSE", "docs/UE-5.8.md"):
                target = package / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(stage / relative, target)
            metadata.update(package_type="binary", engine_compiled=True, engine_version=version, build_id=build_id)
        return archive_tree(package, output, metadata)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--source", action="store_true", help="Create source package; no Unreal binaries")
    mode.add_argument("--engine", type=Path, help="Installed UE 5.8 directory (Win64 build)")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    kind = "Source" if args.source else "Win64"
    output = args.output or root / "dist" / ("Gaea2Unreal-UE5.8-" + kind + ".zip")
    try:
        result = package_plugin(root, output, args.engine)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, "Packaging failed: " + str(error) + "\n")
    print("Created:", result)
    print("SHA256:", hashlib.sha256(result.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
