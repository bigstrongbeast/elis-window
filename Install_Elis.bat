@echo off
chcp 65001 >nul
rem Установить или обновить Элис: C:\Elis из GitHub (ветка release), ярлык «Элис» на рабочий стол.
rem Ключ только на чтение: C:\Tools\elis-git\deploy_key. Запустить второй раз = обновить.
setlocal
set "DIR=C:\Elis"
set "KEY=C:\Tools\elis-git\deploy_key"
set "REPO=git@github.com:bigstrongbeast/elis-window.git"
set "GIT_SSH_COMMAND=C:/Windows/System32/OpenSSH/ssh.exe -i C:/Tools/elis-git/deploy_key -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"

echo.
echo  == Элис: установка ==
where git >nul 2>&1 || (echo  ОШИБКА: не найден Git. & pause & exit /b 1)
if not exist "%KEY%" (echo  ОШИБКА: нет ключа %KEY% & pause & exit /b 1)

if exist "%DIR%\.git" (
  echo  1. Обновляю %DIR% ... если окно Элис открыто — закрой его.
  git -C "%DIR%" pull --ff-only
) else (
  echo  1. Скачиваю в %DIR% ^(около 270 МБ, несколько минут^) ...
  git clone -b release --depth 1 %REPO% "%DIR%"
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
