# binance-boot

English: [README.en.md](README.en.md) / [docs/USAGE.en.md](docs/USAGE.en.md)

**English:** Unofficial fan-made Binance desktop boot animation for Windows. About 25 seconds of black-and-gold intro, then a 2-second crossfade into the real Binance window. Download `startup.mp4` and `startup_nomusic.mp4` from the [v1.0.0 release](https://github.com/hua05727-beep/binance-boot/releases/tag/v1.0.0) into `media/`. Not affiliated with Binance — see [NOTICE.md](NOTICE.md). The full English guide is [README.en.md](README.en.md). The English command walkthrough and `launcher.json` field table are in [docs/USAGE.en.md](docs/USAGE.en.md). Video checksums: [media/README.en.md](media/README.en.md).

非官方的 Windows 币安桌面端开机动画。先播放约 25 秒黑金开场（海报 → BTC K 线 → Binance 标志），最后约 2 秒交叉淡化进真正的币安窗口。

> 本项目与 Binance 无关，未获授权、背书或赞助。商标说明见 [NOTICE.md](NOTICE.md)。

按命令逐步操作见 [docs/USAGE.md](docs/USAGE.md)。改配置或换视频不用重新编译。

## 预览

![1080p 开机海报](posters/poster_horizontal.png)

完整动画在 Release 里，浏览器打开即可播放：

- 有音乐：<https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup.mp4>
- 无音乐（仅音效）：<https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup_nomusic.mp4>

静态海报在 `posters/`：`poster_horizontal.png`（1920×1080）、`poster_desktop_2k.png`（2560×1440）、`poster_desktop_4k.png`（3840×2160）。

## 环境要求

- Windows 10 或 Windows 11，64 位
- 已安装 [.NET Framework 4.8](https://dotnet.microsoft.com/download/dotnet-framework/net48)（系统通常自带；编译用的是 `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe`）
- 币安桌面客户端已经装好，并且你自己能从开始菜单或快捷方式打开它
- Windows PowerShell 5.1（系统自带）和 `curl.exe`（Windows 10 及以上自带）

不需要 Python。`render/` 只是当初做视频的脚本，日常使用用不到。

## 下载

1. 取得源码。任选一种：

```powershell
git clone https://github.com/hua05727-beep/binance-boot.git
cd binance-boot
```

或者打开 <https://github.com/hua05727-beep/binance-boot>，点 **Code → Download ZIP**，解压后进入该文件夹。

2. 把两个 MP4 下载到 `media\`。它们不在 git 仓库里。发布页：<https://github.com/hua05727-beep/binance-boot/releases/tag/v1.0.0>

```powershell
New-Item -ItemType Directory -Force media | Out-Null
curl.exe -L -o media\startup.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup.mp4
curl.exe -L -o media\startup_nomusic.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup_nomusic.mp4
```

也可以在发布页用浏览器下载，再把文件放进 `media\`，文件名保持 `startup.mp4` 和 `startup_nomusic.mp4`。核对大小和 SHA256 的方法写在 [media/README.md](media/README.md)。

## 填写币安程序路径

用记事本或 VS Code 打开 `config\launcher.binance.json`，改这三项。文件请另存为 **UTF-8**。

示例（请换成你电脑上的真实路径）：

```json
"AppLaunch": "C:\\Program Files\\Binance\\Binance.exe",
"ProcessPathContains": "\\Binance\\Binance.exe",
"ProcessNames": ["Binance"]
```

JSON 里反斜杠要写成 `\\`。很多安装实际在用户目录，例如 `C:\\Users\\你的用户名\\AppData\\Local\\Binance\\Binance.exe`。下面的路径只是占位，对不上就会一直停在「Binance正在启动」。

从已有快捷方式查出真实路径：

1. 开始菜单里找到币安，右键，选 **打开文件所在的位置**。
2. 如果打开的是快捷方式而不是 exe，再右键该快捷方式 → **属性** → **快捷方式** → 复制 **目标**。
3. 目标里若包着引号，去掉引号。`AppLaunch` 填这个完整路径。
4. `ProcessPathContains` 填路径里一段不会撞车的文字，一般用 `\\Binance\\Binance.exe` 即可。
5. `ProcessNames` 填任务管理器里的进程名，**不要**带 `.exe`。币安桌面端通常是 `Binance`。

币安已经开着时，可以用这一段确认名字和路径：

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.ExecutablePath -like '*Binance*' } |
  Select-Object Name, ProcessId, ExecutablePath
```

`Name` 是 `Binance.exe` 时，`ProcessNames` 写 `["Binance"]`。`ExecutablePath` 整段填进 `AppLaunch`，并保证它包含 `ProcessPathContains`。

`AppLaunch` 必须是盘符开头、以 `.exe` 结尾的绝对路径，例如 `D:\\Binance\\Binance.exe`。不要填开始菜单里的显示名，也不要只写 `Binance.exe`。

## 编译

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

成功时最后一行类似 `Built: ...\build\BinanceBoot\BinanceBoot.exe`。

`build.ps1` 只会在输出目录还没有 `launcher.json` 时复制一份配置，并且只会在还没有 `media\startup.mp4` 时复制有音乐的那一条。它不会复制 `startup_nomusic.mp4`。所以下面的复制步骤每次改完配置或视频都要再做一次。改 json 或换 mp4 不用重新编译。

## 复制到输出目录

```powershell
New-Item -ItemType Directory -Force build\BinanceBoot\media | Out-Null
Copy-Item media\startup.mp4, media\startup_nomusic.mp4 build\BinanceBoot\media\ -Force
Copy-Item config\launcher.binance.json build\BinanceBoot\launcher.json -Force
Copy-Item toggle-music.ps1, Toggle-Music.vbs build\BinanceBoot\ -Force
```

启动器只读 **exe 旁边** 的 `launcher.json` 和 `media\`。仓库根目录里的文件它看不到。

## 第一次运行

先自己打开一次币安，确认客户端能正常出现，然后关掉它。再运行：

```powershell
.\build\BinanceBoot\BinanceBoot.exe
```

你会看到一个无边框、置顶、大约 1920×1080 的窗口在屏幕正中播放动画，同时去启动 `AppLaunch`。币安已经开着时，窗口出现在币安所在的那块屏幕上；否则出现在鼠标所在的屏幕上。右上角 **跳过** 或按 **Esc** 会立刻结束动画并把币安窗口调到前台。

同一时间只能有一个动画进程。第二次双击若没有任何窗口，看一下任务管理器里是否已有 `BinanceBoot.exe`。

日志写在 `build\BinanceBoot\logs\launcher.log`。

### 最后约 2 秒在做什么

默认时间轴（单位：秒）：

| 字段 | 默认 | 含义 |
|------|------|------|
| `HoldAt` | `22.9` | 币安主窗口还没稳定时，画面停在这里，并显示「Binance正在启动… Esc跳过」。窗口连续约 0.6 秒可见且有响应后继续播放。 |
| `TransitionStart` | `23.0` | 交叉淡化开始。必须大于 `HoldAt`。 |
| `TransitionEnd` | `24.95` | 淡化结束，动画窗口关闭，币安留在前台。必须大于 `TransitionStart`。 |
| `MaxWaitSeconds` | `60` | 一直等不到合格窗口时的等待预算，至少为 10。墙钟大约到 `MaxWaitSeconds + 20` 秒（默认约 80 秒）会放弃等待并关闭动画。 |

淡化期间，程序把币安窗口客户区对齐到播放器，再用系统桌面缩略图从透明渐变到不透明。默认 `ScreenFrames` 覆盖整幅画面，一般不用改。

播放窗口是固定的物理像素（默认 1920×1080），在更大的显示器上是居中窗口，不会自动铺满 4K 屏幕。显示器比这个小的话，把 `PlayerWidth` 和 `PlayerHeight` 一起改小，并保持 16:9，且分别不小于 450 和 280。

## 开关音乐

在 `build\BinanceBoot` 里双击 `Toggle-Music.vbs`（没有黑色命令行窗口），或执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build\BinanceBoot\toggle-music.ps1
```

弹出「开机音乐：已开启」或「开机音乐：已关闭」。脚本改的是它旁边的 `launcher.json`：

| `Music` | 播放的文件 |
|---------|------------|
| `true` | `media/startup.mp4`（有音乐） |
| `false` | `media/startup_nomusic.mp4`（无音乐，仍有音效） |

也可以指定状态：`-Set On`、`-Set Off`。`-Quiet` 不弹窗。

`AppLaunch` 还是示例路径、本机没有这个 exe 时，开关仍然会保存，并额外提示路径不存在。把路径改对后再运行 `BinanceBoot.exe`。对应的视频文件必须已经在 `build\BinanceBoot\media\` 里，否则切换会失败并保持原配置。

## 桌面快捷方式（可选）

在仓库根目录执行。快捷方式指向编译出来的 exe，工作目录设成 exe 所在文件夹：

```powershell
$desktop = [Environment]::GetFolderPath('Desktop')
$root = (Resolve-Path .\build\BinanceBoot).Path
$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut((Join-Path $desktop '币安开机动画.lnk'))
$lnk.TargetPath = Join-Path $root 'BinanceBoot.exe'
$lnk.WorkingDirectory = $root
$lnk.IconLocation = "$root\BinanceBoot.exe,0"
$lnk.Description = '播放币安开机动画后进入币安'
$lnk.Save()
```

以后改视频或配置，仍然改 `build\BinanceBoot` 里的文件，不用重建快捷方式。

`config\launcher.binance.json` 里的 `AutoReplaceEntrypoints` 请保持 `false`，避免启动器去改写你现有的币安快捷方式。

## 排错

### 找不到币安，或一直停在「Binance正在启动」

- `AppLaunch` 必须是真实存在的 exe。资源管理器地址栏进到该文件夹，确认里面有 `Binance.exe`。
- `ProcessNames` 与任务管理器进程名一致，不带 `.exe`，并且是英文数字（不能写「币安」）。
- `ProcessPathContains` 必须是该进程完整路径中的一段，大小写不限。路径片段和真实路径不一致时，窗口会被当成「还没开」。
- 币安主窗口要够大（大约不小于 450×280）。停在托盘、或只有一个很小的登录框时，动画会继续等待。
- 打开 `build\BinanceBoot\logs\launcher.log`。出现 `waiting-for-window` 表示在等窗口；出现 `app-launch-failed` 表示启动命令本身失败；出现 `wait-timeout` 表示等到超时后放弃。

### 没有声音，或放成了另一条片

- `Music: true` 对应 `media/startup.mp4`，`false` 对应 `media/startup_nomusic.mp4`。无音乐那条仍有音效，只是没有背景音乐。
- `Volume` 范围是 0 到 1。同时看一下 Windows 音量合成器里 `BinanceBoot.exe` 是否被静音。
- 两个 mp4 都要放在 `build\BinanceBoot\media\`。只放在仓库的 `media\` 时，启动器会提示「未找到启动视频」。
- 用 [media/README.md](media/README.md) 里的大小和 SHA256 确认没有下错文件或下了一半。

### 交叉淡化一直不开始

淡化要同时满足：播放过了 `TransitionStart`，并且已经找到稳定的币安主窗口。窗口没对上时，画面会停在 `HoldAt`。

- 按上一节改好三个路径字段，保存为 UTF-8，再复制到 `build\BinanceBoot\launcher.json`。
- 币安冷启动很慢时，把 `MaxWaitSeconds` 调大（不要小于 10）。超时点大约是这个值再加 20 秒。
- `HoldAt` 必须大于 0，`TransitionStart` 必须大于 `HoldAt`，`TransitionEnd` 必须再大一些。三个数挨得太近或顺序反了，程序会直接提示「启动时间配置不正确」。
- 视频 12 秒内打不开时会放弃播放并尝试切到币安。日志里对应 `media-open-timeout` 或 `media-failed`。

### 中文路径乱码

`launcher.json` 用 UTF-8 保存。记事本请选 **UTF-8**，不要选 ANSI。用 ANSI/GBK 保存后，路径里的中文会坏掉，表现为文件明明在、程序却说找不到。

`toggle-music.ps1` 写出的也是 UTF-8。它只改 `Music` 和 `Video`，不会把 `AppLaunch` 改掉。

### 杀毒软件或 SmartScreen 拦截

程序没有数字签名。编译或第一次运行时，安全软件可能隔离 `BinanceBoot.exe` 或 `csc.exe`。把仓库目录加入允许列表；SmartScreen 出现「Windows 已保护你的电脑」时，选 **更多信息 → 仍要运行**。隔离之后需要重新执行 `scripts\build.ps1`，再把 `media` 和 `launcher.json` 复制回去。

## 目录

| 路径 | 说明 |
|------|------|
| `README.md` | 本说明（中文） |
| `README.en.md` | 英文版说明 |
| `docs/USAGE.md` | 逐步命令和 `launcher.json` 字段表 |
| `docs/USAGE.en.md` | 英文逐步命令与字段表 |
| `media/README.en.md` | 英文视频下载说明 |
| `NOTICE.md` | 商标与素材声明 |
| `LICENSE` | MIT 许可证 |
| `media/` | 放置两个 MP4 的目录；视频本身在 Release |
| `posters/` | 4K / 2K / 1080p 海报 |
| `config/launcher.binance.json` | 可编辑的示例配置 |
| `launcher.json.example` | 与上一份相同的示例 |
| `src/BinanceBoot.cs` | 启动器源码 |
| `src/binance.ico`、`src/app.manifest` | 图标与 DPI 清单 |
| `scripts/build.ps1` | 编译出 `build\BinanceBoot\BinanceBoot.exe` |
| `toggle-music.ps1`、`Toggle-Music.vbs` | 音乐开关；请复制到编译输出目录再使用 |
| `render/` | 生成 v6 视频和海报的 Python 脚本，使用时不需要运行 |
| `build/` | 编译输出，已被 `.gitignore` 忽略 |

## 致谢

- Windows 启动器结构来自 [dragon-codex-boot](https://github.com/yushua0808-cpu/dragon-codex-boot)（MIT）。
- 动画与打包由 Grok Bot 协助完成。

## 许可证

MIT，见 [LICENSE](LICENSE)。商标与非官方声明见 [NOTICE.md](NOTICE.md)。
