# 币安开机音乐 开关: flips "Music" in launcher.json and points "Video" at the matching file.
param([ValidateSet('Toggle','On','Off')][string]$Set = 'Toggle', [switch]$Quiet)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfgPath = Join-Path $root 'launcher.json'
$utf8 = New-Object System.Text.UTF8Encoding($false)
try {
    $cfg = [IO.File]::ReadAllText($cfgPath, [Text.Encoding]::UTF8) | ConvertFrom-Json
    $cur = $true
    if ($cfg.PSObject.Properties.Name -contains 'Music') { $cur = [bool]$cfg.Music }
    elseif ($cfg.Video -match 'nomusic') { $cur = $false }
    switch ($Set) { 'On' { $new = $true } 'Off' { $new = $false } default { $new = -not $cur } }
    $video = if ($new) { 'media/startup.mp4' } else { 'media/startup_nomusic.mp4' }
    if (-not (Test-Path -LiteralPath (Join-Path $root $video))) { throw "缺少视频文件：$video" }
    if ($cfg.PSObject.Properties.Name -contains 'Music') { $cfg.Music = $new } else { $cfg | Add-Member -NotePropertyName Music -NotePropertyValue $new }
    $cfg.Video = $video
    $json = ConvertTo-Json -InputObject $cfg -Depth 6
    # sanity: must round-trip and keep the app path intact before replacing the file
    $chk = $json | ConvertFrom-Json
    if ($chk.AppLaunch -ne $cfg.AppLaunch -or -not (Test-Path -LiteralPath $chk.AppLaunch)) { throw 'launcher.json 校验失败，未写入' }
    $tmp = $cfgPath + '.tmp'
    [IO.File]::WriteAllText($tmp, $json, $utf8)
    Move-Item -LiteralPath $tmp -Destination $cfgPath -Force
    $msg = if ($new) { '开机音乐：已开启' } else { '开机音乐：已关闭' }
    if (-not $Quiet) { (New-Object -ComObject WScript.Shell).Popup($msg, 2, '币安开机动画', 64) | Out-Null }
    Write-Output $msg
} catch {
    if (-not $Quiet) { (New-Object -ComObject WScript.Shell).Popup('切换失败：' + $_.Exception.Message, 5, '币安开机动画', 16) | Out-Null }
    Write-Error $_; exit 1
}
