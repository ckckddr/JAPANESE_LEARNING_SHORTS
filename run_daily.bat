@echo off
REM ================================================================
REM 비즈니스 일본어 YouTube 자동 업로드 - 배치 실행 파일
REM Windows 작업 스케줄러에 등록하여 매일 오전 7시 실행
REM ================================================================

REM Python 경로 (Python 3.14 사용)
set PYTHON=py -3.14

REM 프로젝트 경로 (이 파일이 있는 폴더)
set PROJECT_DIR=%~dp0

REM 로그 파일
set LOG_FILE=%PROJECT_DIR%data\logs\batch_%date:~0,4%%date:~5,2%%date:~8,2%.log

echo [%date% %time%] 배치 작업 시작 >> "%LOG_FILE%"

cd /d "%PROJECT_DIR%"

REM 실전 실행: privacy 옵션은 public (공개)
%PYTHON% main.py --privacy public >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] 완료 >> "%LOG_FILE%"
) else (
    echo [%date% %time%] 오류 발생 (코드: %ERRORLEVEL%) >> "%LOG_FILE%"
)

REM ================================================================
REM Windows 작업 스케줄러 등록 명령어 (관리자 권한 PowerShell에서 실행):
REM
REM $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"%PROJECT_DIR%run_daily.bat`""
REM $trigger = New-ScheduledTaskTrigger -Daily -At "07:00"
REM $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable
REM Register-ScheduledTask -TaskName "JLPT_YouTube_Upload" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest
REM ================================================================
