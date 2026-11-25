#!/usr/bin/env python3
"""Apply local PCL-CE patches, failing closed on upstream source drift."""

from pathlib import Path
import sys


RELATIVE_PATH = Path("PCL.Core/App/Region/RegionPolicy.cs")
OLD = "public bool IsRestricted => Classification is RegionClassification.Mainland or RegionClassification.Unknown;"
NEW = "public bool IsRestricted => false;"
PROFILE_UI_PATH = Path("Plain Craft Launcher 2/Modules/Minecraft/ProfileUi.cs")
PROFILE_UI_OLD = '''        int? selected = null;
        ModBase.RunInUiWait(() =>
        {
            var includeOthers = CanCreateOtherProfile();
            selected = ModMain.MyMsgBoxSelect(_GetAvailableProfileSelection(includeOthers),
                Lang.Text("Launch.Account.Profile.Create.SelectAuthType.Title"), Lang.Text("Common.Action.Continue"), Lang.Text("Common.Action.Cancel"));
        });
        if (selected is null) return;
        ProfileService.IsCreatingProfile = true;
        var type = selected.Value switch
        {
            0 => ModLaunch.McLoginType.Ms,
            1 => ModLaunch.McLoginType.Auth,
            _ => ModLaunch.McLoginType.Legacy
        };'''
PROFILE_UI_NEW = '''        var includeOthers = CanCreateOtherProfile();
        int? selected = null;
        ModBase.RunInUiWait(() =>
        {
            selected = ModMain.MyMsgBoxSelect(_GetAvailableProfileSelection(includeOthers),
                Lang.Text("Launch.Account.Profile.Create.SelectAuthType.Title"), Lang.Text("Common.Action.Continue"), Lang.Text("Common.Action.Cancel"));
        });
        if (selected is null) return;
        ProfileService.IsCreatingProfile = true;
        var type = selected.Value switch
        {
            0 => ModLaunch.McLoginType.Ms,
            1 when includeOthers => ModLaunch.McLoginType.Auth,
            _ => ModLaunch.McLoginType.Legacy
        };'''
PROFILE_SELECTION_OLD = '''        : [new MyListItem { Title = Lang.Text("Launch.Account.Type.Microsoft"), Type = MyListItem.CheckType.RadioBox, SvgIcon = "lucide/shield-check" }];'''
PROFILE_SELECTION_NEW = '''        : [
            new MyListItem { Title = Lang.Text("Launch.Account.Type.Microsoft"), Type = MyListItem.CheckType.RadioBox, SvgIcon = "lucide/shield-check" },
            new MyListItem { Title = Lang.Text("Launch.Account.Type.Offline"), Type = MyListItem.CheckType.RadioBox, SvgIcon = "lucide/link-2-off" }
        ];'''
