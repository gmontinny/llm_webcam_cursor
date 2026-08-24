@echo off
echo Instalando dependencias do NonMouse...
python -m pip install --no-cache-dir -r requirements.txt
if %ERRORLEVEL% == 0 (
    echo.
    echo Instalacao concluida com sucesso!
) else (
    echo.
    echo Erro na instalacao. Verifique sua conexao e tente novamente.
)
pause
