@echo off
chcp 65001 >nul
rem Установить или обновить Элис: C:\Elis из GitHub (ветка release) по HTTPS, ярлык «Элис» на рабочий стол.
rem SSH к GitHub из сети Лены виснет (30.10) — поэтому HTTPS. Доступ только на чтение: токен в C:\Tools\elis-git\token.txt
rem (в git config не пишется, передаётся на время команды). Нет файла — качает как открытый репозиторий.
rem Запустить второй раз = обновить.
setlocal
set "DIR=C:\Elis"
set "TOKENFILE=C:\Tools\elis-git\token.txt"
set "REPO=https://github.com/bigstrongbeast/elis-window.git"
set "GIT_TERMINAL_PROMPT=0"
set "AUTH="
if exist "%TOKENFILE%" (
  for /f "usebackq delims=" %%h in (`powershell -NoProfile -Command "'Authorization: Basic ' + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes('x-access-token:' + (Get-Content '%TOKENFILE%' -Raw).Trim()))"`) do set AUTH=-c "http.extraHeader=%%h"
)

echo.
echo  == Элис: установка ==
where git >nul 2>&1 || (echo  ОШИБКА: не найден Git. & pause & exit /b 1)

if exist "%DIR%\.git" (
  echo  1. Обновляю %DIR% ... если окно Элис открыто — закрой его.
  git %AUTH% -C "%DIR%" pull --ff-only
) else (
  echo  1. Скачиваю в %DIR% ^(около 270 МБ, пара минут^) ...
  git %AUTH% clone -b release --depth 1 %REPO% "%DIR%"
)
if errorlevel 1 (echo. & echo  ОШИБКА: не скачалось. Покажи это окно Диме. & pause & exit /b 1)

echo  2. Ярлык «Элис» на рабочий стол
powershell -NoProfile -Command "$n=[string]::new([char[]](0x42D,0x43B,0x438,0x441)); $s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\'+$n+'.lnk'); $s.TargetPath='%DIR%\Elis.exe'; $s.WorkingDirectory='%DIR%'; $s.IconLocation='%DIR%\app\elis.ico'; $s.Save()"

echo  3. Самопроверка: окно откроется само секунд на 10 и закроется
start "" "%DIR%\Elis.exe" --selftest

echo.
echo  ГОТОВО. Элис — ярлык «Элис» на рабочем столе. Обновить — запустить этот файл ещё раз.
echo.
pause