PROFILE_PAGE_PATH = Path("Plain Craft Launcher 2/Pages/PageLaunch/PageLoginProfile.xaml.cs")
PROFILE_HINT_OLD = "HintMicrosoft.Visibility = ProfileService.Profiles.Count == 0 ? Visibility.Visible : Visibility.Collapsed;"
PROFILE_HINT_NEW = "HintMicrosoft.Visibility = Visibility.Collapsed;"
UPDATE_MANAGER_PATH = Path("Plain Craft Launcher 2/Modules/Updates/UpdateManager.cs")
UPDATE_MANAGER_OLD = "    public static UpdatesWrapperModel remoteServer = new(new List<IUpdateSource>\n    {\n        new UpdatesMirrorChyanModel(),\n        new UpdatesRandomModel(new[]\n        {\n            new UpdatesMinioModel(\"https://s3.pysio.online/pcl2-ce/\", \"Pysio\"),\n            new UpdatesMinioModel(\"https://staticassets.naids.com/resources/pclce/\", \"Naids\")\n        }),\n        new UpdatesMinioModel(\"https://github.com/PCL-Community/PCL2_CE_Server/raw/main/\", \"GitHub\")\n    });"
UPDATE_MANAGER_NEW = "    public static UpdatesWrapperModel remoteServer = new(new List<IUpdateSource>\n    {\n        new UpdatesGitHubReleaseModel()\n    });\n\n    public static UpdatesWrapperModel announcementServer = new(new List<IUpdateSource>\n    {\n        new UpdatesMirrorChyanModel(),\n        new UpdatesRandomModel(new[]\n        {\n            new UpdatesMinioModel(\"https://s3.pysio.online/pcl2-ce/\", \"Pysio\"),\n            new UpdatesMinioModel(\"https://staticassets.naids.com/resources/pclce/\", \"Naids\")\n        }),\n        new UpdatesMinioModel(\"https://github.com/PCL-Community/PCL2_CE_Server/raw/main/\", \"GitHub\")\n    });"
ANNOUNCEMENT_PATH = Path("Plain Craft Launcher 2/Modules/Updates/AnnouncementService.cs")
ANNOUNCEMENT_OLD = "UpdateManager.remoteServer.GetAnnouncementList()"
ANNOUNCEMENT_NEW = "UpdateManager.announcementServer.GetAnnouncementList()"
CHANGELOG_PATH = Path("Plain Craft Launcher 2/Pages/PageSetup/PageSetupUpdate.xaml.cs")
CHANGELOG_OLD = "ModBase.OpenWebsite(\"https://github.com/PCL-Community/PCL2-CE/releases/v\" + ModBase.versionBaseName);"
CHANGELOG_NEW = "ModBase.OpenWebsite(\"https://github.com/Luoning77/PCL-CE-LUO/releases/tag/pcl-ce-v\" + ModBase.versionBaseName + \"-custom-x64\");"
MIRROR_LINK_PATH = Path("Plain Craft Launcher 2/Pages/PageSetup/PageSetupUpdate.xaml.cs")
MIRROR_LINK_OLD = "ModBase.OpenWebsite(\"https://mirrorchyan.com/\");"
MIRROR_LINK_NEW = "ModBase.OpenWebsite(\"https://github.com/Luoning77/PCL-CE-LUO/releases\");"
CHANNEL_PATH = Path("Plain Craft Launcher 2/Pages/PageSetup/PageSetupUpdate.xaml.cs")
CHANNEL_OLD = "ComboSystemUpdateChannel.SelectedIndex = (int)Config.Update.UpdateChannel;"
CHANNEL_NEW = "ComboSystemUpdateChannel.SelectedIndex = 0;\n        ComboSystemUpdateChannel.IsEnabled = false;\n        Config.Update.UpdateChannel = (Core.App.UpdateChannel)0;"
MIRROR_UI_PATH = Path("Plain Craft Launcher 2/Pages/PageSetup/PageSetupUpdate.xaml")
MIRROR_UI_OLD = "                        <TextBlock Text=\"{DynamicResource Setup.Update.MirrorChyanCdk.Label}\" Grid.Row=\"4\" VerticalAlignment=\"Center\"\n                                   HorizontalAlignment=\"Left\" Margin=\"0,0,25,0\" />\n                        <PasswordBox x:Name=\"TextMirrorCDK\"\n                                      ToolTip=\"{DynamicResource Setup.Update.MirrorChyanCdk.ToolTip}\"\n                                     Grid.Row=\"4\" Grid.Column=\"1\"\n                                     PasswordChanged=\"TextMirrorCDK_PasswordChanged\" />\n                        <local:MyButton x:Name=\"BtnGetMirrorCDK\" Text=\"{DynamicResource Setup.Update.MirrorChyanCdk.Get}\" Grid.Column=\"3\" Grid.Row=\"4\"\n                                        ColorType=\"Highlight\" Click=\"BtnGetMirrorCDK_Click\" />"
MIRROR_UI_NEW = "                        <TextBlock Visibility=\"Collapsed\" Text=\"{DynamicResource Setup.Update.MirrorChyanCdk.Label}\" Grid.Row=\"4\" VerticalAlignment=\"Center\"\n                                   HorizontalAlignment=\"Left\" Margin=\"0,0,25,0\" />\n                        <PasswordBox Visibility=\"Collapsed\" x:Name=\"TextMirrorCDK\"\n                                      ToolTip=\"{DynamicResource Setup.Update.MirrorChyanCdk.ToolTip}\"\n                                     Grid.Row=\"4\" Grid.Column=\"1\"\n                                     PasswordChanged=\"TextMirrorCDK_PasswordChanged\" />\n                        <local:MyButton Visibility=\"Collapsed\" x:Name=\"BtnGetMirrorCDK\" Text=\"{DynamicResource Setup.Update.MirrorChyanCdk.Get}\" Grid.Column=\"3\" Grid.Row=\"4\"\n                                        ColorType=\"Highlight\" Click=\"BtnGetMirrorCDK_Click\" />"
UPDATE_SOURCE_FILE = Path("Plain Craft Launcher 2/Modules/Updates/UpdatesGitHubReleaseModel.cs")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-region-policy.py <pcl-ce-source-root>", file=sys.stderr)
        return 2

    source_root = Path(sys.argv[1])
    file_path = source_root / RELATIVE_PATH
    if not file_path.is_file():
        print(f"expected source file not found: {file_path}", file=sys.stderr)
        return 1

    content = file_path.read_text(encoding="utf-8")
    matches = content.count(OLD)
    if matches != 1:
        print(
            f"expected exactly one region-policy expression, found {matches}; "
            "upstream may have changed, refusing to publish",
            file=sys.stderr,
        )
        return 1

    patched = content.replace(OLD, NEW, 1)
    if patched.count(NEW) != 1 or OLD in patched:
        print("patch verification failed; refusing to publish", file=sys.stderr)
        return 1

    with file_path.open("w", encoding="utf-8", newline="") as output:
        output.write(patched)
    print(f"patched {file_path}")

    for relative_path, old, new, label in (
        (PROFILE_UI_PATH, PROFILE_UI_OLD, PROFILE_UI_NEW, "offline profile selection"),
        (PROFILE_UI_PATH, PROFILE_SELECTION_OLD, PROFILE_SELECTION_NEW, "offline profile option"),
        (PROFILE_PAGE_PATH, PROFILE_HINT_OLD, PROFILE_HINT_NEW, "obsolete Microsoft hint"),
        (UPDATE_MANAGER_PATH, UPDATE_MANAGER_OLD, UPDATE_MANAGER_NEW, "exclusive custom version source"),
        (ANNOUNCEMENT_PATH, ANNOUNCEMENT_OLD, ANNOUNCEMENT_NEW, "separate announcement source"),
        (CHANGELOG_PATH, CHANGELOG_OLD, CHANGELOG_NEW, "custom release link"),
        (MIRROR_LINK_PATH, MIRROR_LINK_OLD, MIRROR_LINK_NEW, "obsolete mirror link"),
        (CHANNEL_PATH, CHANNEL_OLD, CHANNEL_NEW, "stable-only update channel"),
        (MIRROR_UI_PATH, MIRROR_UI_OLD, MIRROR_UI_NEW, "hide obsolete mirror settings"),
    ):
        target = source_root / relative_path
        if not target.is_file():
            print(f"expected source file not found: {target}", file=sys.stderr)
            return 1
        content = target.read_text(encoding="utf-8")
        matches = content.count(old)
        if matches != 1:
            print(
                f"expected exactly one {label} source block, found {matches}; "
                "upstream may have changed, refusing to publish",
                file=sys.stderr,
            )
            return 1
        updated = content.replace(old, new, 1)
        if (new and updated.count(new) != 1) or (old in updated and old not in new):
            print(f"{label} patch verification failed; refusing to publish", file=sys.stderr)
            return 1
        with target.open("w", encoding="utf-8", newline="") as output:
            output.write(updated)
        print(f"patched {target}")

    update_source = source_root / UPDATE_SOURCE_FILE
    template = Path(__file__).with_name("UpdatesGitHubReleaseModel.cs")
    if update_source.exists():
        print(f"unexpected upstream update source already exists: {update_source}", file=sys.stderr)
        return 1
    if not template.is_file():
        print(f"GitHub update source template not found: {template}", file=sys.stderr)
        return 1
    with update_source.open("w", encoding="utf-8", newline="") as output:
        output.write(template.read_text(encoding="utf-8"))
    print(f"added {update_source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
