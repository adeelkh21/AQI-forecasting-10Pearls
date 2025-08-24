#!/usr/bin/env python3
"""
Production deployment script for AQI Forecasting System
"""
import os
import sys
import subprocess
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class ProductionDeployer:
    """Production deployment automation"""
    
    def __init__(self, config_path: str = None):
        self.project_root = Path(__file__).resolve().parents[2]
        self.app_dir = self.project_root / "app"
        self.config_path = config_path
        self.deployment_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log deployment message"""
        # Cross-platform timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.deployment_log.append(log_entry)
        print(log_entry)
    
    def run_command(self, command: List[str], cwd: Path = None) -> bool:
        """Run a shell command safely"""
        try:
            self.log(f"Running: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout:
                self.log(f"Output: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}", "ERROR")
            if e.stderr:
                self.log(f"Error: {e.stderr.strip()}", "ERROR")
            return False
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        self.log("Checking deployment prerequisites...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 9):
            self.log("Python 3.9+ required", "ERROR")
            return False
        
        # Check required directories
        required_dirs = [
            self.app_dir / "backend",
            self.app_dir / "frontend",
            self.app_dir / "config"
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                self.log(f"Required directory missing: {dir_path}", "ERROR")
                return False
        
        # Check if virtual environment exists
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            self.log("Virtual environment not found", "ERROR")
            return False
        
        self.log("Prerequisites check passed")
        return True
    
    def install_production_dependencies(self) -> bool:
        """Install production dependencies"""
        self.log("Installing production dependencies...")
        
        requirements_file = self.app_dir / "requirements-production.txt"
        if not requirements_file.exists():
            self.log("Production requirements file not found", "ERROR")
            return False
        
        # Activate virtual environment and install
        if os.name == 'nt':  # Windows
            pip_cmd = [str(self.project_root / "venv" / "Scripts" / "pip")]
        else:  # Unix/Linux
            pip_cmd = [str(self.project_root / "venv" / "bin" / "pip")]
        
        return self.run_command(pip_cmd + ["install", "-r", str(requirements_file)])
    
    def setup_production_config(self) -> bool:
        """Setup production configuration"""
        self.log("Setting up production configuration...")
        
        # Create production .env file
        prod_env_path = self.project_root / ".env.production"
        if not prod_env_path.exists():
            self.log("Creating production environment file...")
            env_content = """# Production Environment Configuration
# Server Configuration
PROD_HOST=0.0.0.0
PROD_PORT=8000
PROD_WORKERS=4

# Security
CORS_ORIGINS=http://localhost:8501,https://yourdomain.com
API_KEYS_ENABLED=false

# Logging
LOG_LEVEL=INFO
SYSLOG_ENABLED=false

# Monitoring
ALERTING_ENABLED=false

# Data Management
BACKUP_ENABLED=true
MAX_CONCURRENT_JOBS=5
JOB_TIMEOUT=7200

# OpenWeather API Key
OPENWEATHER_API_KEY=86e22ef485ce8beb1a30ba654f6c2d5a
"""
            prod_env_path.write_text(env_content)
            self.log("Production environment file created")
        
        return True
    
    def create_systemd_service(self) -> bool:
        """Create systemd service file for production"""
        self.log("Creating systemd service file...")
        
        service_content = f"""[Unit]
Description=AQI Forecasting System Backend
After=network.target

[Service]
Type=exec
User={os.getenv('USER', 'ubuntu')}
WorkingDirectory={self.project_root}
Environment=PATH={self.project_root}/venv/bin
ExecStart={self.project_root}/venv/bin/python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_path = Path("/etc/systemd/system/aqi-forecasting.service")
        if not service_path.exists():
            try:
                # This requires sudo privileges
                service_path.write_text(service_content)
                self.log("Systemd service file created")
                return True
            except PermissionError:
                self.log("Cannot create systemd service (requires sudo)", "WARNING")
                return False
        
        return True
    
    def create_nginx_config(self) -> bool:
        """Create nginx configuration for production"""
        self.log("Creating nginx configuration...")
        
        nginx_config = f"""server {{
    listen 80;
    server_name yourdomain.com;
    
    # Backend API
    location /api/ {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Frontend
    location / {{
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Health check
    location /health {{
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }}
}}
"""
        
        nginx_path = Path("/etc/nginx/sites-available/aqi-forecasting")
        if not nginx_path.exists():
            try:
                nginx_path.write_text(nginx_config)
                self.log("Nginx configuration created")
                return True
            except PermissionError:
                self.log("Cannot create nginx config (requires sudo)", "WARNING")
                return False
        
        return True
    
    def setup_logging(self) -> bool:
        """Setup production logging"""
        self.log("Setting up production logging...")
        
        log_dir = Path("/var/log/aqi-forecasting")
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                self.log("Log directory created")
            except PermissionError:
                self.log("Cannot create log directory (requires sudo)", "WARNING")
                return False
        
        return True
    
    def run_tests(self) -> bool:
        """Run production tests"""
        self.log("Running production tests...")
        
        # Test backend
        backend_test = self.run_command([
            "python", "-m", "pytest", "tests/", "-v"
        ], cwd=self.app_dir)
        
        # Test frontend
        frontend_test = self.run_command([
            "python", "-c", "from app.frontend.streamlit_app import main; print('Frontend import successful')"
        ], cwd=self.project_root)
        
        return backend_test and frontend_test
    
    def deploy(self) -> bool:
        """Run complete production deployment"""
        self.log("Starting production deployment...")
        
        steps = [
            ("Checking prerequisites", self.check_prerequisites),
            ("Installing production dependencies", self.install_production_dependencies),
            ("Setting up production configuration", self.setup_production_config),
            ("Creating systemd service", self.create_systemd_service),
            ("Creating nginx configuration", self.create_nginx_config),
            ("Setting up logging", self.setup_logging),
            ("Running tests", self.run_tests)
        ]
        
        for step_name, step_func in steps:
            self.log(f"Step: {step_name}")
            if not step_func():
                self.log(f"Deployment failed at: {step_name}", "ERROR")
                return False
        
        self.log("Production deployment completed successfully!")
        return True
    
    def save_deployment_log(self, log_path: str = "deployment.log"):
        """Save deployment log to file"""
        log_file = self.project_root / log_path
        log_file.write_text("\n".join(self.deployment_log))
        self.log(f"Deployment log saved to: {log_file}")

def main():
    """Main deployment function"""
    deployer = ProductionDeployer()
    
    if deployer.deploy():
        deployer.save_deployment_log()
        print("\n🎉 Production deployment completed successfully!")
        print("Next steps:")
        print("1. Configure your domain in nginx config")
        print("2. Enable and start systemd service: sudo systemctl enable aqi-forecasting")
        print("3. Start the service: sudo systemctl start aqi-forecasting")
        print("4. Check status: sudo systemctl status aqi-forecasting")
        return 0
    else:
        deployer.save_deployment_log("deployment-error.log")
        print("\n❌ Production deployment failed!")
        print("Check deployment-error.log for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())
