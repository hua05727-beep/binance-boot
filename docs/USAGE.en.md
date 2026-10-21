# Usage

中文: [README.md](../README.md) / [docs/USAGE.md](USAGE.md)

This is the from-scratch command sequence for the Binance boot animation on Windows, plus the meaning of every `launcher.json` field. The overview is [README.en.md](../README.en.md).

Run every command in **Windows PowerShell**. The current directory is the repository root (the folder that contains `scripts` and `config`).

## 1. Check the environment

```powershell
[Environment]::OSVersion.Version
# Major version 10 means Windows 10 or 11

Test-Path "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
# Expect True. The .NET Framework 4.8 compiler lives in this 4.0.30319 directory.
```

If that is `False`, install [.NET Framework 4.8](https://dotnet.microsoft.com/download/dotnet-framework/net48), open a new PowerShell window, and test again.

The Binance desktop client must already be installed, and you must be able to open it yourself.

## 2. Get the source

```powershell
git clone https://github.com/hua05727-beep/binance-boot.git
cd binance-boot
```

Without Git, download <https://github.com/hua05727-beep/binance-boot/archive/refs/heads/main.zip> in a browser, unzip, and enter the extracted folder.

## 3. Download both videos

Release page: <https://github.com/hua05727-beep/binance-boot/releases/tag/v1.0.0>

```powershell
New-Item -ItemType Directory -Force media | Out-Null
curl.exe -L -o media\startup.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup.mp4
curl.exe -L -o media\startup_nomusic.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup_nomusic.mp4
```

Check them:

```powershell
(Get-Item media\startup.mp4).Length
# 32349183

(Get-Item media\startup_nomusic.mp4).Length
# 32341666

Get-FileHash media\startup.mp4 -Algorithm SHA256
# 48C563F53A80AA29DAEFFD3A46C1B8582FB5AC3C33E30469D33DA28A4E18B165

Get-FileHash media\startup_nomusic.mp4 -Algorithm SHA256
# 1FFEA2B2D58EE1CB72A27B2661D4D6326520864F7C4CD92C2A8E25FCBA06A3C2
```

Download again when the length or hash differs. Keep both files. The music switch selects between them.

## 4. Find Binance.exe and write the config

With Binance running:

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.ExecutablePath -like '*Binance*' } |
  Select-Object Name, ExecutablePath | Format-List
