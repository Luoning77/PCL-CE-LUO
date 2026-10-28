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
UPDATE_SOURCE_OLD = '        new UpdatesMinioModel("https://github.com/PCL-Community/PCL2_CE_Server/raw/main/", "GitHub")'
UPDATE_SOURCE_NEW = ""
UPDATE_PRIMARY_OLD = "    public static UpdatesWrapperModel remoteServer = new(new List<IUpdateSource>\n    {\n"
UPDATE_PRIMARY_NEW = UPDATE_PRIMARY_OLD + "        new UpdatesGitHubReleaseModel(),\n"
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
        (UPDATE_MANAGER_PATH, UPDATE_SOURCE_OLD, UPDATE_SOURCE_NEW, "GitHub update source"),
        (UPDATE_MANAGER_PATH, UPDATE_PRIMARY_OLD, UPDATE_PRIMARY_NEW, "primary fork update source"),
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
        if (new and updated.count(new) != 1) or (old in updated and label != "primary fork update source"):
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
