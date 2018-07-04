@echo off

if "%1"=="clean" goto CLEAN
if "%1"=="release" goto RELEASE
if "%1"=="debug" goto DEBUG
if "%1"=="help" goto USAGE
if "%1"=="-help" goto USAGE
if "%1"=="/?" goto USAGE

rem --------------------------------------------------------------------------
:DEFAULT
echo Starting Visual Studio...
devenv example_utilities.sln
goto END

rem --------------------------------------------------------------------------
:CLEAN
echo Cleaning...
devenv /clean Debug example_utilities.sln
devenv /clean Release example_utilities.sln
del /s /q *.ncb
del /s /q *.opt
del /s /q *.plg
del /s /q *.exe
rmdir /s /q bin
goto END

rem --------------------------------------------------------------------------
:RELEASE
echo Starting release build...
devenv /build Release example_utilities.sln
goto END

rem --------------------------------------------------------------------------
:DEBUG
echo Starting debug build...
devenv /build Debug example_utilities.sln
goto END

rem --------------------------------------------------------------------------
:USAGE
echo .
echo This script is for building the test-framework example utilities on windows
echo platforms. To run this the 'devenv' executable must be on your path. If this 
echo is not set, run the 'vsvars32' batch file in your Visual Studio installation 
echo to set the path. This file can typically be found in 
echo C:\Program Files\Microsoft Visual Studio .NET 2003\Common7\Tools\
echo .
echo "make [ help | clean | release | debug]"
echo   help    - Show this message.
echo   clean   - Remove all intermediate files and final binaries
echo   release - Perform a background (non-interactive) RELEASE build.
echo   debug   - Perform a background (non-interactive) DEBUG build.
echo .
echo Without any parameters the script will launch Visual Studio with the 
echo workspace loaded.
goto END


rem -------------------------------------------------------------------------
:END
