@echo off
echo ========================================
echo  Push para GitHub - Extracao Contabil
echo ========================================
echo.

REM Verificar se o git esta configurado
git config user.email >nul 2>&1
if %errorlevel% neq 0 (
    echo Configurando usuario do Git...
    git config user.email "valdiraw@yahoo.com.br"
    git config user.name "Valdir"
)

set REPO_URL=https://github.com/VAW1970/Extracao2.git

REM Verificar se ja existe um remote
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo Adicionando remote origin...
    git remote add origin %REPO_URL%
)

git remote set-url origin %REPO_URL%
echo Remote 'origin' configurado:
git remote get-url origin
echo.
echo Fazendo push para %REPO_URL%...
git branch -M main
git push -u origin main

echo.
echo ========================================
echo  Push concluido!
echo ========================================
pause
