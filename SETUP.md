# IoT Platform Gyors Setup

## Előkövetelmények

- Docker Desktop
- Python 3.8+

---

## Gyors Setup

### 1. Python Environment

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Docker Indítása

```bash
docker compose up -d
docker compose ps
```

All containers should be `Up`

### 3. Producer & Consumer Indítása (3 terminál)

**Terminal 1 - IoT Simulator Producer:**

```powershell
.\.venv\Scripts\python.exe .\producers\iot_simulator.py
```

**Terminal 2 - Data Processor Consumer (Kafka → InfluxDB):**

```powershell
.\.venv\Scripts\python.exe .\consumer\data_processor.py
```

**Terminal 3 - Kafka Consumer (opcionális, valós idejű debug):**

```powershell
docker exec iot-kafka-1 kafka-console-consumer --bootstrap-server localhost:9092 --topic iot_sensor_data
```

## 3. Szolgáltatások Elérése

### 3.1 Grafana (Vizualizáció)

- **URL:** http://localhost:3000
- **Felhasználó:** admin
- **Jelszó:** Az `.env` fájlban (`GRAFANA_ADMIN_PASSWORD`)
- **Feladat:** Dashboard létrehozása, Data Source hozzáadása

### 3.2 InfluxDB (Adatbázis)

- **URL:** http://localhost:8086
- **Felhasználó:** admin
- **Jelszó:** Az `.env` fájlban (`INFLUXDB_INIT_PASSWORD`)
- **Bucket:** `iot_data` (már létrehozva)
- **API Token:** Az `.env` fájlban (`INFLUXDB_INIT_ADMIN_TOKEN`)
- **Feladat:** Bucket ellenőrzése, adatok vizsgálata

### 3.3 Kafka (Üzenetközvetítő)

- **Bootstrap Server:** `localhost:9092` (docker belül)
- **Docker belül:** `kafka:29092`
- **Port:** 9092 / 29092 (TCP)
- **Feladat:** Topics ellenőrzése, producerek/consumerek tesztelése

### 3.4 Zookeeper

- **Port:** 2181 (Docker belül), 22181 (Host-ról)
- **Szerepe:** Kafka koordináció (általában nem közvetlenül használod)

---

## 4. InfluxDB Konfigurálása

### 4.1 Bejelentkezés

Nyiss meg http://localhost:8086-on és jelentkezz be az admin jelszóval.

### 4.2 Bucket Ellenőrzése

- **Bucket létezik?** Menü → "Buckets" → `iot_data`
- **Retenció:** 30 nap (alapértelmezett)

## Szolgáltatások

| Service      | URL                   | Bejelentkezés  |
| ------------ | --------------------- | -------------- |
| **Grafana**  | http://localhost:3000 | admin / `.env` |
| **InfluxDB** | http://localhost:8086 | admin / `.env` |
| **Kafka**    | localhost:9092        | -              |

## InfluxDB Setup

1. http://localhost:8086 → admin jelszó
2. Bucket: `iot_data` (már létezik)
3. Token: `.env`-ben (`INFLUXDB_INIT_ADMIN_TOKEN`)

## Grafana Setup

1. http://localhost:3000 → admin jelszó
2. Connections → Data Source → InfluxDB
   - URL: `http://influxdb:8086`
   - Organization: `iot_org`
   - Token: `.env`-ből
   - Bucket: `iot_data`

## Parancsok

```bash
# Status
docker compose ps

# Logok
docker compose logs [service-name]

# Leállítás
docker compose down
docker compose down --remove-orphans  #force
# Újraindítás
docker compose restart [service-name]
```

## Verifikáció (Definition of Done)

- ✅ `docker compose ps` → Összes `Up`
- ✅ http://localhost:3000 → Grafana elérhető
- ✅ http://localhost:8086 → InfluxDB elérhető
- ✅ Grafana csatlakozik InfluxDB-hez
