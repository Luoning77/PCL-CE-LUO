using System;
using System.Linq;
using PCL.Core.App.Localization;
using PCL.Core.Utils;
using PCL.Network;
using PCL.Network.Loaders;
using PCL.Core.IO.Net.Http;

namespace PCL;

/// <summary>
/// Reads stable x64 updates from this fork's custom GitHub Releases.
/// </summary>
public sealed class UpdatesGitHubReleaseModel : IUpdateSource
{
    private const string ReleasesApi = "https://api.github.com/repos/Luoning77/PCL-CE-LUO/releases?per_page=100";
    private const string TagPrefix = "pcl-ce-";
    private const string TagSuffix = "-custom-x64";

    private JsonObject? _release;
    private string? _assetName;
    private string? _assetUrl;
    private string? _sha256;

    public string SourceName { get; set; } = "Luoning77/PCL-CE-LUO";

    public bool IsAvailable() => true;

    public bool RefreshCache()
    {
        var releases = Requester.FetchJson(ReleasesApi, RequestParam.WithRetry).AsArray();
        foreach (var release in releases)
        {
            var tag = release?["tag_name"]?.ToString() ?? string.Empty;
            if (!tag.StartsWith(TagPrefix, StringComparison.Ordinal) ||
                !tag.EndsWith(TagSuffix, StringComparison.Ordinal))
                continue;

            _release = release!.AsObject();
            _assetName = null;
            _assetUrl = null;
            _sha256 = null;
            return true;
        }

        throw new Exception("No custom x64 release found in Luoning77/PCL-CE-LUO.");
    }

    public VersionDataModel GetLatestVersion(UpdateChannel channel, UpdateArch arch)
    {
        EnsureRelease();
        _ = GetAssetUrl();
        var tag = _release!["tag_name"]!.ToString();
        var versionName = tag[TagPrefix.Length..^TagSuffix.Length];
        var releaseVersion = versionName.StartsWith("v", StringComparison.OrdinalIgnoreCase)
            ? versionName[1..]
            : versionName;

        return new VersionDataModel
        {
            Source = SourceName,
            VersionName = releaseVersion,
            VersionCode = 0,
            Sha256 = GetSha256(),
            Changelog = _release["body"]?.ToString() ?? string.Empty
        };
    }

    public bool IsLatest(UpdateChannel channel, UpdateArch arch, SemVer currentVersion, int currentVersionCode)
    {
        var latestVersion = GetLatestVersion(channel, arch);
        return currentVersion >= SemVer.Parse(latestVersion.VersionName);
    }

    public VersionAnnouncementDataModel GetAnnouncementList()
    {
        throw new Exception("GitHub Releases source does not provide announcements.");
    }

    public List<ModLoader.LoaderBase> GetDownloadLoader(UpdateChannel channel, UpdateArch arch, string output)
    {
        EnsureRelease();
        var download = new DownloadFile(new[] { GetAssetUrl() }, output);
        return new List<ModLoader.LoaderBase>
        {
            new LoaderDownload(Lang.Text("Update.Task.DownloadUpdateFile"), new List<DownloadFile> { download })
        };
    }

    private void EnsureRelease()
    {
        if (_release is null)
            RefreshCache();
    }

    private string GetAssetUrl()
    {
        if (_assetUrl is not null)
            return _assetUrl;

        var release = _release ?? throw new InvalidOperationException("Release metadata is unavailable.");
        foreach (var asset in release["assets"]!.AsArray())
        {
            var name = asset?["name"]?.ToString() ?? string.Empty;
            if (name == "PCL2_CE_Release_x64.exe")
            {
                _assetName = name;
                _assetUrl = asset!["browser_download_url"]!.ToString();
                return _assetUrl;
            }
        }

        throw new Exception("The latest custom x64 release has no launcher executable.");
    }

    private string GetSha256()
    {
        if (_sha256 is not null)
            return _sha256;

        var checksumAsset = _release!["assets"]!.AsArray()
            .FirstOrDefault(asset => asset?["name"]?.ToString() == "SHA256SUMS.txt");
        if (checksumAsset is null)
            throw new Exception("The latest custom x64 release has no SHA256SUMS.txt.");

        using var response = HttpRequest.Create(checksumAsset["browser_download_url"]!.ToString())
            .SendAsync()
            .GetAwaiter()
            .GetResult();
        var checksumText = response.AsString();
        var line = checksumText.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries)
            .FirstOrDefault(item => item.EndsWith("  " + _assetName, StringComparison.Ordinal) ||
                                    item.EndsWith(" *" + _assetName, StringComparison.Ordinal));
        _sha256 = line?.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries).FirstOrDefault();
        if (string.IsNullOrWhiteSpace(_sha256))
            throw new Exception("The launcher SHA256 is missing from SHA256SUMS.txt.");
        return _sha256;
    }
}
