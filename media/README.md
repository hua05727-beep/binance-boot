# media

English: [media/README.en.md](README.en.md)

开机视频放在 GitHub Release，不随 `git clone` 下载。请把下面两个文件保存到本目录（和这份说明放在一起）。

发布页：<https://github.com/hua05727-beep/binance-boot/releases/tag/v1.0.0>

| 文件 | 直接下载 | 大小 | SHA256 |
|------|----------|------|--------|
| `startup.mp4` | [startup.mp4](https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup.mp4) | 32349183 字节 | `48c563f53a80aa29daeffd3a46c1b8582fb5ac3c33e30469d33da28a4e18b165` |
| `startup_nomusic.mp4` | [startup_nomusic.mp4](https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup_nomusic.mp4) | 32341666 字节 | `1ffea2b2d58ee1cb72a27b2661d4d6326520864f7c4cd92c2a8e25fcba06a3c2` |

- `startup.mp4`：约 25 秒，有背景音乐和音效（1080p）。
- `startup_nomusic.mp4`：同一条画面，只有音效，没有音乐。

放好之后目录应是：

```text
media/startup.mp4
media/startup_nomusic.mp4
media/README.md
```

在仓库根目录用 PowerShell 下载并核对：

```powershell
New-Item -ItemType Directory -Force media | Out-Null
curl.exe -L -o media\startup.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup.mp4
curl.exe -L -o media\startup_nomusic.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup_nomusic.mp4
(Get-Item media\startup.mp4).Length
(Get-Item media\startup_nomusic.mp4).Length
Get-FileHash media\startup.mp4, media\startup_nomusic.mp4 -Algorithm SHA256
```

两个长度应分别是 `32349183` 和 `32341666`。哈希要和上表一致；对不上就重新下载，不要改名凑合用。

编译完成后，还要把这两个文件复制到 `build\BinanceBoot\media\`。启动器读的是 exe 旁边的 `media`，不是仓库根目录这份。步骤见 [README](../README.md) 和 [docs/USAGE.md](../docs/USAGE.md)。
