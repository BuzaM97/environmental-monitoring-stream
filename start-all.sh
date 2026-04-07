#!/bin/bash
#
# IoT Platform Startup Script
# Platform-független megoldás (Windows, macOS, Linux)
#

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
VENV_PATH="$PROJECT_ROOT/.venv"
PIDS=()

# Szín definíciók
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fejléc kiírása
print_header() {
    echo -e "\n${CYAN}================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}================================================${NC}"
}

# Lépés kiírása
print_step() {
    echo -e "\n${YELLOW}[$1] $2...${NC}"
}

# Hiba kiírása
print_error() {
    echo -e "${RED}  ❌ $1${NC}"
}

# Siker kiírása
print_success() {
    echo -e "${GREEN}  ✓ $1${NC}"
}

# Graceful shutdown
cleanup() {
    echo -e "\n\n${YELLOW}⏹️  Leállítás...${NC}"
    
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Leállítom: PID $pid"
            kill "$pid" 2>/dev/null || true
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
    done
    
    echo "  ${GREEN}✓ Leállítva${NC}"
}

trap cleanup EXIT INT TERM

print_header "IoT Platform - Startup Script"

# 1. Python Environment ellenőrzése
print_step "1/4" "Python környezet ellenőrzése"

if [ ! -d "$VENV_PATH" ]; then
    print_error "Python venv nem található!"
    echo "  Kérlek futtasd: python -m venv .venv"
    exit 1
fi

if [ ! -f "$VENV_PYTHON" ]; then
    print_error "Python végrehajtható nem található!"
    exit 1
fi

print_success "Python venv OK"

# 2. Docker Compose ellenőrzése és indítása
print_step "2/4" "Docker Compose indítása"

COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "docker-compose.yml nem található!"
    exit 1
fi

echo "  Konténerek indítása..."
if ! docker compose -f "$COMPOSE_FILE" up -d; then
    print_error "Docker indítás sikertelen!"
    exit 1
fi

print_success "Docker konténerek elindítva"
echo "  ${YELLOW}⏳ Várakozás a szolgáltatások indulására (60 másodperc)...${NC}"
sleep 60

# 3. IoT Simulator Producer indítása
print_step "3/4" "IoT Simulator Producer indítása"

PRODUCER_SCRIPT="$PROJECT_ROOT/producers/iot_simulator.py"
if [ ! -f "$PRODUCER_SCRIPT" ]; then
    print_error "Producer script nem található!"
    exit 1
fi

if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd '$PROJECT_ROOT'; '$VENV_PYTHON' '$PRODUCER_SCRIPT'; bash" &
elif command -v xterm &> /dev/null; then
    xterm -e "cd '$PROJECT_ROOT'; '$VENV_PYTHON' '$PRODUCER_SCRIPT'" &
else
    # Fallback: háttérben futtatás
    nohup "$VENV_PYTHON" "$PRODUCER_SCRIPT" > /dev/null 2>&1 &
fi

PRODUCER_PID=$!
PIDS+=($PRODUCER_PID)
print_success "Producer indítva (PID: $PRODUCER_PID)"
sleep 2

# 4. Sentinel API Producer indítása
print_step "4/4" "Sentinel API Producer indítása"

SENTINEL_SCRIPT="$PROJECT_ROOT/producers/sentinel_api.py"
if [ ! -f "$SENTINEL_SCRIPT" ]; then
    print_error "Sentinel Producer script nem található!"
    exit 1
fi

if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd '$PROJECT_ROOT'; '$VENV_PYTHON' '$SENTINEL_SCRIPT'; bash" &
elif command -v xterm &> /dev/null; then
    xterm -e "cd '$PROJECT_ROOT'; '$VENV_PYTHON' '$SENTINEL_SCRIPT'" &
else
    # Fallback: háttérben futtatás
    nohup "$VENV_PYTHON" "$SENTINEL_SCRIPT" > /dev/null 2>&1 &
fi

SENTINEL_PID=$!
PIDS+=($SENTINEL_PID)
print_success "Sentinel Producer indítva (PID: $SENTINEL_PID)"
sleep 2

# 5. Data Processor Consumer indítása
print_step "5/6" "Data Processor Consumer indítása"

CONSUMER_SCRIPT="$PROJECT_ROOT/consumer/data_processor.py"
if [ ! -f "$CONSUMER_SCRIPT" ]; then
    print_error "Consumer script nem található!"
    exit 1
fi

if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd '$PROJECT_ROOT'; '$VENV_PYTHON' '$CONSUMER_SCRIPT'; bash" &
elif command -v xterm &> /dev/null; then
    xterm -e "cd '$PROJECT_ROOT'; '$VENV_PYTHON' '$CONSUMER_SCRIPT'" &
else
    # Fallback: háttérben futtatás
    nohup "$VENV_PYTHON" "$CONSUMER_SCRIPT" > /dev/null 2>&1 &
fi

CONSUMER_PID=$!
PIDS+=($CONSUMER_PID)
print_success "Consumer indítva (PID: $CONSUMER_PID)"

# 6. Összefoglalás
print_step "6/6" "Összefoglalás"

echo -e "\n${CYAN}📊 Szolgáltatások:${NC}"
echo "  • Grafana: http://localhost:3000 (admin/admin)"
echo "  • InfluxDB: http://localhost:8086"
echo "  • Kafka: localhost:9092"
echo "  • Sentinel Hub API: Az aktuális OAuth2 token szükséges"

echo -e "\n${CYAN}📋 Futó processek:${NC}"
for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "  PID $pid: ${GREEN}✓ Futó${NC}"
    else
        echo -e "  PID $pid: ${RED}❌ Leállt${NC}"
    fi
done

print_header "✓ Összes szolgáltatás elindítva!"

echo -e "${YELLOW}💡 Tippek:${NC}"
echo "  • Bezáráshoz: Ctrl+C az ablakban"
echo "  • Docker leállítása: docker compose down"
echo "  • Log megtekintése: docker compose logs -f"

echo -e "\n${CYAN}(Script az összes processz közös vezérléséhez nyitva marad. Bezáráshoz Ctrl+C)${NC}"

# Várakozás a végéig
wait
