@echo off
echo 🚀 Starting Auto Webhook Setup System...
echo.

REM Create temp file for tunnel output
set TEMP_FILE=%TEMP%\tunnel_output.txt

REM Start tunnel and capture output
echo ⏳ Starting Cloudflare Tunnel...
start /B cloudflared tunnel --url http://localhost:8000 > "%TEMP_FILE%" 2>&1

REM Wait for tunnel to initialize
timeout /t 10 /nobreak > nul

REM Try to extract URL from output
echo 🔍 Looking for tunnel URL...
timeout /t 5 /nobreak > nul

REM Read the output file and look for URL
for /f "tokens=*" %%i in ('findstr "trycloudflare.com" "%TEMP_FILE%"') do (
    echo Found: %%i
    REM Extract just the URL part
    for /f "tokens=*" %%j in ('echo %%i ^| findstr /R "https://[^[:space:]]*trycloudflare.com"') do (
        set TUNNEL_URL=%%j
    )
)

if defined TUNNEL_URL (
    echo.
    echo ✅ SUCCESS! Tunnel URL found: %TUNNEL_URL%
    echo 🔗 Webhook URL: %TUNNEL_URL%/payments/webhook/bank
    echo.
    echo ⚠️  MANUAL STEPS:
    echo 1. Copy this URL: %TUNNEL_URL%/payments/webhook/bank
    echo 2. Go to SePay dashboard
    echo 3. Update webhook URL
    echo 4. Test the webhook
    echo.
    echo 💡 TIP: Use auto_webhook_setup.py for full automation
    echo.
) else (
    echo ❌ Failed to extract tunnel URL
    echo 📄 Check %TEMP_FILE% for details
)

echo 🔄 Tunnel is running in background...
echo 🛑 Press any key to stop tunnel and exit...
pause > nul

REM Kill cloudflared processes
taskkill /F /IM cloudflared.exe > nul 2>&1
echo ✅ Tunnel stopped.