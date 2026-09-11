"""Package integrity tests. These do not compile or execute Unreal Engine."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_plugin", ROOT / "scripts/package_plugin.py")
packaging = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packaging)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_source_is_clean_and_integrity_manifest_matches(self):
        fixture = self.root / "fixture"
        packaging.stage_source(ROOT, fixture)
        for relative in ("Binaries/Win64/old.dll", "Intermediate/old.generated.h",
                         "Source/Intermediate/stale.cpp", "Resources/old.pdb"):
            target = fixture / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("stale")
        output = packaging.package_plugin(fixture, self.root / "source.zip")
        with zipfile.ZipFile(output) as archive:
            self.assertIsNone(archive.testzip())
            prefix = packaging.PLUGIN + "/"
            names = archive.namelist()
            self.assertTrue(all(name.startswith(prefix) for name in names))
            self.assertFalse(any("stale" in name or "old." in name for name in names))
            self.assertEqual(archive.read(prefix + "LICENSE"), (ROOT / "LICENSE").read_bytes())
            info = json.loads(archive.read(prefix + "BUILD_INFO.json"))
            self.assertFalse(info["engine_compiled"])
            self.assertFalse(info["editor_smoke_tested"])
            self.assertEqual(info["package_type"], "source")
            self.assertEqual(set(names), {prefix + name for name in info["files_sha256"]} | {prefix + "BUILD_INFO.json"})
            for name, digest in info["files_sha256"].items():
                self.assertEqual(hashlib.sha256(archive.read(prefix + name)).hexdigest(), digest)
            for module in ("GaeaUnrealTools", "GaeaUEToolsEditor"):
                self.assertIn(prefix + "Source/" + module + "/" + module + ".Build.cs", names)
            self.assertIn(prefix + "Resources/ImporterIcon.png", names)

    def test_source_is_reproducible_and_never_overwrites_output(self):
        first = packaging.package_plugin(ROOT, self.root / "one.zip")
        second = packaging.package_plugin(ROOT, self.root / "two.zip")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        before = first.read_bytes()
        with self.assertRaises(FileExistsError):
            packaging.package_plugin(ROOT, first)
        self.assertEqual(first.read_bytes(), before)

    def make_engine(self, minor=8):
        engine = self.root / "UE installation with spaces"
        version = engine / "Engine/Build/Build.version"
        version.parent.mkdir(parents=True, exist_ok=True)
        version.write_text(json.dumps({"MajorVersion": 5, "MinorVersion": minor, "PatchVersion": 1}))
        uat = engine / "Engine/Build/BatchFiles/RunUAT.bat"
        uat.parent.mkdir(parents=True, exist_ok=True)
        uat.write_text("@echo off")
        return engine

    def test_wrong_engine_rejected(self):
        with self.assertRaisesRegex(ValueError, "requires UE 5.8"):
            packaging.validate_engine(self.make_engine(7))
        version, uat = packaging.validate_engine(self.make_engine())
        self.assertEqual(version["MinorVersion"], 8)
        self.assertTrue(uat.is_file())

    def fake_uat(self, command, **kwargs):
        # Simulate the packaging protocol only; these are NOT compiled DLLs.
        self.assertIn("-TargetPlatforms=Win64", command)
        self.assertIn("-StrictIncludes", command)
        package = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("-Package=")))
        source = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("-Plugin=")))
        binary_dir = package / "Binaries/Win64"
        binary_dir.mkdir(parents=True)
        shutil.copyfile(source, package / packaging.DESCRIPTOR)
        modules = {}
        for module in json.loads(source.read_text())["Modules"]:
            filename = "UnrealEditor-" + module["Name"] + ".dll"
            modules[module["Name"]] = filename
            (binary_dir / filename).write_bytes(b"test fixture, not an executable")
        (binary_dir / "UnrealEditor.modules").write_text(json.dumps({"BuildId": "test-only", "Modules": modules}))

    def test_binary_package_requires_success_and_complete_manifest(self):
        engine = self.make_engine()
        with patch.object(packaging, "os", SimpleNamespace(name="nt")), patch.object(packaging.subprocess, "run", self.fake_uat):
            output = packaging.package_plugin(ROOT, self.root / "binary.zip", engine)
        with zipfile.ZipFile(output) as archive:
            metadata = json.loads(archive.read(packaging.PLUGIN + "/BUILD_INFO.json"))
            self.assertEqual(metadata["build_id"], "test-only")
            self.assertTrue(metadata["engine_compiled"])
            self.assertFalse(metadata["editor_smoke_tested"])

    def test_uat_failure_produces_no_archive(self):
        output = self.root / "failed.zip"
        with patch.object(packaging, "os", SimpleNamespace(name="nt")), patch.object(packaging.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "fake UAT")):
            with self.assertRaises(subprocess.CalledProcessError):
                packaging.package_plugin(ROOT, output, self.make_engine())
        self.assertFalse(output.exists())
        self.assertTrue(output.with_suffix(".build.log").is_file())

    def test_missing_dll_produces_no_archive(self):
        output = self.root / "incomplete.zip"
        def incomplete(command, **kwargs):
            self.fake_uat(command, **kwargs)
            package = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("-Package=")))
            (package / "Binaries/Win64/UnrealEditor-GaeaUEToolsEditor.dll").unlink()
        with patch.object(packaging, "os", SimpleNamespace(name="nt")), patch.object(packaging.subprocess, "run", incomplete):
            with self.assertRaisesRegex(ValueError, "Missing/empty compiled module"):
                packaging.package_plugin(ROOT, output, self.make_engine())
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
