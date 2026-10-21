# 使用说明

这份文档是在 Windows 上从零跑通币安开机动画的命令步骤，以及 `launcher.json` 每个字段的含义。概览见仓库根目录的 [README.md](../README.md)。

下面所有命令都在 **Windows PowerShell** 里执行，并且假设当前目录是仓库根目录（能看到 `scripts` 和 `config` 的那一层）。

## 1. 确认环境

```powershell
[Environment]::OSVersion.Version
# 主版本 10 即 Windows 10/11

Test-Path "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
# 应输出 True。.NET Framework 4.8 的编译器就在这个 4.0.30319 目录里。
```

若是 `False`，先安装 [.NET Framework 4.8](https://dotnet.microsoft.com/download/dotnet-framework/net48)，重新打开 PowerShell 再测一次。

币安桌面客户端需要已经安装，并且你平时能自己打开它。

## 2. 取得源码

```powershell
git clone https://github.com/hua05727-beep/binance-boot.git
cd binance-boot
```

没有 Git 时，用浏览器下载 <https://github.com/hua05727-beep/binance-boot/archive/refs/heads/main.zip>，解压，进入解压出来的文件夹。

## 3. 下载两个视频

发布页：<https://github.com/hua05727-beep/binance-boot/releases/tag/v1.0.0>

```powershell
New-Item -ItemType Directory -Force media | Out-Null
curl.exe -L -o media\startup.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup.mp4
curl.exe -L -o media\startup_nomusic.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup_nomusic.mp4
```

核对：

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

长度或哈希不一致时重新下载。两个文件都要保留：开关音乐时会在它们之间切换。

## 4. 查出币安 exe，并写入配置

币安开着时执行：

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.ExecutablePath -like '*Binance*' } |
  Select-Object Name, ExecutablePath | Format-List
