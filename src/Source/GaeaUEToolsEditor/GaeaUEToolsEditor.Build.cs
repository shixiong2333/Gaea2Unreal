using System.IO;
using UnrealBuildTool;

public class GaeaUEToolsEditor : ModuleRules
{
    public GaeaUEToolsEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        var EngineDir = Path.GetFullPath(base.Target.RelativeEnginePath);
        PublicSystemIncludePaths.AddRange(new string[]
        
        {
            Path.Combine(EngineDir, "Source/Editor/LandscapeEditor/Private")
            }
        );

        PublicDependencyModuleNames.AddRange(
            new string[]
            {
                "Core", "CoreUObject", "Engine", "Landscape", "Slate", "SlateCore",
                "EditorSubsystem", "LandscapeEditor", "PropertyEditor", "DesktopPlatform",
            }
        );

        PrivateDependencyModuleNames.AddRange(
            new string[]
            {
                "InputCore",
                "LevelEditor",
                "Projects",
                "MaterialEditor", 
                "UnrealEd", 
                "ToolMenus", 
                "EditorFramework",
                "Foliage",
                "Json",
                "JsonUtilities",
                "AssetRegistry", "EditorScriptingUtilities", "AssetTools"
            }
        );
    }
}
