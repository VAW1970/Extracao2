@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ============================================
echo   Extracao Contabil — Setup do Ambiente
echo ============================================
echo.

REM ── Verificar se Python esta instalado ──
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.11+ e adicione ao PATH.
    pause
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PY_VERSION=%%a
echo [OK] Python %PY_VERSION% encontrado.

REM ── Criar ambiente virtual ──
if not exist "venv" (
    echo.
    echo [1/7] Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado em .\venv
) else (
    echo.
    echo [1/7] Ambiente virtual ja existe. Pulando criacao.
)

REM ── Ativar ambiente virtual ──
echo.
echo [2/7] Ativando ambiente virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERRO] Falha ao ativar ambiente virtual.
    pause
    exit /b 1
)
echo [OK] Ambiente virtual ativado.

REM ── Atualizar pip ──
echo.
echo [3/7] Atualizando pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [AVISO] Falha ao atualizar pip, continuando...
)

REM ── Verificar Visual C++ Build Tools (Windows) ──
echo.
echo [4/7] Verificando compilador C++...
where cl.exe >nul 2>&1
if errorlevel 1 (
    echo [INFO] Visual C++ Build Tools nao detectado.
    echo        Alguns pacotes (lxml, psycopg) podem precisar de compilacao.
    echo        Se encontrar erros, instale as Build Tools:
    echo        https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
)

REM ── Instalar dependencias ──
echo.
echo [5/7] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ============================================
    echo [ERRO] Falha ao instalar dependencias!
    echo ============================================
    echo.
    echo O erro "Microsoft Visual C++ 14.0 or greater is required"
    echo significa que um pacote precisa ser compilado mas o compilador
    echo nao foi encontrado.
    echo.
    echo SOLUCOES:
    echo.
    echo   Opcao 1 (Recomendada): Instalar Microsoft C++ Build Tools
    echo     1. Baixe: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo     2. Execute o instalador
    echo     3. Selecione "Desktop development with C++"
    echo     4. Instale e reinicie o terminal
    echo     5. Execute este script novamente
    echo.
    echo   Opcao 2: Usar WSL (Windows Subsystem for Linux)
    echo     wsl --install
    echo     # Depois rode o setup no Ubuntu
    echo.
    echo   Opcao 3: Tentar instalar versoes especificas
    echo     pip install lxml --only-binary :all:
    echo     pip install psycopg[binary]
    echo     pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas.

REM ── Copiar .env.example para .env se nao existir ──
echo.
echo [6/7] Verificando arquivo .env...
if not exist ".env" (
    copy .env.example .env >nul
    echo [OK] Arquivo .env criado a partir do .env.example
    echo.
    echo   *** IMPORTANTE: Edite o arquivo .env com suas configuracoes ***
    echo   *** (DJANGO_SECRET_KEY, DATABASE_URL, LLM_API_KEY)          ***
    echo.
) else (
    echo [OK] Arquivo .env ja existe.
)

REM ── Executar migracoes ──
echo.
echo [7/7] Executando migracoes do banco de dados...
python manage.py migrate
if errorlevel 1 (
    echo [ERRO] Falha ao executar migracoes.
    pause
    exit /b 1
)
echo [OK] Migracoes aplicadas.

echo.
echo ============================================
echo   Setup concluido com sucesso!
echo ============================================
echo.
set /p CRIAR_SUPERUSER="Deseja criar um superuser agora? (S/N): "
if /i "%CRIAR_SUPERUSER%"=="S" (
    echo.
    python manage.py createsuperuser
) else (
    echo.
    echo Para criar o superuser depois, execute:
    echo   venv\Scripts\activate
    echo   python manage.py createsuperuser
)

echo.
echo Para iniciar o servidor de desenvolvimento:
echo   venv\Scripts\activate
echo   python manage.py runserver
echo.
echo Acesse: http://localhost:8000
echo.
pause
