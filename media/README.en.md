# media

中文: [media/README.md](README.md)

The boot videos are published on the GitHub Release. A `git clone` does not download them. Save both files into this directory, next to this note.

Release page: <https://github.com/hua05727-beep/binance-boot/releases/tag/v1.0.0>

| File | Direct download | Size | SHA256 |
|------|-----------------|------|--------|
| `startup.mp4` | [startup.mp4](https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup.mp4) | 32349183 bytes | `48c563f53a80aa29daeffd3a46c1b8582fb5ac3c33e30469d33da28a4e18b165` |
| `startup_nomusic.mp4` | [startup_nomusic.mp4](https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup_nomusic.mp4) | 32341666 bytes | `1ffea2b2d58ee1cb72a27b2661d4d6326520864f7c4cd92c2a8e25fcba06a3c2` |

- `startup.mp4`: about 25 seconds, with background music and effects (1080p).
- `startup_nomusic.mp4`: the same picture, effects only, no music bed.

After the download, this directory should contain:

```text
media/startup.mp4
media/startup_nomusic.mp4
media/README.md
media/README.en.md
```

From the repository root, download and check in PowerShell:

```powershell
New-Item -ItemType Directory -Force media | Out-Null
curl.exe -L -o media\startup.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup.mp4
curl.exe -L -o media\startup_nomusic.mp4 https://github.com/hua05727-beep/binance-boot/releases/download/v1.0.0/startup_nomusic.mp4
(Get-Item media\startup.mp4).Length
(Get-Item media\startup_nomusic.mp4).Length
Get-FileHash media\startup.mp4, media\startup_nomusic.mp4 -Algorithm SHA256
```

The two lengths must be `32349183` and `32341666`. The hashes must match the table. If they do not, download again and keep the original file names.

After the build, copy both files to `build\BinanceBoot\media\` as well. The launcher reads the `media` folder next to the exe, not this copy at the repository root. Steps: [README.en.md](../README.en.md) and [docs/USAGE.en.md](../docs/USAGE.en.md).
