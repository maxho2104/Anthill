"""
Build script for Document Workflow Management Application using PyInstaller
"""
import subprocess
import sys
import os

def build_executable():
    """Build the application executable using PyInstaller"""
    try:
        # Install pyinstaller if not already installed
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
        # Build command - using OS-agnostic syntax
        import platform
        if platform.system() == 'Windows':
            # Windows uses semicolon separator
            add_data_param = "--add-data=document_storage;document_storage"
        else:
            # Linux/MacOS uses colon separator
            add_data_param = "--add-data=document_storage:document_storage"
        
        cmd = [
            "pyinstaller",
            "--onefile",           # Create a single executable file
            "--windowed",          # Create a GUI application (no console on Windows)
            "--name=DocumentWorkflowApp",  # Name of the executable
            "--hidden-import=PyQt5.sip",   # Include hidden imports
            "main.py"
        ]
        
        print("Building executable...")
        subprocess.run(cmd, check=True)
        print("Build completed successfully!")
        print("Executable located in dist/ folder")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()