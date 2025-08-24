"""
Safe subprocess execution utilities for the AQI Forecasting System
"""
import subprocess
import logging
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from .paths import get_python_executable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    """Result of a subprocess execution"""
    success: bool
    return_code: int
    stdout: str
    stderr: str
    execution_time: float
    command: str
    error_message: Optional[str] = None

class ScriptRunner:
    """Safe script execution with timeout and error handling"""
    
    def __init__(self, timeout: int = 3600):
        self.timeout = timeout
        self.python_executable = get_python_executable()
    
    def run_script(self, script_path: Path, args: list = None, timeout: int = None) -> ExecutionResult:
        """
        Run a Python script safely
        
        Args:
            script_path: Path to the Python script
            args: Additional arguments to pass to the script
            timeout: Execution timeout in seconds (overrides default)
        
        Returns:
            ExecutionResult with execution details
        """
        if args is None:
            args = []
        
        if timeout is None:
            timeout = self.timeout
        
        # Build the command
        command = [self.python_executable, str(script_path)] + args
        command_str = " ".join(command)
        
        logger.info(f"🚀 Executing script: {command_str}")
        start_time = time.time()
        
        try:
            # Execute the script
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=script_path.parent
            )
            
            execution_time = time.time() - start_time
            
            # Check if execution was successful
            success = result.returncode == 0
            
            if success:
                logger.info(f"✅ Script executed successfully in {execution_time:.2f}s")
            else:
                logger.error(f"❌ Script failed with return code {result.returncode}")
            
            return ExecutionResult(
                success=success,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                command=command_str
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            error_msg = f"Script execution timed out after {timeout}s"
            logger.error(f"⏰ {error_msg}")
            
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=error_msg,
                execution_time=execution_time,
                command=command_str,
                error_message=error_msg
            )
            
        except FileNotFoundError:
            execution_time = time.time() - start_time
            error_msg = f"Script not found: {script_path}"
            logger.error(f"📁 {error_msg}")
            
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=error_msg,
                execution_time=execution_time,
                command=command_str,
                error_message=error_msg
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"💥 {error_msg}")
            
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=error_msg,
                execution_time=execution_time,
                command=command_str,
                error_message=error_msg
            )
    
    def run_collect_script(self, timeout: int = 1800) -> ExecutionResult:
        """Run the data collection script"""
        from .paths import COLLECT_SCRIPT
        return self.run_script(COLLECT_SCRIPT, timeout=timeout)
    
    def run_pipeline_script(self, timeout: int = 3600) -> ExecutionResult:
        """Run the combined data pipeline script"""
        from .paths import COMBINED_PIPELINE_SCRIPT
        return self.run_script(COMBINED_PIPELINE_SCRIPT, timeout=timeout)
    
    def run_forecast_script(self, timeout: int = 1800) -> ExecutionResult:
        """Run the forecasting script"""
        from .paths import FORECAST_SCRIPT
        return self.run_script(FORECAST_SCRIPT, timeout=timeout)
    
    def validate_script(self, script_path: str | Path) -> bool:
        """Validate that a script exists and is executable"""
        # Convert string to Path if needed
        if isinstance(script_path, str):
            script_path = Path(script_path)
        
        if not script_path.exists():
            logger.error(f"❌ Script not found: {script_path}")
            return False
        
        if not script_path.is_file():
            logger.error(f"❌ Path is not a file: {script_path}")
            return False
        
        # Check if it's a Python file
        if script_path.suffix != '.py':
            logger.error(f"❌ Not a Python file: {script_path}")
            return False
        
        logger.info(f"✅ Script validated: {script_path}")
        return True

def format_execution_result(result: ExecutionResult) -> Dict[str, Any]:
    """Format execution result for API response"""
    return {
        "success": result.success,
        "return_code": result.return_code,
        "execution_time": round(result.execution_time, 2),
        "command": result.command,
        "stdout": result.stdout.strip() if result.stdout else "",
        "stderr": result.stderr.strip() if result.stderr else "",
        "error_message": result.error_message,
        "status": "success" if result.success else "failed"
    }

if __name__ == "__main__":
    # Test the runner
    runner = ScriptRunner()
    
    # Test path validation
    from .paths import COLLECT_SCRIPT, COMBINED_PIPELINE_SCRIPT, FORECAST_SCRIPT
    
    print("🔍 Testing script validation...")
    scripts = [COLLECT_SCRIPT, COMBINED_PIPELINE_SCRIPT, FORECAST_SCRIPT]
    
    for script in scripts:
        if runner.validate_script(script):
            print(f"✅ {script.name} is valid")
        else:
            print(f"❌ {script.name} is invalid")
    
    print(f"🐍 Python executable: {runner.python_executable}")
