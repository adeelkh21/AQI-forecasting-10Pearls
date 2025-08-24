#!/usr/bin/env python3
"""
Launch script for the AQI Forecasting System Streamlit frontend
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def main():
    """Main launch function"""
    parser = argparse.ArgumentParser(description="Launch AQI Forecasting System Streamlit Frontend")
    parser.add_argument("--port", type=int, default=8501, help="Port to run Streamlit on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    app_file = script_dir / "streamlit_app.py"
    
    if not app_file.exists():
        print(f"❌ Error: Streamlit app file not found at {app_file}")
        sys.exit(1)
    
    # Set environment variables
    env = os.environ.copy()
    env["STREAMLIT_SERVER_PORT"] = str(args.port)
    env["STREAMLIT_SERVER_ADDRESS"] = args.host
    
    if args.debug:
        env["STREAMLIT_LOGGER_LEVEL"] = "debug"
    
    # Build Streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_file),
        "--server.port", str(args.port),
        "--server.address", args.host,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    if args.debug:
        cmd.extend(["--logger.level", "debug"])
    
    print(f"🚀 Launching AQI Forecasting System Streamlit Frontend...")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"📁 App file: {app_file}")
    print(f"🔧 Debug mode: {args.debug}")
    print("---")
    
    try:
        # Launch Streamlit
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Streamlit frontend stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Streamlit: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: Streamlit not found. Please install it with: pip install streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main()
