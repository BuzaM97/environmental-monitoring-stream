#!/usr/bin/env python3
"""
IoT Platform Startup Script
Cross-platform solution (Windows, macOS, Linux)
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
        """Find Python executable from virtual environment"""
        venv_path = self.project_root / ".venv"
        
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            
        if not python_exe.exists():
            print("ERROR: Python venv not found!")
            print("Please run: python -m venv .venv")
            sys.exit(1)
            
        return str(python_exe)
    
    def _print_header(self, text):
        """Print a nice header"""
        print("\n" + "="*50)
        print(f"  {text}")
        print("="*50)
    
    def _print_step(self, step, text):
        """Print a step message"""
        print(f"\n[{step}] {text}...")
    
    def start_docker(self):
        """Start Docker Compose services"""
        self._print_step("1/4", "Starting Docker Compose")
        
        compose_file = self.project_root / "docker-compose.yml"
        if not compose_file.exists():
            print("  ERROR: docker-compose.yml not found!")
            return False
        
        try:
            print("  Starting containers...")
            subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=self.project_root,
                check=True
            )
            print("  OK: Docker containers started")
            print("  Waiting for services to start (60 seconds)...")
            time.sleep(60)
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: Docker startup failed: {e}")
            return False
        except FileNotFoundError:
            print("  ERROR: Docker not installed or not available!")
            return False
    
    def start_producer(self):
        """Start IoT Simulator Producer"""
        self._print_step("2/4", "Starting IoT Simulator Producer")
        
        producer_script = self.project_root / "producers" / "iot_simulator.py"
        if not producer_script.exists():
            print("  ERROR: Producer script not found!")
            return False
        
        try:
            if sys.platform == "win32":
                # Windows: separate PowerShell window
                proc = subprocess.Popen(
                    ["powershell", "-NoExit", "-Command", 
                     f"cd '{self.project_root}'; & '{self.venv_python}' '{producer_script}'"],
                    stdout=None,
                    stderr=None
                )
            else:
                # macOS/Linux: separate terminal window
                proc = subprocess.Popen(
                    [self.venv_python, str(producer_script)],
                    cwd=self.project_root,
                    stdout=None,
                    stderr=None
                )
            self.processes.append(("Producer", proc))
            print(f"  OK: Producer started (PID: {proc.pid})")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"  ERROR: Producer startup failed: {e}")
            return False
    
    def start_sentinel_producer(self):
        """Start Sentinel API Producer"""
        self._print_step("2.5/4", "Starting Sentinel API Producer")
        
        producer_script = self.project_root / "producers" / "sentinel_api.py"
        if not producer_script.exists():
            print("  ERROR: Sentinel Producer script not found!")
            return False
        
        try:
            if sys.platform == "win32":
                # Windows: separate PowerShell window
                proc = subprocess.Popen(
                    ["powershell", "-NoExit", "-Command", 
                     f"cd '{self.project_root}'; & '{self.venv_python}' '{producer_script}'"],
                    stdout=None,
                    stderr=None
                )
            else:
                # macOS/Linux: separate terminal window
                proc = subprocess.Popen(
                    [self.venv_python, str(producer_script)],
                    cwd=self.project_root,
                    stdout=None,
                    stderr=None
                )
            self.processes.append(("Sentinel Producer", proc))
            print(f"  OK: Sentinel Producer started (PID: {proc.pid})")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"  ERROR: Sentinel Producer startup failed: {e}")
            return False
    
    def start_consumer(self):
        """Start Data Processor Consumer"""
        self._print_step("3/4", "Starting Data Processor Consumer")
        
        consumer_script = self.project_root / "consumer" / "data_processor.py"
        if not consumer_script.exists():
            print("  ERROR: Consumer script not found!")
            return False
        
        try:
            if sys.platform == "win32":
                # Windows: separate PowerShell window
                proc = subprocess.Popen(
                    ["powershell", "-NoExit", "-Command", 
                     f"cd '{self.project_root}'; & '{self.venv_python}' '{consumer_script}'"],
                    stdout=None,
                    stderr=None
                )
            else:
                # macOS/Linux: separate terminal window
                proc = subprocess.Popen(
                    [self.venv_python, str(consumer_script)],
                    cwd=self.project_root,
                    stdout=None,
                    stderr=None
                )
            self.processes.append(("Consumer", proc))
            print(f"  OK: Consumer started (PID: {proc.pid})")
            return True
        except Exception as e:
            print(f"  ERROR: Consumer startup failed: {e}")
            return False
    
    def show_info(self):
        """Show information panel"""
        self._print_step("4/4", "Summary")
        
        print("\nServices:")
        print("  * Grafana: http://localhost:3000 (admin/admin)")
        print("  * InfluxDB: http://localhost:8086")
        print("  * Kafka: localhost:9092")
        print("  * Sentinel Hub API: Requires OAuth2 token")
        
        print("\nRunning processes:")
        for name, proc in self.processes:
            status = "Running" if proc.poll() is None else "Stopped"
            print(f"  {name}: PID {proc.pid} ({status})")
    
    def cleanup(self, signum=None, frame=None):
        """Graceful shutdown"""
        print("\n\nShutting down...")
        
        for name, proc in self.processes:
            if proc.poll() is None:
                print(f"  Stopping: {name} (PID {proc.pid})")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        
        print("  OK: All processes stopped")
        sys.exit(0)
    
    def run(self):
        """Main program"""
        self._print_header("IoT Platform - Startup Script")
        
        # Set up shutdown handler
        signal.signal(signal.SIGINT, self.cleanup)
        
        if not self.start_docker():
            print("WARNING: Docker startup failed, but continuing...")
            return
        
        if not self.start_producer():
            print("WARNING: Producer startup failed!")
            return
        time.sleep(20)  # Short wait before producer
        if not self.start_sentinel_producer():
            print("WARNING: Sentinel Producer startup failed!")
            return
        
        if not self.start_consumer():
            print("WARNING: Consumer startup failed!")
            return
        
        self._print_header("OK: All services started!") 
        self.show_info()
        
        print("\nTips:")
        print("  * Stop: Ctrl+C")
        print("  * Stop Docker: docker compose down")
        print("  * View logs: docker compose logs -f")
        
        print("\n(Press Ctrl+C to stop)\n")
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
