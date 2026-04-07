#!/usr/bin/env python3
"""
CASTEL GAME - Quick Start Guide
Run this script to get started!
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                   CASTEL - QUICK START                     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    print("1️⃣  Checking Python version...")
    version = subprocess.run([sys.executable, "--version"], 
                           capture_output=True, text=True)
    print(f"   {version.stdout.strip()}")
    print()
    
    print("2️⃣  Running tests...")
    result = subprocess.run([sys.executable, "test_suite.py"], cwd=Path(__file__).parent)
    if result.returncode != 0:
        print("❌ Tests failed!")
        sys.exit(1)
    print()
    
    print("3️⃣  Ready to play!")
    print()
    print("   To start the game, run:")
    print("   $ python3 main.py")
    print()
    print("   Documentation:")
    print("   - README.md          : Overview")
    print("   - DOCUMENTATION.md   : Full guide")
    print("   - SUMMARY.md         : Project status")
    print()
    print("   Controls:")
    print("   - Click card: Select")
    print("   - Click board: Place")
    print("   - ESC: Quit")
    print()
    print("4️⃣  Start playing!")
    print()
    
    response = input("Start game now? (y/n): ").lower()
    if response == 'y':
        subprocess.run([sys.executable, "main.py"], cwd=Path(__file__).parent)
    else:
        print("Use 'python3 main.py' to start anytime!")

if __name__ == "__main__":
    main()
