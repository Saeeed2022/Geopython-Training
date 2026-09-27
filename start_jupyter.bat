@echo off
REM Double-click this file to start the course in JupyterLab (Windows).
REM It assumes Miniforge in its default place and the course in C:\Geopython.

call "%USERPROFILE%\miniforge3\Scripts\activate.bat" geopython
if errorlevel 1 (
    echo Could not activate the conda environment "geopython". See INSTALL_WINDOWS.md, step 2.
    pause
    exit /b 1
)
REM SAGA command line (group D4), if unzipped to C:\SAGA
if exist "C:\SAGA\saga_cmd.exe" set "PATH=C:\SAGA;%PATH%"

cd /d "%~dp0notebooks"
jupyter lab
