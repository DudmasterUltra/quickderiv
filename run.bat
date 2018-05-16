echo off
cls
echo quickderiv launcher
echo by Rory Eckel
echo.
echo Checking for existing build...
if exist build/exe.win32-3.6/quickderiv.exe (
	echo Build found. Launching...
	echo.
	cd build/exe.win32-3.6
	quickderiv.exe
) else (
	echo Build not found. Building with cx_Freeze
	python setup.py build
	echo Attempting to launch build.
	echo.
	cd build/exe.win32-3.6
	quickderiv.exe
)