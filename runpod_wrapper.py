#!/usr/bin/env python3
"""
RunPod Wrapper for TKR News Gather
This serves as the entry point for RunPod serverless execution
"""

import os
import sys

def main():
    """Main entry point - detect if running in RunPod serverless environment"""
    
    print("=== TKR News Gather Container Starting ===")
    print(f"Environment variables: {list(os.environ.keys())}")
    
    # Check multiple possible RunPod environment indicators
    runpod_indicators = [
        'RUNPOD_ENDPOINT_ID', 'RUNPOD_POD_ID', 'RUNPOD_API_KEY',
        'RUNPOD_TEMPLATE_ID', 'RUNPOD_DC_ID', 'RUNPOD'
    ]
    
    is_runpod = any(os.environ.get(var) for var in runpod_indicators)
    
    print(f"RunPod environment detected: {is_runpod}")
    
    # Always try RunPod mode first (since this is intended for serverless)
    try:
        print("Attempting to start RunPod serverless worker...")
        import runpod
        from runpod_handler import handler
        
        print("RunPod SDK imported successfully")
        print("Handler imported successfully")
        print("Starting serverless worker...")
        
        runpod.serverless.start({"handler": handler})
        
    except ImportError as e:
        print(f"RunPod SDK not available: {e}")
        print("This might be a local environment - starting FastAPI server instead...")
        
        # Fallback to regular API server
        print("Starting FastAPI server...")
        import subprocess
        subprocess.run([sys.executable, "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"])
        
    except Exception as e:
        print(f"Error starting RunPod worker: {e}")
        print("Falling back to FastAPI server...")
        
        import subprocess
        subprocess.run([sys.executable, "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    main()