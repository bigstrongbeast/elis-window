# Собрать папку «Элис» для запуска на любом Windows 11 без установки:
#   Элис.exe      — запускалка (собирается встроенным в Windows компилятором csc)
#   app\          — наш открытый код: server.py, main.py, index.html, значки
#   python\       — свой Python 3.13 (embeddable с python.org) + pywebview в Lib\site-packages
# Использование: make_dist.ps1 -PyZip <python-3.13.x-embed-amd64.zip> -Libs <папка с pywebview и зависимостями> [-Out <куда>]
param([string]$PyZip, [string]$Libs, [string]$Out)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
if (-not $Out) { $Out = Join-Path $repo 'dist\Elis' }
if (Test-Path $Out) { Remove-Item -Recurse -Force $Out }
New-Item -ItemType Directory -Force $Out | Out-Null

# app — только нужное, без входящих и логов
$app = New-Item -ItemType Directory -Force (Join-Path $Out 'app')
'server.py', 'main.py', 'index.html', 'elis.ico', 'elis_face.png' | ForEach-Object { Copy-Item (Join-Path $repo "app\$_") $app }

# свой Python
$py = Join-Path $Out 'python'
Expand-Archive -Path $PyZip -DestinationPath $py
$pth = Get-ChildItem $py -Filter 'python3*._pth' | Select-Object -First 1
$lines = (Get-Content $pth.FullName) -replace '^#\s*import site', 'import site'
Set-Content -Path $pth.FullName -Value ($lines + 'Lib\site-packages' + '..\app') -Encoding ascii
$site = New-Item -ItemType Directory -Force (Join-Path $py 'Lib\site-packages')
Get-ChildItem $Libs | Where-Object { $_.Name -ne '__pycache__' -and $_.Name -ne 'bin' } | Copy-Item -Destination $site -Recurse

# запускалка
$csc = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$exe = Join-Path $Out 'Elis.exe'
& $csc /nologo /target:winexe /optimize+ "/win32icon:$(Join-Path $repo 'app\elis.ico')" "/out:$exe" /r:System.Windows.Forms.dll (Join-Path $repo 'launcher\Elis.cs')
if ($LASTEXITCODE -ne 0) { throw "csc: ошибка сборки запускалки" }
# Имя exe и пути — только латиница (Дима 30.10: «никаких русских, на ярлыках только можно»)

$size = (Get-ChildItem $Out -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
"ok: $Out · {0:N1} МБ" -f $size
