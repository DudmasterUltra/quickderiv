echo off
cls
echo quickderiv launcher
echo by Rory Eckel
echo.
echo Checking for existing build...
if exist build/exe.win32-3.6/__main__.exe (
	echo Build found. Launching...
	echo.
	cd build/exe.win32-3.6
	__main__.exe
) else (
	echo Build not found. Building with cx_Freeze
	python setup.py build
	echo Attempting to launch build.
	echo.
	cd build/exe.win32-3.6
	__main__.exe
)