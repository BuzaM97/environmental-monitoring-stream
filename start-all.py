#!/usr/bin/env python3
"""
IoT Platform Startup Script
Platform-független megoldás (Windows, macOS, Linux)
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

class IoTStartup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_python = self._get_python_executable()
        self.processes = []
        
    def _get_python_executable(self):
        """Virtuális environment Python keresése"""
        venv_path = self.project_root / ".venv"
        
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            
        if not python_exe.exists():
            print("❌ Python venv nem található!")
            print("Kérlek futtasd: python -m venv .venv")
            sys.exit(1)
            
        return str(python_exe)
    
    def _print_header(self, text):
        """Szép fejléc kiírása"""
        print("\n" + "="*50)
        print(f"  {text}")
        print("="*50)
    
    def _print_step(self, step, text):
        """Lépés kiírása"""
        print(f"\n[{step}] {text}...")
    
    def start_docker(self):
        """Docker Compose indítása"""
        self._print_step("1/4", "Docker Compose indítása")
        
        compose_file = self.project_root / "docker-compose.yml"
        if not compose_file.exists():
            print("  ❌ docker-compose.yml nem található!")
            return False
        
        try:
            print("  Konténerek indítása...")
            subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=self.project_root,
                check=True
            )
            print("  ✓ Docker konténerek elindítva")
            print("  ⏳ Várakozás a szolgáltatások indulására (60 másodperc)...")
            time.sleep(60)
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Docker indítás sikertelen: {e}")
            return False
        except FileNotFoundError:
            print("  ❌ Docker nem telepítve vagy nem elérhető!")
            return False
    
    def start_producer(self):
        """IoT Simulator Producer indítása"""
        self._print_step("2/4", "IoT Simulator Producer indítása")
        
        producer_script = self.project_root / "producers" / "iot_simulator.py"
        if not producer_script.exists():
            print("  ❌ Producer script nem található!")
            return False
        
        try:
            if sys.platform == "win32":
                # Windows: külön PowerShell ablakban
                proc = subprocess.Popen(
                    ["powershell", "-NoExit", "-Command", 
                     f"cd '{self.project_root}'; & '{self.venv_python}' '{producer_script}'"],
                    stdout=None,
                    stderr=None
                )
            else:
                # macOS/Linux: külön terminál ablakban vagy egyszerűen futtatva
                proc = subprocess.Popen(
                    [self.venv_python, str(producer_script)],
                    cwd=self.project_root,
                    stdout=None,
                    stderr=None
                )
            self.processes.append(("Producer", proc))
            print(f"  ✓ Producer indítva (PID: {proc.pid})")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"  ❌ Producer indítás sikertelen: {e}")
            return False
    
    def start_sentinel_producer(self):
        """Sentinel API Producer indítása"""
        self._print_step("2.5/4", "Sentinel API Producer indítása")
        
        producer_script = self.project_root / "producers" / "sentinel_api.py"
        if not producer_script.exists():
            print("  ❌ Sentinel Producer script nem található!")
            return False
        
        try:
            if sys.platform == "win32":
                # Windows: külön PowerShell ablakban
                proc = subprocess.Popen(
                    ["powershell", "-NoExit", "-Command", 
                     f"cd '{self.project_root}'; & '{self.venv_python}' '{producer_script}'"],
                    stdout=None,
                    stderr=None
                )
            else:
                # macOS/Linux: külön terminál ablakban vagy egyszerűen futtatva
                proc = subprocess.Popen(
                    [self.venv_python, str(producer_script)],
                    cwd=self.project_root,
                    stdout=None,
                    stderr=None
                )
            self.processes.append(("Sentinel Producer", proc))
            print(f"  ✓ Sentinel Producer indítva (PID: {proc.pid})")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"  ❌ Sentinel Producer indítás sikertelen: {e}")
            return False
    
    def start_consumer(self):
        """Data Processor Consumer indítása"""
        self._print_step("3/4", "Data Processor Consumer indítása")
        
        consumer_script = self.project_root / "consumer" / "data_processor.py"
        if not consumer_script.exists():
            print("  ❌ Consumer script nem található!")
            return False
        
        try:
            if sys.platform == "win32":
                # Windows: külön PowerShell ablakban
                proc = subprocess.Popen(
                    ["powershell", "-NoExit", "-Command", 
                     f"cd '{self.project_root}'; & '{self.venv_python}' '{consumer_script}'"],
                    stdout=None,
                    stderr=None
                )
            else:
                # macOS/Linux: külön terminál ablakban vagy egyszerűen futtatva
                proc = subprocess.Popen(
                    [self.venv_python, str(consumer_script)],
                    cwd=self.project_root,
                    stdout=None,
                    stderr=None
                )
            self.processes.append(("Consumer", proc))
            print(f"  ✓ Consumer indítva (PID: {proc.pid})")
            return True
        except Exception as e:
            print(f"  ❌ Consumer indítás sikertelen: {e}")
            return False
    
    def show_info(self):
        """Információs panel"""
        self._print_step("4/4", "Összefoglalás")
        
        print("\n📊 Szolgáltatások:")
        print("  • Grafana: http://localhost:3000 (admin/admin)")
        print("  • InfluxDB: http://localhost:8086")
        print("  • Kafka: localhost:9092")
        print("  • Sentinel Hub API: Az aktuális OAuth2 token szükséges")
        
        print("\n📋 Futó processek:")
        for name, proc in self.processes:
            status = "✓ Futó" if proc.poll() is None else "❌ Leállt"
            print(f"  {name}: PID {proc.pid} ({status})")
    
    def cleanup(self, signum=None, frame=None):
        """Graceful shutdown"""
        print("\n\n⏹️  Leállítás...")
        
        for name, proc in self.processes:
            if proc.poll() is None:
                print(f"  Leállítom: {name} (PID {proc.pid})")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        
        print("  ✓ Összes process leállítva")
        sys.exit(0)
    
    def run(self):
        """Főprogram"""
        self._print_header("IoT Platform - Startup Script")
        
        # Shutdown handler beállítása
        signal.signal(signal.SIGINT, self.cleanup)
        
        if not self.start_docker():
            print("⚠️  Docker indítás meghiúsult, de folytatom...")
            return
        
        if not self.start_producer():
            print("⚠️  Producer indítás meghiúsult!")
            return
        time.sleep(20)  # Rövid várakozás a producer előtt
        if not self.start_sentinel_producer():
            print("⚠️  Sentinel Producer indítás meghiúsult!")
            return
        
        if not self.start_consumer():
            print("⚠️  Consumer indítás meghiúsult!")
            return
        
        self._print_header("✓ Összes szolgáltatás elindítva!")
        self.show_info()
        
        print("\n💡 Tippek:")
        print("  • Leállítás: Ctrl+C")
        print("  • Docker leállítása: docker compose down")
        print("  • Logok megtekintése: docker compose logs -f")
        
        print("\n(Nyomj Ctrl+C a leállításhoz)\n")
        
        # Várakozás
        try:
            while True:
                time.sleep(1)
                # Ellenőrizzük, hogy a processek még futnak-e
                for name, proc in self.processes:
                    if proc.poll() is not None:
                        print(f"\n⚠️  {name} leállt (exit code: {proc.returncode})")
        except KeyboardInterrupt:
            self.cleanup()

if __name__ == "__main__":
    starter = IoTStartup()
    starter.run()
