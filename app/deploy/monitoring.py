"""
Production monitoring configuration for AQI Forecasting System
"""
import os
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    uptime: float

@dataclass
class ApplicationMetrics:
    """Application performance metrics"""
    timestamp: datetime
    active_connections: int
    request_count: int
    response_time_avg: float
    error_rate: float
    cache_hit_rate: float
    job_queue_length: int
    active_jobs: int

class ProductionMonitor:
    """Production system monitoring"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or "/var/log/aqi-forecasting/monitoring.log"
        self.metrics_history: List[SystemMetrics] = []
        self.app_metrics_history: List[ApplicationMetrics] = []
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "error_rate": 5.0,
            "response_time_avg": 2.0  # seconds
        }
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """Setup monitoring logging"""
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network metrics
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Process metrics
            process_count = len(psutil.pids())
            
            # Uptime
            uptime = time.time() - psutil.boot_time()
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_io,
                process_count=process_count,
                uptime=uptime
            )
            
            self.metrics_history.append(metrics)
            
            # Keep only last 1000 metrics (about 16 hours at 1-minute intervals)
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return None
    
    def collect_application_metrics(self, api_client) -> ApplicationMetrics:
        """Collect application performance metrics"""
        try:
            # Get system status
            status_response = api_client.get("/api/v1/system/status")
            if not status_response.get('success'):
                return None
            
            data = status_response.get('data', {})
            
            # Extract metrics
            active_connections = data.get('active_connections', 0)
            request_count = data.get('request_count', 0)
            response_time_avg = data.get('response_time_avg', 0.0)
            error_rate = data.get('error_rate', 0.0)
            cache_hit_rate = data.get('cache_hit_rate', 0.0)
            
            # Get job metrics
            jobs_response = api_client.get("/api/v1/jobs/statistics")
            if jobs_response.get('success'):
                job_data = jobs_response.get('data', {})
                job_queue_length = job_data.get('queue_length', 0)
                active_jobs = job_data.get('current_status', {}).get('running', 0)
            else:
                job_queue_length = 0
                active_jobs = 0
            
            metrics = ApplicationMetrics(
                timestamp=datetime.now(),
                active_connections=active_connections,
                request_count=request_count,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
                cache_hit_rate=cache_hit_rate,
                job_queue_length=job_queue_length,
                active_jobs=active_jobs
            )
            
            self.app_metrics_history.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.app_metrics_history) > 1000:
                self.app_metrics_history = self.app_metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {e}")
            return None
    
    def check_alerts(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        
        if system_metrics:
            # CPU alert
            if system_metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
                alerts.append({
                    "level": "WARNING",
                    "type": "SYSTEM",
                    "metric": "CPU_USAGE",
                    "value": system_metrics.cpu_percent,
                    "threshold": self.alert_thresholds["cpu_percent"],
                    "message": f"High CPU usage: {system_metrics.cpu_percent:.1f}%"
                })
            
            # Memory alert
            if system_metrics.memory_percent > self.alert_thresholds["memory_percent"]:
                alerts.append({
                    "level": "WARNING",
                    "type": "SYSTEM",
                    "metric": "MEMORY_USAGE",
                    "value": system_metrics.memory_percent,
                    "threshold": self.alert_thresholds["memory_percent"],
                    "message": f"High memory usage: {system_metrics.memory_percent:.1f}%"
                })
            
            # Disk alert
            if system_metrics.disk_percent > self.alert_thresholds["disk_percent"]:
                alerts.append({
                    "level": "CRITICAL",
                    "type": "SYSTEM",
                    "metric": "DISK_USAGE",
                    "value": system_metrics.disk_percent,
                    "threshold": self.alert_thresholds["disk_percent"],
                    "message": f"Critical disk usage: {system_metrics.disk_percent:.1f}%"
                })
        
        if app_metrics:
            # Error rate alert
            if app_metrics.error_rate > self.alert_thresholds["error_rate"]:
                alerts.append({
                    "level": "WARNING",
                    "type": "APPLICATION",
                    "metric": "ERROR_RATE",
                    "value": app_metrics.error_rate,
                    "threshold": self.alert_thresholds["error_rate"],
                    "message": f"High error rate: {app_metrics.error_rate:.1f}%"
                })
            
            # Response time alert
            if app_metrics.response_time_avg > self.alert_thresholds["response_time_avg"]:
                alerts.append({
                    "level": "WARNING",
                    "type": "APPLICATION",
                    "metric": "RESPONSE_TIME",
                    "value": app_metrics.response_time_avg,
                    "threshold": self.alert_thresholds["response_time_avg"],
                    "message": f"Slow response time: {app_metrics.response_time_avg:.2f}s"
                })
        
        return alerts
    
    def generate_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate monitoring report for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter metrics by time
        recent_system_metrics = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        recent_app_metrics = [
            m for m in self.app_metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_system_metrics:
            return {"error": "No metrics available for the specified time period"}
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_system_metrics) / len(recent_system_metrics)
        avg_memory = sum(m.memory_percent for m in recent_system_metrics) / len(recent_system_metrics)
        avg_disk = sum(m.disk_percent for m in recent_system_metrics) / len(recent_system_metrics)
        
        # Find peaks
        peak_cpu = max(m.cpu_percent for m in recent_system_metrics)
        peak_memory = max(m.memory_percent for m in recent_system_metrics)
        peak_disk = max(m.disk_percent for m in recent_system_metrics)
        
        report = {
            "period_hours": hours,
            "timestamp": datetime.now().isoformat(),
            "system_metrics": {
                "average": {
                    "cpu_percent": round(avg_cpu, 2),
                    "memory_percent": round(avg_memory, 2),
                    "disk_percent": round(avg_disk, 2)
                },
                "peak": {
                    "cpu_percent": round(peak_cpu, 2),
                    "memory_percent": round(peak_memory, 2),
                    "disk_percent": round(peak_disk, 2)
                },
                "sample_count": len(recent_system_metrics)
            }
        }
        
        if recent_app_metrics:
            avg_response_time = sum(m.response_time_avg for m in recent_app_metrics) / len(recent_app_metrics)
            avg_error_rate = sum(m.error_rate for m in recent_app_metrics) / len(recent_app_metrics)
            
            report["application_metrics"] = {
                "average": {
                    "response_time_avg": round(avg_response_time, 3),
                    "error_rate": round(avg_error_rate, 2)
                },
                "sample_count": len(recent_app_metrics)
            }
        
        return report
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous monitoring"""
        self.logger.info(f"Starting production monitoring (interval: {interval_seconds}s)")
        
        try:
            while True:
                # Collect metrics
                system_metrics = self.collect_system_metrics()
                
                # Check for alerts
                alerts = self.check_alerts(system_metrics, None)
                
                # Log alerts
                for alert in alerts:
                    if alert["level"] == "CRITICAL":
                        self.logger.critical(alert["message"])
                    elif alert["level"] == "WARNING":
                        self.logger.warning(alert["message"])
                
                # Wait for next interval
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")

def main():
    """Main monitoring function"""
    monitor = ProductionMonitor()
    
    # Start monitoring
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
