@echo off
setlocal enabledelayedexpansion

:: List of "student-style" commit messages - funny but realistic
set "messages[0]=update code"
set "messages[1]=fix bug"
set "messages[2]=add feature"
set "messages[3]=final version"
set "messages[4]=update ui"
set "messages[5]=fix error"
set "messages[6]=done"
set "messages[7]=code chay duoc roi"
set "messages[8]=test thu"
set "messages[9]=cap nhat moi nhat"

:: Get a random index between 0 and 9
set /a "idx=%RANDOM% %% 10"
set "msg=!messages[%idx%]!"

echo [STUDENT MODE] Dang day code len GitHub...
echo Message: "%msg%"

git add .
git commit -m "%msg%"
git push origin main

echo.
echo [OK] Xong roi do! Di ngu thoi.
pause