```

Write down `ExecutablePath`. You can also use the shortcut: Start menu → right-click Binance → **Open file location** → if that is still a shortcut, open **Properties → Target**.

Open `config\launcher.binance.json` and change only the three fields below. Write backslashes as `\\`, and save as UTF-8.

Placeholder (replace it with the path from the previous step):

```json
"AppLaunch": "C:\\Program Files\\Binance\\Binance.exe",
"ProcessPathContains": "\\Binance\\Binance.exe",
"ProcessNames": ["Binance"]
```

How they map:

- `AppLaunch` is the full `ExecutablePath`. A per-user install is often `C:\\Users\\YourName\\AppData\\Local\\Binance\\Binance.exe`.
- `ProcessNames` is `Name` without `.exe`. `Binance.exe` becomes `["Binance"]`.
- `ProcessPathContains` is a distinctive fragment of the full path. The default `\\Binance\\Binance.exe` matches both common locations above.

Read the file again after saving and confirm the JSON is still valid (commas and quotes intact).

## 5. Build

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Success prints `Built:` and the full path of `build\BinanceBoot\BinanceBoot.exe`.

This step produces the exe. It may also copy a config and `startup.mp4`, but only when the output file is not already there, and it never copies the no-music video. Always run the next step so you do not keep a half-updated output folder.

## 6. Copy config, videos, and the toggle next to the exe

```powershell
New-Item -ItemType Directory -Force build\BinanceBoot\media | Out-Null
Copy-Item media\startup.mp4, media\startup_nomusic.mp4 build\BinanceBoot\media\ -Force
Copy-Item config\launcher.binance.json build\BinanceBoot\launcher.json -Force
Copy-Item toggle-music.ps1, Toggle-Music.vbs build\BinanceBoot\ -Force
Get-ChildItem build\BinanceBoot, build\BinanceBoot\media | Select-Object FullName, Length
```

If you later edit only `config\launcher.binance.json`, run the `Copy-Item ... launcher.json` line again. No rebuild. If you replace an mp4, copy `media` again.

## 7. Run

Close Binance if it is open, then:

```powershell
.\build\BinanceBoot\BinanceBoot.exe
```

What you should see:

1. A borderless animation window in the center of the screen, with 「跳过」 (Skip) at the top right.
2. Binance starts. If a matching main window is already open, that window is used.
3. Around 22.9 seconds, if the window is not stable yet, playback pauses and shows 「Binance正在启动… Esc跳过」.
4. After the window is stable, playback continues. From about 23.0 seconds to 24.95 seconds the Binance window fades in and the animation window closes.

Esc, or the Skip button, hands the foreground to Binance immediately. Log:

```powershell
Get-Content .\build\BinanceBoot\logs\launcher.log -Tail 30
```

If a second launch shows no window, end the existing `BinanceBoot.exe` and start again. A mutex allows only one instance.

## 8. Toggle music

```powershell
powershell -ExecutionPolicy Bypass -File .\build\BinanceBoot\toggle-music.ps1
powershell -ExecutionPolicy Bypass -File .\build\BinanceBoot\toggle-music.ps1 -Set On
powershell -ExecutionPolicy Bypass -File .\build\BinanceBoot\toggle-music.ps1 -Set Off
```

Or double-click `build\BinanceBoot\Toggle-Music.vbs` in File Explorer. The vbs runs `toggle-music.ps1` in the same folder.

| Popup text | `Music` | `Video` |
|------------|---------|---------|
| 开机音乐：已开启 (music on) | `true` | `media/startup.mp4` |
| 开机音乐：已关闭 (music off) | `false` | `media/startup_nomusic.mp4` |

If the `AppLaunch` file does not exist yet, the switch still saves and adds a warning line. After you correct the path, copy `launcher.json` again, or edit `build\BinanceBoot\launcher.json` directly.

The no-music file has no background music. Effects are still there. Set `Volume` to `0` for silence.

## 9. Optional desktop shortcut

```powershell
$desktop = [Environment]::GetFolderPath('Desktop')
$root = (Resolve-Path .\build\BinanceBoot).Path
$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut((Join-Path $desktop 'Binance Boot.lnk'))
$lnk.TargetPath = Join-Path $root 'BinanceBoot.exe'
$lnk.WorkingDirectory = $root
$lnk.IconLocation = "$root\BinanceBoot.exe,0"
$lnk.Save()
Write-Output (Join-Path $desktop 'Binance Boot.lnk')
```

Leave `AutoReplaceEntrypoints` at `false`. The program will not replace your original Binance icon. Open this “Binance Boot” shortcut when you want the animation.

## launcher.json fields

At run time the exe reads `build\BinanceBoot\launcher.json`. In the repository, edit `config\launcher.binance.json`, then copy it over. Encoding is UTF-8.

| Field | Example | Meaning |
|-------|---------|---------|
| `Music` | `true` | Used by `toggle-music.ps1`. `true` selects the music video, `false` the no-music video. The launcher itself follows `Video`. |
| `Video` | `media/startup.mp4` | Path relative to the exe folder. The file must exist. The toggle rewrites this to `media/startup.mp4` or `media/startup_nomusic.mp4`. |
| `AppLaunch` | `C:\\Program Files\\Binance\\Binance.exe` | Program to open. It must be an absolute `.exe` path starting with a drive letter. If the file is missing, the animation still plays and hands the path to File Explorer, which usually reports that the file cannot be found. No Binance window appears, so the picture stays at `HoldAt`. |
| `ProcessPathContains` | `\\Binance\\Binance.exe` | Fragment searched inside the process image path. Case-insensitive. It must occur in the real `ExecutablePath`. |
| `ProcessNames` | `["Binance"]` | Process name without `.exe`. Only letters, digits, spaces, `_`, `.`, and `-`. A Chinese display name cannot go here. |
| `HoldAt` | `22.9` | Greater than 0. Pause at this second while the Binance window is not ready. |
| `TransitionStart` | `23.0` | Crossfade start. Must be greater than `HoldAt`. |
| `TransitionEnd` | `24.95` | Crossfade end. Must be greater than `TransitionStart`. The animation window then closes. |
| `MaxWaitSeconds` | `60` | At least 10. If the window never qualifies, waiting ends about this many seconds plus 20. |
| `Volume` | `1` | Volume, from 0 to 1. |
| `PlayerWidth` | `1920` | Player width in physical pixels, 450–7680. |
| `PlayerHeight` | `1080` | Player height in physical pixels, 280–4320. Change it together with the width. Keep 16:9. |
| `MatchClientToPlayer` | `true` | Align the Binance client area to the player before the fade. |
| `ScreenFrames` | see below | At least two frames, with increasing `Time`. `X` / `Y` / `Width` / `Height` are 0–1 relative coordinates, and the rectangle must stay inside the frame. The default two frames are the full picture, so the fade fills the player. |
| `DisplayName` | `Binance 开机动画` | Window title. If it contains Chinese, the whole json file must be UTF-8. |
| `AutoReplaceEntrypoints` | `false` | Leave this `false`. `true` makes the launcher try to rewrite shortcuts that point at Binance. |
| `ScanAllLocalDrives` | `false` | Leave this `false`. A full-disk scan is used only by that shortcut rewrite. |

Leave the default screen keyframes as they are:

```json
"ScreenFrames": [
  {"Time": 23.0, "X": 0, "Y": 0, "Width": 1, "Height": 1},
  {"Time": 24.95, "X": 0, "Y": 0, "Width": 1, "Height": 1}
]
```

Illegal timing shows 「启动时间配置不正确」. A process name that is empty or contains Chinese shows 「视频路径或进程匹配配置无效」. If `AppLaunch` is neither an absolute exe path nor a `shell:AppsFolder\Package!App` id, the dialog mentions `shell:AppsFolder`. For a normal install, use the absolute exe path.

## Log lines

| Log | Meaning |
|-----|---------|
| `app-launch-requested` | A launch of `AppLaunch` was requested |
| `app-launch-failed` | The launch command failed. The picture says to press Esc to exit |
| `waiting-for-window` | Playback reached `HoldAt` and no suitable Binance main window exists yet |
| `window-available` | The window is stable, so playback continues |
| `live-window-connected` | The desktop thumbnail is connected and the crossfade can run |
| `wait-timeout` | More than `MaxWaitSeconds + 20` seconds passed, so waiting stopped |
| `media-open-timeout` / `media-failed` | The video could not be opened |
| `handed-off-to-real-window` | The foreground was given to Binance |

Symptom notes: [Troubleshooting in the English README](../README.en.md#troubleshooting).
