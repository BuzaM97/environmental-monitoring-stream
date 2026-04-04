# Projekt Kontextus: IoT és Műholdas Adatstream Platform

## 🎯 Projekt Leírása

Egy end-to-end adatfeldolgozó platformot fejlesztek, amely egyesíti a távérzékelési adatokat és a szimulált IoT szenzoradatokat egy közös dashboardon. A cél egy környezeti monitoring rendszer prototípusa, amely a vízmennyiség változását követi.
A projekt kiemelt célja egy valódi **"Edge-to-Cloud" architektúra** szimulálása, ahol az adatgyűjtés lokálisan (Edge), a feldolgozás és vizualizáció pedig a felhőben (AWS EC2) történik, 24/7 rendelkezésre állást biztosítva.

## 🛠 Technológiai Stack

- **Adatforrás 1 (API):** Sentinel Hub API (Sentinel-2 műholdas adatok, NDWI index számítás).
- **Adatforrás 2 (Edge):** Python-alapú IoT szimulátor (szimulált talajnedvesség és vízszint adatok).
- **Üzenetközvetítő (Cloud):** Apache Kafka (Docker konténerben, publikus IP-re konfigurálva).
- **Adatbázis (Cloud):** InfluxDB 2.x (Idősoros adatbázis tartós EBS tárolón).
- **Vizualizáció (Cloud):** Grafana.
- **Infrastruktúra:** Docker & Docker Compose, üzemeltetve AWS EC2 példányon (Ubuntu 24.04 LTS).

## 🏗 Architektúra Felépítése

1.  **Producerek (Lokális futtatás):** Különálló Python szkriptek, amelyek JSON formátumban küldenek adatokat az interneten keresztül a felhőben futó Kafka topicokba.
2.  **Consumer (Felhős futtatás):** Egy Python feldolgozó egység a felhőben, amely kiolvassa a Kafka üzeneteket és az InfluxDB Python kliensén keresztül aszinkron módon menti az adatokat.
3.  **Dockerizálás:** A szerver oldali komponensek (Kafka, Influx, Grafana, Consumer) konténerekben futnak a felhőben, egyetlen `docker-compose.prod.yml` által vezérelve.

## 🤝 Miben várok segítséget (Fókuszpontok)

- A Docker-környezet (`docker-compose.prod.yml`) felhő-specifikus konfigurálása (pl. hálózatok, `restart: always` szabályok, volume perzisztencia).
- A Kafka `advertised.listeners` beállítása úgy, hogy biztonságosan fogadjon üzeneteket a lokális gépemről (Edge).
- Biztonsági beállítások az AWS-en (Security Groups, tűzfalak, környezeti változók kezelése `.env` fájlokkal).
- A Python producerek robusztusabbá tétele (újracsatlakozási kísérletek hálózati hiba esetén).

---

## 🚀 IMPLEMENTÁCIÓ ÉS KONFIGURÁLÁS

### ✅ Befejezett Lépések (Lokális Tesztfázis)

- **Docker Stack Konfigurálása:** `docker-compose.yml` kész (Zookeeper, Kafka, InfluxDB, Grafana).
- **Tesztelési Infrastruktúra:** `test_stack.py` és dokumentációk létrehozva.
- **Python Függőségek:** `requirements.txt` összeállítva (kafka-python, influxdb-client, requests, apscheduler, python-dotenv).
- **Producer & Consumer Architektúra:**
  - IoT Simulator (30-60 sec) -> `iot_sensor_data` topic.
  - Sentinel API (Napi 1x) -> `sentinel_data` topic.
  - Consumer elkészítve és tesztelve a lokális adatbázis írással.

### 📋 Rendszer Állapota

| Komponens    | Státusz           | Megjegyzés                                   |
| ------------ | ----------------- | -------------------------------------------- |
| Docker Stack | ✅ Lokálisan Kész | Felhős migráció (AWS) következik             |
| Producerek   | ✅ Kész           | Hálózati hibakezelés finomítása hátravan     |
| Consumer     | ✅ Kész           | Stabil adatbázis írás                        |
| Grafana      | ⏳ Folyamatban    | Dashboardok kialakítása a végleges adatokból |
| AWS EC2      | ⏳ Tervezve       | Infrastruktúra előkészítése és telepítés     |

### 🔄 Következő Lépések (Felhőbe költözés Sprint)

1.  **AWS Infrastruktúra Előkészítése:** EC2 példány indítása, Docker Engine telepítése.
2.  **Biztonság Beállítása:** Security Groupok konfigurálása (csak a szükséges portok nyitása: 22, 3000, és a Kafka/Influx biztonságos elérése).
3.  **Deployment:** A `docker-compose` stacket és a Consumert feltölteni a felhőbe, és elindítani.
4.  **Rendszer Integráció teszt:** A lokális (saját gépen futó) IoT és Sentinel szkriptek rákötése a felhős Kafkára.
5.  **Vizualizáció Véglegesítése:** Grafana dashboardok publikálása.
