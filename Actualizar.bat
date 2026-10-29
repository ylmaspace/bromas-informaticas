@echo off
chcp 65001 > nul
title Actualizador Oculto e Inteligente de la Biblioteca Secreta
color 0A
cls

echo =======================================================
echo            PREPARANDO NUEVA ACTUALIZACIÓN
echo =======================================================
echo.
set /p msg="Introduce la descripción del commit: "

set hora=%time:~0,5%
set fecha=%date%

:: 1. Indexamos de golpe todos tus cambios locales reales
git add .

:: 2. TRUCO DE INVISIBILIDAD: Sacamos este archivo .bat para que no aparezca en GitHub
git rm --cached "Actualizar.bat" >nul 2>&1

:: 3. Consolidamos tus cambios de forma segura en un Commit local
git commit -m "%msg% (%fecha% - %hora%)" >nul 2>&1

echo.
echo =======================================================
echo               ENVIANDO CAMBIOS A GITHUB...
echo =======================================================
:: Intentamos la subida directa
git push
if %errorlevel% neq 0 (
    echo.
    color 0E
    echo [AVISO] Subida rechazada. Detectados cambios remotos en la web de GitHub.
    echo Ejecutando sincronización y fusión automática reactiva...
    echo.
    
    :: Se ejecuta el pull SOLÓ si el push falló por falta de sincronización
    git pull --no-rebase
    if %errorlevel% neq 0 (
        echo.
        color 0C
        echo [ERROR CRÍTICO] No se pudieron fusionar automáticamente los cambios.
        echo Revisa si hay un conflicto directo editando el mismo archivo.
        pause
        exit
    )
    
    :: Reintentamos el envío definitivo tras la fusión limpia
    echo.
    echo Reintentando envío final a GitHub...
    git push
    if %errorlevel% neq 0 (
        echo.
        color 0C
        echo [ERROR] Falló el segundo intento de subida. Revisa permisos o conexión.
        pause
        exit
    )
)

echo.
echo =======================================================
echo    ¡REPOSITORIO ACTUALIZADO Y SINCRONIZADO CON ÉXITO!
echo =======================================================
echo.
pause
