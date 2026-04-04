## 0. Sprint: Előkészítés (A "Szívverés" beállítása)

**Cél:** A környezet stabilizálása, ahol az adatok folyni fognak (a "csővezeték" megépítése).
**Definition of Done:** Grafana (localhost:3000) és InfluxDB (localhost:8086) elérhető, bejelentkezés működik.

---

### Fázis 1: Lokális Development Environment (Docker Desktop)

**1.1** Docker Desktop telepítése (ha még nincs) → Verif: `docker --version` kiadása a terminálban

**1.2** `docker-compose.yml` konfigurálása (Zookeeper, Kafka, InfluxDB, Grafana)

**1.3** Docker stack indítása: `docker compose up -d`

**1.4** Szolgáltatások elérhetőségének ellenőrzése:

- Grafana: http://localhost:3000 (admin/admin alapértelmezés)
- InfluxDB: http://localhost:8086 (kezdeti setup szükséges)
- Kafka: localhost:9092 (Docker belső hálózaton)

---

### Fázis 2: InfluxDB Alapbeállítása (Bucket - "vödör")

**2.1** InfluxDB admin felületén bejelentkezés (http://localhost:8086)

### Fázis 3: Grafana Alapbeállítása (Kijelző)

**3.1** Grafana felületén bejelentkezés (http://localhost:3000)

**3.2** Data Source hozzáadása (InfluxDB csatlakozás):

- URL: `http://influxdb:8086`
- Bucket: `sensor-data`
- API Token: az 2.3-ból

**3.3** Egy próba Dashboard vagy vizualizáció lemez felhasználó később

---

### Fázis 4: Producer & Consumer Integrálás (Csővezeték teljessé tétele)

**4.1** IoT Producer indítása (`producers/iot_simulator.py`) → adatok küldése Kafka `iot_sensor_data` topicba

```powershell
.\.venv\Scripts\python.exe .\producers\iot_simulator.py
```

**4.2** Data Processor Consumer indítása (Kafka-ból olvassa, InfluxDB-be ír)

```powershell
.\.venv\Scripts\python.exe .\consumer\data_processor.py
```

- Olvassa a Kafka `iot_sensor_data` topicot
- Feldolgozza az IoT szenzoradatokat
- Írja az InfluxDB `iot_data` bucketbe (measurement: `iot_sensor`)
- Tagek: `sensor_id`, `location`
- Mezők: `soil_moisture`, `water_level`, `temperature`

**4.3** Grafana Dashboard ellenőrzése → Adatok láthatók-e?

---

### Fázis 5: Felhős Előkészítés (AWS Setup - Opció)

**5.1** `docker-compose.prod.yml` vázlatának elkészítése:

- Kafka `advertised.listeners`: AWS EC2 IP/domain (nem localhost)
- Volumes: AWS EBS paths dokumentálása
- Env vars: `.env.prod` fájlból olvasva

**5.2** Biztonsági vázlat:

- Security Groups: SSH (22), Grafana (3000), Kafka (9092)
- `.env.example` template létrehozása

---

### Kötelező Sikerkritériumok (Definition of Done)

- ✅ `docker ps` futó konténereket mutat
- ✅ Grafana (localhost:3000) elérhető és bejelentkezés működik
- ✅ InfluxDB (localhost:8086) elérhető, Bucket létrehozva, token generálva
- ✅ Grafana Data Source csatlakozik az InfluxDB-hez
- ✅ Producer → Kafka üzenetek folynak
- ✅ Consumer → InfluxDB adatok írása működik
- ✅ Grafana Dashboard adatpontokat jelenít meg (vagy üres, de csatlakozik)

---
