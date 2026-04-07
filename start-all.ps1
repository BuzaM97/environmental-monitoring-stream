# IoT Platform - Teljes indítási script
# Sorban elindítja: Docker, Producer, Consumer

param(
    [switch]$SkipDocker = $false,
    [switch]$SkipGrafana = $false
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPath = "$ProjectRoot\.venv\Scripts\python.exe"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "    IoT Platform - Startup Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# 1. Python Environment ellenőrzése
Write-Host "`n[1/6] Python környezet ellenőrzése..." -ForegroundColor Yellow
if (-Not (Test-Path $VenvPath)) {
    Write-Host "    ❌ Python venv nem található!" -ForegroundColor Red
    Write-Host "    Kérlek futtasd: python -m venv .venv" -ForegroundColor Red
    exit 1
}
Write-Host "    ✓ Python venv OK" -ForegroundColor Green

# 2. Docker Compose ellenőrzése
if (-Not $SkipDocker) {
    Write-Host "`n[2/6] Docker Compose indítása..." -ForegroundColor Yellow
    
    $ComposeFile = "$ProjectRoot\docker-compose.yml"
    if (-Not (Test-Path $ComposeFile)) {
        Write-Host "    ❌ docker-compose.yml nem található!" -ForegroundColor Red
        exit 1
    }
    
    # Docker konténerek indítása
    Write-Host "    Konténerek indítása..." -ForegroundColor Gray
    docker compose -f $ComposeFile up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    ❌ Docker indítás sikertelen!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "    ✓ Docker konténerek elindítva" -ForegroundColor Green
    Write-Host "    ⏳ Várakozás a Docker szolgáltatások indulására (15 másodperc)..." -ForegroundColor Gray
    Start-Sleep -Seconds 15
    
    # Docker status ellenőrzése
    Write-Host "    Docker status:" -ForegroundColor Gray
    docker compose -f $ComposeFile ps
} else {
    Write-Host "`n[2/6] Docker Compose kihagyva (--SkipDocker flag)" -ForegroundColor Yellow
}

# 3. IoT Simulator Producer indítása
Write-Host "`n[3/6] IoT Simulator Producer indítása..." -ForegroundColor Yellow
$ProducerScript = "$ProjectRoot\producers\iot_simulator.py"
if (-Not (Test-Path $ProducerScript)) {
    Write-Host "    ❌ Producer script nem található!" -ForegroundColor Red
    exit 1
}

$ProducerWindowTitle = "IoT Producer - Simulator"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$VenvPath' '$ProducerScript'" -WindowName $ProducerWindowTitle
Write-Host "    ✓ Producer elindítva (új ablakban)" -ForegroundColor Green
Start-Sleep -Seconds 2

# 3.5. Sentinel API Producer indítása
Write-Host "`n[4/6] Sentinel API Producer indítása..." -ForegroundColor Yellow
$SentinelScript = "$ProjectRoot\producers\sentinel_api.py"
if (-Not (Test-Path $SentinelScript)) {
    Write-Host "    ❌ Sentinel Producer script nem található!" -ForegroundColor Red
    exit 1
}

$SentinelWindowTitle = "IoT Producer - Sentinel API"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$VenvPath' '$SentinelScript'" -WindowName $SentinelWindowTitle
Write-Host "    ✓ Sentinel Producer elindítva (új ablakban)" -ForegroundColor Green
Start-Sleep -Seconds 2

# 4. Data Processor Consumer indítása
Write-Host "`n[5/6] Data Processor Consumer indítása..." -ForegroundColor Yellow
$ConsumerScript = "$ProjectRoot\consumer\data_processor.py"
if (-Not (Test-Path $ConsumerScript)) {
    Write-Host "    ❌ Consumer script nem található!" -ForegroundColor Red
    exit 1
}

$ConsumerWindowTitle = "IoT Consumer - Data Processor"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$VenvPath' '$ConsumerScript'" -WindowName $ConsumerWindowTitle
Write-Host "    ✓ Consumer elindítva (új ablakban)" -ForegroundColor Green

# 5. Grafana és Összefoglalás
Write-Host "`n[6/6] Összefoglalás" -ForegroundColor Yellow
Write-Host "`n    📊 Szolgáltatások:" -ForegroundColor Cyan
Write-Host "      • Grafana: http://localhost:3000 (admin/admin)" -ForegroundColor Gray
Write-Host "      • InfluxDB: http://localhost:8086" -ForegroundColor Gray
Write-Host "      • Kafka: localhost:9092" -ForegroundColor Gray
Write-Host "      • Sentinel Hub API: Az aktuális OAuth2 token szükséges" -ForegroundColor Gray

Write-Host "`n================================================" -ForegroundColor Green
Write-Host "✓ Összes szolgáltatás elindítva!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

Write-Host "`n📋 Nyitott ablakok:" -ForegroundColor Cyan
Write-Host "  • Simulator Producer: $ProducerWindowTitle" -ForegroundColor Gray
Write-Host "  • Sentinel Producer: $SentinelWindowTitle" -ForegroundColor Gray
Write-Host "  • Consumer: $ConsumerWindowTitle" -ForegroundColor Gray

Write-Host "`n💡 Tippek:" -ForegroundColor Yellow
Write-Host "  • Bezáráshoz: Ctrl+C az egyes ablakokban" -ForegroundColor Gray
Write-Host "  • Docker leállítása: docker compose down" -ForegroundColor Gray
Write-Host "  • Log megtekintése: docker compose logs -f" -ForegroundColor Gray

# Script nyitva tartása
Write-Host "`n(Ez az ablak nyitva marad. Bezáráshoz Ctrl+C)" -ForegroundColor DarkGray
Read-Host
