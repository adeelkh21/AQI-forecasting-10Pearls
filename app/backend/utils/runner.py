import subprocess
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

from .paths import RUN_PY, ROOT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    success: bool
    duration: float
    
    @property
    def failed(self) -> bool:
        return self.returncode != 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "returncode": self.returncode,
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration
        }


def run_py(args: List[str], timeout: int = 3600, cwd: Optional[Path] = None) -> RunResult:
    """
    Run a Python script with the virtual environment interpreter.
    
    Args:
        args: List of arguments to pass to python
        timeout: Timeout in seconds
        cwd: Working directory for the command
        
    Returns:
        RunResult with execution details
    """
    import time
    
    start_time = time.time()
    cmd = [RUN_PY] + args
    working_dir = str(cwd) if cwd else str(ROOT)
    
    logger.info(f"Running: {' '.join(cmd)} (cwd: {working_dir})")
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=working_dir
        )
        
        duration = time.time() - start_time
        success = proc.returncode == 0
        
        if success:
            logger.info(f"Command succeeded in {duration:.2f}s")
        else:
            logger.warning(f"Command failed with return code {proc.returncode} in {duration:.2f}s")
            if proc.stderr:
                logger.warning(f"Stderr: {proc.stderr[:500]}...")
        
        return RunResult(
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            success=success,
            duration=duration
        )
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"Command timed out after {timeout}s")
        return RunResult(
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            success=False,
            duration=duration
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Command failed with exception: {e}")
        return RunResult(
            returncode=-1,
            stdout="",
            stderr=str(e),
            success=False,
            duration=duration
        )


def run_script(script_path: Path, args: List[str] = None, timeout: int = 3600) -> RunResult:
    """
    Run a specific script with optional arguments.
    
    Args:
        script_path: Path to the script to run
        args: Additional arguments for the script
        timeout: Timeout in seconds
        
    Returns:
        RunResult with execution details
    """
    if args is None:
        args = []
    
    if not script_path.exists():
        return RunResult(
            returncode=-1,
            stdout="",
            stderr=f"Script not found: {script_path}",
            success=False,
            duration=0.0
        )
    
    return run_py([str(script_path)] + args, timeout=timeout, cwd=script_path.parent)


def check_script_exists(script_path: Path) -> bool:
    """Check if a script exists and is executable."""
    return script_path.exists() and script_path.is_file()


