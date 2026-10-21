# binance-boot

中文: [README.md](README.md) / [docs/USAGE.md](docs/USAGE.md)

Unofficial fan-made Binance desktop boot animation for Windows. It plays about 25 seconds of black-and-gold intro (poster, then a BTC candlestick sequence, then the Binance mark), then crossfades for about 2 seconds into the real Binance window.

> This project is not affiliated with, endorsed by, or sponsored by Binance. Trademark notice: [NOTICE.md](NOTICE.md).

Command-by-command steps and the `launcher.json` field table: [docs/USAGE.en.md](docs/USAGE.en.md). Config and video changes do not need a rebuild.

## Preview

![1080p boot poster](posters/poster_horizontal.png)

The full animation is on the GitHub Release. Open either file in a browser:

- With music: <https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup.mp4>
- Without music (effects only): <https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup_nomusic.mp4>

Still posters in `posters/`: `poster_horizontal.png` (1920×1080), `poster_desktop_2k.png` (2560×1440), `poster_desktop_4k.png` (3840×2160).

## Requirements

- Windows 10 or Windows 11, 64-bit
- [.NET Framework 4.8](https://dotnet.microsoft.com/download/dotnet-framework/net48) (usually already installed; the build uses `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe`)
- The Binance desktop app, already installed, and a shortcut or Start menu entry you can open yourself
- Windows PowerShell 5.1 (built in) and `curl.exe` (built in on Windows 10 and later)

Python is not required. `render/` is the pipeline that produced the video. Day-to-day use does not run it.

## Download

1. Get the source. Either:

```powershell
git clone https://github.com/hua05727-beep/binance-boot.git
cd binance-boot
```

or open <https://github.com/hua05727-beep/binance-boot>, choose **Code → Download ZIP**, unzip, and enter that folder.

2. Download both MP4s into `media\`. They are not stored in the git repository. Release page: <https://github.com/hua05727-beep/binance-boot/releases/tag/v1.0.0>

```powershell
New-Item -ItemType Directory -Force media | Out-Null
curl.exe -L -o media\startup.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup.mp4
curl.exe -L -o media\startup_nomusic.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup_nomusic.mp4
```

You can also download them in a browser from the release page and drop them into `media\` with those exact names. Sizes and SHA256 checksums are in [media/README.en.md](media/README.en.md).

## Configure AppLaunch

Open `config\launcher.binance.json` in Notepad or VS Code and edit these three fields. Save the file as **UTF-8**.

Example (replace this with the real path on your PC):

```json
"AppLaunch": "C:\\Program Files\\Binance\\Binance.exe",
"ProcessPathContains": "\\Binance\\Binance.exe",
"ProcessNames": ["Binance"]
```

In JSON, write each backslash as `\\`. Many installs live under the user profile, for example `C:\\Users\\YourName\\AppData\\Local\\Binance\\Binance.exe`. The path above is only a placeholder. If it does not match your install, the animation stays on “Binance正在启动”.

Find the real path from an existing shortcut:

1. Find Binance in the Start menu, right-click it, and choose **Open file location**.
2. If that opens a shortcut rather than the exe, right-click the shortcut → **Properties** → **Shortcut**, and copy **Target**.
3. If Target is wrapped in quotes, remove the quotes. Put the full path in `AppLaunch`.
4. `ProcessPathContains` is a unique fragment of that path. `\\Binance\\Binance.exe` is enough in the common layouts.
5. `ProcessNames` is the process name from Task Manager, **without** `.exe`. The desktop app is usually `Binance`.

While Binance is already running, confirm the name and path:

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.ExecutablePath -like '*Binance*' } |
  Select-Object Name, ProcessId, ExecutablePath
```

When `Name` is `Binance.exe`, set `ProcessNames` to `["Binance"]`. Put the whole `ExecutablePath` in `AppLaunch`, and make sure that path contains `ProcessPathContains`.

`AppLaunch` must be an absolute path that starts with a drive letter and ends in `.exe`, such as `D:\\Binance\\Binance.exe`. Use the exe path from the shortcut Target. A Start-menu display name, or a bare `Binance.exe`, will not launch the app.

## Build

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

On success the last line looks like `Built: ...\build\BinanceBoot\BinanceBoot.exe`.

`build.ps1` copies `launcher.json` only when that output file is absent, and it copies `media\startup.mp4` only when that output file is absent. It never copies `startup_nomusic.mp4`. Run the copy step below again after every config or video change. Editing the json or replacing an mp4 does not require a rebuild.

## Copy into the output folder

```powershell
New-Item -ItemType Directory -Force build\BinanceBoot\media | Out-Null
Copy-Item media\startup.mp4, media\startup_nomusic.mp4 build\BinanceBoot\media\ -Force
Copy-Item config\launcher.binance.json build\BinanceBoot\launcher.json -Force
Copy-Item toggle-music.ps1, Toggle-Music.vbs build\BinanceBoot\ -Force
```

The launcher reads `launcher.json` and `media\` **next to the exe**. Files left in the repository root are invisible to it.

## First run

Open Binance once yourself and confirm the client appears, then close it. Then run:

```powershell
.\build\BinanceBoot\BinanceBoot.exe
```

A borderless, topmost window of about 1920×1080 plays in the center of a screen while `AppLaunch` starts. If Binance is already open, the player uses the monitor that contains that window. Otherwise it uses the monitor under the mouse. **Skip** at the top right, or **Esc**, ends the animation immediately and brings the Binance window forward.

Only one animation process runs at a time. If a second double-click shows nothing, check Task Manager for an existing `BinanceBoot.exe`.

The log is `build\BinanceBoot\logs\launcher.log`.

### What the last ~2 seconds do

Default timeline, in seconds:

| Field | Default | Meaning |
|-------|---------|---------|
| `HoldAt` | `22.9` | If the Binance main window is not stable yet, playback pauses here and shows “Binance正在启动… Esc跳过”. Playback resumes after the window has been visible and responsive for about 0.6 seconds. |
| `TransitionStart` | `23.0` | Crossfade starts. Must be greater than `HoldAt`. |
| `TransitionEnd` | `24.95` | Crossfade ends, the animation window closes, and Binance stays in front. Must be greater than `TransitionStart`. |
| `MaxWaitSeconds` | `60` | How long to keep waiting for a usable window. Minimum 10. Wall-clock give-up is about `MaxWaitSeconds + 20` seconds (about 80 seconds with the default). |

During the fade, the launcher aligns the Binance client area to the player and composites a Desktop Window Manager thumbnail from transparent to opaque. The default `ScreenFrames` cover the whole picture. Leave them as they are.

The player is a fixed size in physical pixels (default 1920×1080). On a larger monitor it stays a centered window; it does not stretch to fill a 4K screen. On a smaller monitor, lower `PlayerWidth` and `PlayerHeight` together, keep 16:9, and stay at or above 450 and 280.

## Music toggle

In `build\BinanceBoot`, double-click `Toggle-Music.vbs` (no console window), or run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build\BinanceBoot\toggle-music.ps1
```

A popup says 「开机音乐：已开启」 (music on) or 「开机音乐：已关闭」 (music off). The script edits the `launcher.json` beside it:

| `Music` | File played |
|---------|-------------|
| `true` | `media/startup.mp4` (with music) |
| `false` | `media/startup_nomusic.mp4` (no music bed; effects remain) |

You can force a state with `-Set On` or `-Set Off`. `-Quiet` skips the popup.

If `AppLaunch` is still the example path and that exe is not on this PC, the switch still saves and adds a warning that the path is missing. Fix the path, then run `BinanceBoot.exe`. The matching video must already be in `build\BinanceBoot\media\`. If it is missing, the switch fails and leaves the previous config in place.

## Desktop shortcut (optional)

Run this from the repository root. The shortcut points at the built exe, and its working directory is the exe folder:

```powershell
$desktop = [Environment]::GetFolderPath('Desktop')
$root = (Resolve-Path .\build\BinanceBoot).Path
$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut((Join-Path $desktop 'Binance Boot.lnk'))
$lnk.TargetPath = Join-Path $root 'BinanceBoot.exe'
$lnk.WorkingDirectory = $root
$lnk.IconLocation = "$root\BinanceBoot.exe,0"
$lnk.Description = 'Play the Binance boot animation, then open Binance'
$lnk.Save()
```

Later video or config edits stay inside `build\BinanceBoot`. The shortcut does not need to be recreated.

Leave `AutoReplaceEntrypoints` set to `false` in `config\launcher.binance.json` so the launcher does not rewrite your existing Binance shortcuts.

## Troubleshooting

### Binance is not found, or the video stays on “Binance正在启动”

- `AppLaunch` must be an exe that exists. Open that folder in File Explorer and confirm `Binance.exe` is there.
- `ProcessNames` must match the Task Manager process name, without `.exe`, and it must be ASCII (letters, digits, space, `_`, `.`, `-`). The Chinese display name 「币安」 is rejected.
- `ProcessPathContains` must be a fragment of that process’s full path. Matching is case-insensitive. If the fragment is not in the real path, the window is treated as not open yet.
- The Binance main window needs to be large enough (about 450×280 or more). A tray-only process, or a tiny login box, keeps the animation waiting.
- Open `build\BinanceBoot\logs\launcher.log`. `waiting-for-window` means it is waiting. `app-launch-failed` means the launch command itself failed. `wait-timeout` means it gave up after the timeout.

### Silent video, or the wrong file plays

- `Music: true` selects `media/startup.mp4`. `false` selects `media/startup_nomusic.mp4`. The no-music file still has effects; it has no music bed.
- `Volume` is from 0 to 1. Also check the Windows volume mixer for a muted `BinanceBoot.exe`.
- Both mp4s belong in `build\BinanceBoot\media\`. If they exist only in the repository `media\` folder, the launcher reports 「未找到启动视频」.
- Compare size and SHA256 with [media/README.en.md](media/README.en.md) so a partial or swapped download is not used.

### The crossfade never starts

The fade starts only after playback has passed `TransitionStart` **and** a stable Binance main window has been found. Until the window matches, the picture stays at `HoldAt`.

- Fix the three path fields from the previous section, save UTF-8, and copy the file to `build\BinanceBoot\launcher.json`.
- If a cold start of Binance is slow, raise `MaxWaitSeconds` (do not go below 10). The give-up point is about that value plus 20 seconds.
- `HoldAt` must be greater than 0, `TransitionStart` must be greater than `HoldAt`, and `TransitionEnd` must be greater still. Equal values, or the wrong order, show 「启动时间配置不正确」 immediately.
- If the video cannot open within 12 seconds, playback is abandoned and the launcher tries to hand off to Binance. The log line is `media-open-timeout` or `media-failed`.

### Chinese paths look corrupted

Save `launcher.json` as UTF-8. In Notepad choose **UTF-8**, not ANSI. An ANSI/GBK save corrupts Chinese characters in the path, so the file can be sitting on disk while the program says it is missing.

`toggle-music.ps1` also writes UTF-8. It changes only `Music` and `Video`. It leaves `AppLaunch` as it was.

### Antivirus or SmartScreen blocks the exe

The program is unsigned. On the first build or first run, security software may quarantine `BinanceBoot.exe` or `csc.exe`. Allow the repository folder. If SmartScreen says “Windows protected your PC” (「Windows 已保护你的电脑」), choose **More info → Run anyway**. After a quarantine, run `scripts\build.ps1` again, then copy `media` and `launcher.json` back.

## Layout

| Path | Description |
|------|-------------|
| `README.md` | Chinese guide |
| `README.en.md` | This English guide |
| `docs/USAGE.md` | Chinese command walkthrough and `launcher.json` field table |
| `docs/USAGE.en.md` | English command walkthrough and field table |
| `media/README.en.md` | English video download notes |
| `NOTICE.md` | Trademark and media notice |
| `LICENSE` | MIT license |
| `media/` | Folder for the two MP4s; the videos themselves are on the Release |
| `posters/` | 4K / 2K / 1080p posters |
| `config/launcher.binance.json` | Example config to edit |
| `launcher.json.example` | The same example |
| `src/BinanceBoot.cs` | Launcher source |
| `src/binance.ico`, `src/app.manifest` | Icon and DPI manifest |
| `scripts/build.ps1` | Builds `build\BinanceBoot\BinanceBoot.exe` |
| `toggle-music.ps1`, `Toggle-Music.vbs` | Music switch; copy them into the build output before use |
| `render/` | Python scripts that generated the v6 video and posters; not needed to run the launcher |
| `build/` | Build output, ignored by `.gitignore` |

## Credits

- The Windows launcher structure comes from [dragon-codex-boot](https://github.com/yushua0808-cpu/dragon-codex-boot) (MIT).
- Animation and packaging were prepared with Grok Bot.

## License

MIT. See [LICENSE](LICENSE). Trademark and unofficial-project notice: [NOTICE.md](NOTICE.md).
