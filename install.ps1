# LifeOS Lite — установка в Hermes для Windows без Python (на остальных системах и при наличии Python: install.py)
# Запуск: двойной клик по install.cmd или
#   powershell -ExecutionPolicy Bypass -File install.ps1
param(
    [string]$ProfileName = "lifeos",
    [string]$VaultPath = (Join-Path $env:USERPROFILE "Documents\LifeOS")
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$utf8 = New-Object System.Text.UTF8Encoding $false
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function Say($t) { Write-Host $t -ForegroundColor Cyan }
function Fail($t) { Write-Host "ОШИБКА: $t" -ForegroundColor Red; exit 1 }

Say "== LifeOS Lite: установка =="

# 1. Hermes установлен?
if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
    Fail "команда hermes не найдена. Открой новое окно PowerShell или проверь установку Hermes."
}

# 2. Профиль ещё не существует?
$existing = (& hermes profile list 2>&1 | Out-String)
if ($existing -match "(?m)^\W*$([regex]::Escape($ProfileName))\b") {
    Fail "профиль '$ProfileName' уже есть. Запусти с другим именем: .\install.ps1 -ProfileName lifeos2"
}

# 3. Создаём профиль, копируя настройки модели и ключи из текущего профиля
Say "Создаю профиль '$ProfileName' (модель и ключи берутся из текущего профиля Hermes)..."
& hermes profile create $ProfileName --clone
if ($LASTEXITCODE -ne 0) { Fail "hermes profile create завершился с ошибкой." }

# 4. Где лежит профиль
$profileDir = $null
$show = (& hermes profile show $ProfileName 2>&1 | Out-String)
if ($show -match "(?m)^Path:\s+(.+?)\s*$") { $profileDir = $Matches[1].Trim() }
if (-not $profileDir -or -not (Test-Path $profileDir)) {
    $root = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA "hermes" }
    $profileDir = Join-Path $root "profiles\$ProfileName"
}
if (-not (Test-Path $profileDir)) { Fail "не нашёл папку профиля. Вывод hermes profile show:`n$show" }
Say "Профиль: $profileDir"

# 5. Папка заметок (не перезаписываем, если уже есть)
if (Test-Path $VaultPath) {
    Say "Папка заметок уже есть, не трогаю: $VaultPath"
} else {
    New-Item -ItemType Directory -Force -Path $VaultPath | Out-Null
    Copy-Item -Path (Join-Path $here "vault\LifeOS\*") -Destination $VaultPath -Recurse -Force
    Say "Папка заметок создана: $VaultPath"
}

# 6. Личность ассистента (SOUL.md) с путём к заметкам
$soul = [System.IO.File]::ReadAllText((Join-Path $here "profile\SOUL.md"), $utf8)
$soul = $soul.Replace("{{VAULT}}", $VaultPath)
[System.IO.File]::WriteAllText((Join-Path $profileDir "SOUL.md"), $soul, $utf8)

# 7. Навыки LifeOS
$skillsDst = Join-Path $profileDir "skills\lifeos"
New-Item -ItemType Directory -Force -Path $skillsDst | Out-Null
Copy-Item -Path (Join-Path $here "profile\skills\lifeos\*") -Destination $skillsDst -Recurse -Force

# 8. Чистая память: клон мог унести память из текущего профиля
$mem = Join-Path $profileDir "memories"
New-Item -ItemType Directory -Force -Path $mem | Out-Null
foreach ($f in @("MEMORY.md", "USER.md")) {
    [System.IO.File]::WriteAllText((Join-Path $mem $f), "", $utf8)
}

Say ""
Say "Готово."
Say "Запуск ассистента:  hermes -p $ProfileName"
Say "  (или в приложении Hermes выбери профиль '$ProfileName')"
Say "Первое сообщение:   Давай познакомимся"
Say "Заметки можно открыть в Obsidian: Open folder as vault -> $VaultPath"