```

记下 `ExecutablePath`。也可以从快捷方式查：开始菜单 → 右键币安 → **打开文件所在的位置** → 若仍是快捷方式，再 **属性 → 目标**。

用编辑器打开 `config\launcher.binance.json`，只改下面三项。反斜杠写成 `\\`，保存为 UTF-8。

占位示例（请替换成上一步得到的路径）：

```json
"AppLaunch": "C:\\Program Files\\Binance\\Binance.exe",
"ProcessPathContains": "\\Binance\\Binance.exe",
"ProcessNames": ["Binance"]
```

对照关系：

- `AppLaunch` = `ExecutablePath` 的完整文字。安装在用户目录时往往是 `C:\\Users\\你的用户名\\AppData\\Local\\Binance\\Binance.exe`。
- `ProcessNames` = `Name` 去掉 `.exe`。`Binance.exe` 就写 `["Binance"]`。
- `ProcessPathContains` = 完整路径里独特的一段。默认 `\\Binance\\Binance.exe` 能匹配上面两种常见安装位置。

保存后再读一遍，确认 JSON 仍然是合法的（逗号、引号都在）。

## 5. 编译

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

成功时输出 `Built:` 加上 `build\BinanceBoot\BinanceBoot.exe` 的完整路径。

这一步只生成 exe。它可能顺手复制一份配置和 `startup.mp4`，但规则是「输出位置还没有文件才复制」，而且不会复制无音乐视频。下一步每次都执行，避免用到半份旧文件。

## 6. 把配置、视频和开关复制到 exe 旁边

```powershell
New-Item -ItemType Directory -Force build\BinanceBoot\media | Out-Null
Copy-Item media\startup.mp4, media\startup_nomusic.mp4 build\BinanceBoot\media\ -Force
Copy-Item config\launcher.binance.json build\BinanceBoot\launcher.json -Force
Copy-Item toggle-music.ps1, Toggle-Music.vbs build\BinanceBoot\ -Force
Get-ChildItem build\BinanceBoot, build\BinanceBoot\media | Select-Object FullName, Length
```

之后若只改了 `config\launcher.binance.json`，重新执行上面的 `Copy-Item ... launcher.json` 即可，不用编译。换了 mp4 就重新复制 `media`。

## 7. 运行

先关掉已经打开的币安，再执行：

```powershell
.\build\BinanceBoot\BinanceBoot.exe
```

正常过程：

1. 屏幕中央出现无边框动画窗口，右上角有「跳过」。
2. 币安被启动（若当时已经有一个匹配的主窗口，就直接用它）。
3. 约 22.9 秒时，如果窗口还没稳定，画面暂停并显示「Binance正在启动… Esc跳过」。
4. 窗口稳定后继续播放。约 23.0 秒到 24.95 秒，币安画面渐显，动画窗口关闭。

按 Esc 或点「跳过」会马上交到币安。日志：

```powershell
Get-Content .\build\BinanceBoot\logs\launcher.log -Tail 30
```

第二次启动没有任何窗口时，结束已有的 `BinanceBoot.exe` 再开。程序用互斥体保证同时只有一份。

## 8. 开关音乐

```powershell
powershell -ExecutionPolicy Bypass -File .\build\BinanceBoot\toggle-music.ps1
powershell -ExecutionPolicy Bypass -File .\build\BinanceBoot\toggle-music.ps1 -Set On
powershell -ExecutionPolicy Bypass -File .\build\BinanceBoot\toggle-music.ps1 -Set Off
```

或在资源管理器中双击 `build\BinanceBoot\Toggle-Music.vbs`。这个 vbs 会调用同一文件夹里的 `toggle-music.ps1`。

| 弹出文字 | `Music` | `Video` |
|----------|---------|---------|
| 开机音乐：已开启 | `true` | `media/startup.mp4` |
| 开机音乐：已关闭 | `false` | `media/startup_nomusic.mp4` |

`AppLaunch` 的文件还不存在时，开关照样保存，并多一行警告。把路径改好后再次复制 `launcher.json`，或直接改 `build\BinanceBoot\launcher.json`。

无音乐版本没有背景音乐，音效还在。要完全静音，把 `Volume` 设为 `0`。

## 9. 可选：桌面快捷方式

```powershell
$desktop = [Environment]::GetFolderPath('Desktop')
$root = (Resolve-Path .\build\BinanceBoot).Path
$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut((Join-Path $desktop '币安开机动画.lnk'))
$lnk.TargetPath = Join-Path $root 'BinanceBoot.exe'
$lnk.WorkingDirectory = $root
$lnk.IconLocation = "$root\BinanceBoot.exe,0"
$lnk.Save()
Write-Output (Join-Path $desktop '币安开机动画.lnk')
```

`AutoReplaceEntrypoints` 保持 `false`。不要指望程序去替换你原来的币安图标；每天从「币安开机动画」这个快捷方式进入即可。

## launcher.json 字段

文件位置：运行时读 `build\BinanceBoot\launcher.json`。仓库里编辑的是 `config\launcher.binance.json`，复制过去之后才生效。编码用 UTF-8。

| 字段 | 示例 | 说明 |
|------|------|------|
| `Music` | `true` | 给 `toggle-music.ps1` 用。`true` 选有音乐视频，`false` 选无音乐视频。启动器本身看的是 `Video`。 |
| `Video` | `media/startup.mp4` | 相对 exe 所在目录的路径，文件必须存在。开关脚本会把它改成 `media/startup.mp4` 或 `media/startup_nomusic.mp4`。 |
| `AppLaunch` | `C:\\Program Files\\Binance\\Binance.exe` | 要打开的程序。必须是盘符开头、以 `.exe` 结尾的绝对路径。文件不存在时动画仍会播放，并转交资源管理器打开该路径（通常弹出找不到文件）。币安窗口不会出现，画面会停在 `HoldAt`。 |
| `ProcessPathContains` | `\\Binance\\Binance.exe` | 在进程完整路径里查找的片段，不区分大小写。必须能命中真实的 `ExecutablePath`。 |
| `ProcessNames` | `["Binance"]` | 进程名，不含 `.exe`。只允许英文字母、数字、空格、`_`、`.`、`-`。中文显示名不能写在这里。 |
| `HoldAt` | `22.9` | 大于 0。币安窗口未就绪时，暂停在这一秒。 |
| `TransitionStart` | `23.0` | 交叉淡化开始，必须大于 `HoldAt`。 |
| `TransitionEnd` | `24.95` | 交叉淡化结束，必须大于 `TransitionStart`。结束后关闭动画窗口。 |
| `MaxWaitSeconds` | `60` | 不小于 10。窗口一直不合格时，大约在该秒数再加 20 秒后结束等待。 |
| `Volume` | `1` | 音量，0 到 1。 |
| `PlayerWidth` | `1920` | 播放窗口宽度，物理像素，450–7680。 |
| `PlayerHeight` | `1080` | 播放窗口高度，物理像素，280–4320。与宽度一起改，建议保持 16:9。 |
| `MatchClientToPlayer` | `true` | 淡化前把币安窗口客户区对齐到播放窗口。 |
| `ScreenFrames` | 见下方 | 至少两帧，`Time` 递增。`X`/`Y`/`Width`/`Height` 是 0–1 的相对坐标，矩形不能超出画面。默认两帧都是整幅，淡化铺满播放器。 |
| `DisplayName` | `Binance 开机动画` | 窗口标题。含中文时，整个 json 必须是 UTF-8。 |
| `AutoReplaceEntrypoints` | `false` | 保持 `false`。设为 `true` 时，启动器会尝试改写指向币安的快捷方式。 |
| `ScanAllLocalDrives` | `false` | 保持 `false`。只有在改写快捷方式时才会用到全盘扫描。 |

默认的画面关键帧不用改：

```json
"ScreenFrames": [
  {"Time": 23.0, "X": 0, "Y": 0, "Width": 1, "Height": 1},
  {"Time": 24.95, "X": 0, "Y": 0, "Width": 1, "Height": 1}
]
```

时间字段不合法时，程序弹窗「启动时间配置不正确」。进程名含中文或空字符串时，弹窗「视频路径或进程匹配配置无效」。`AppLaunch` 既不是绝对路径 exe、也不是 `shell:AppsFolder\包名!应用名` 这种标识时，弹窗会提到 `shell:AppsFolder`。日常安装填绝对路径 exe 即可。

## 常见日志

| 日志 | 含义 |
|------|------|
| `app-launch-requested` | 已请求启动 `AppLaunch` |
| `app-launch-failed` | 启动命令失败，画面上会提示按 Esc 退出 |
| `waiting-for-window` | 已到 `HoldAt`，还没有合格的币安主窗口 |
| `window-available` | 窗口已稳定，继续播放 |
| `live-window-connected` | 桌面缩略图已接上，可以交叉淡化 |
| `wait-timeout` | 超过 `MaxWaitSeconds + 20` 秒，放弃等待 |
| `media-open-timeout` / `media-failed` | 视频打不开 |
| `handed-off-to-real-window` | 已把前台交给币安 |

更多症状对照见 [README 的排错](../README.md#排错)。
