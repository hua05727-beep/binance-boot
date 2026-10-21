# binance-boot

Unofficial Binance desktop **boot animation** for Windows: a 25-second black-gold intro (poster → BTC K-line → Binance mark), then a 2-second crossfade into the real Binance window.

> Not affiliated with Binance. See [NOTICE.md](NOTICE.md).

## What's included

| Path | Description |
|------|-------------|
| `media/startup.mp4` | Final boot video **with** music (25 s, 1080p). Download from the [v1.0.0 release](https://github.com/hua05727-beep/binance-boot/releases/tag/v1.0.0) into `media/` |
| `media/startup_nomusic.mp4` | Same picture, effects only (no music bed). Same release; place next to `startup.mp4` |
| `posters/` | Desktop posters (4K / 2K / 1080p) |
| `src/BinanceBoot.cs` | WPF launcher (DWM thumbnail handoff) |
| `toggle-music.ps1` | Flip music on/off without rebuilding |
| `render/` | Python code that rendered the video & posters |
| `config/launcher.binance.json` | Example config (edit `AppLaunch` to your Binance.exe) |

## Quick start (Windows)

1. Install [.NET Framework 4.8](https://dotnet.microsoft.com/download/dotnet-framework/net48) (usually already on Windows 10/11).
2. Clone this repo.
3. Download `startup.mp4` and `startup_nomusic.mp4` from the [v1.0.0 release](https://github.com/hua05727-beep/binance-boot/releases/tag/v1.0.0) into `media/` (they are not in the git clone). See [media/README.md](media/README.md).
4. Edit `config/launcher.binance.json`: set `AppLaunch` to your `Binance.exe` path, and `ProcessPathContains` to a unique fragment of that path.
5. Build:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

6. Copy videos into the build output if needed:

```powershell
New-Item -ItemType Directory -Force build\BinanceBoot\media | Out-Null
Copy-Item media\startup.mp4, media\startup_nomusic.mp4 build\BinanceBoot\media\
Copy-Item config\launcher.binance.json build\BinanceBoot\launcher.json
Copy-Item toggle-music.ps1, Toggle-Music.vbs build\BinanceBoot\
```

7. Run `build\BinanceBoot\BinanceBoot.exe`.

### Music on/off

From the build folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\toggle-music.ps1
```

Or double-click `Toggle-Music.vbs` (no console window). A short popup shows `开机音乐：已开启` / `已关闭`.

`Music: true` → `media/startup.mp4`  
`Music: false` → `media/startup_nomusic.mp4`

### Timing (crossfade)

Default config holds the last calm frame around **22.9 s**, then fades video out / Binance window in from **23.0 → 24.95 s**.

## Render scripts (optional)

The `render/` folder contains the Python pipeline used to generate v6 (beat-synced poster, K-line text effects, logo assembly). It needs a local venv with numpy, Pillow, librosa, etc., plus CJK fonts. The shipped MP4s are already final — you do not need to re-render to use the launcher.

## Credits

- Launcher architecture based on [dragon-codex-boot](https://github.com/yushua0808-cpu/dragon-codex-boot) (MIT).
- Animation & packaging prepared with Grok Bot.

## License

MIT — see [LICENSE](LICENSE).
