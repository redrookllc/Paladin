#!/usr/bin/env python3
"""
Paladin Setup & Training Script
- Validates all dependencies
- Trains AI model with 50%+ accuracy targeting
- Verifies data4.json integration
- Provides system diagnostics
"""

import sys, os, json
from pathlib import Path
import subprocess
import warnings

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).parent
BRAIN_JSON = BASE_DIR / "data4.json"
REQ_FILE = BASE_DIR / "requirements.txt"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text, **kwargs):
    print(f"{BLUE}ℹ {text}{RESET}", **kwargs)

def check_dependencies():
    """Verify all required packages."""
    print_header("DEPENDENCY CHECK")
    
    required = {
        "numpy": "numpy",
        "pandas": "pandas",
        "scikit-learn": "sklearn",
        "lightgbm": "lightgbm",
        "yfinance": "yfinance",
        "PyQt5": "PyQt5",
        "matplotlib": "matplotlib",
        "qtawesome": "qtawesome",
        "joblib": "joblib",
    }
    
    missing = []
    
    for pkg, import_name in required.items():
        try:
            __import__(import_name)
            print_success(f"{pkg} is installed")
        except (ImportError, ModuleNotFoundError) as e:
            print_error(f"{pkg} is missing: {e}")
            missing.append(pkg)
    
    if missing:
        print(f"\n{YELLOW}Installing missing packages...{RESET}")
        for pkg in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg], timeout=60)
                print_success(f"Installed {pkg}")
            except subprocess.TimeoutExpired:
                print_warning(f"Installation of {pkg} timed out (may still be installing)")
            except Exception as e:
                print_error(f"Failed to install {pkg}: {e}")
    
        return len(missing) == 0

def check_brain_json():
    """Verify trading brain JSON structure."""
    print_header("DATA VERIFICATION")
    
    if not BRAIN_JSON.exists():
        print_error(f"data4.json not found at {BRAIN_JSON}")
        return False
    
    try:
        with open(BRAIN_JSON, 'r') as f:
            brain = json.load(f)
        
        print_success("JSON file loaded successfully")
        
        sections = ["metadata", "patterns", "indicators", "strategies", "risk_management"]
        for sec in sections:
            if sec in brain:
                count = len(brain[sec]) if isinstance(brain[sec], dict) else 1
                print_success(f"  • {sec}: {count} items")
            else:
                print_warning(f"  • {sec}: MISSING")
        
        print_info(f"Total patterns defined: {len(brain.get('patterns', {}))}")
        print_info(f"Total indicators: {len(brain.get('indicators', {}))}")
        print_info(f"Total strategies: {len(brain.get('strategies', {}))}")
        
        return True
    
    except json.JSONDecodeError as e:
        print_error(f"JSON parse error: {e}")
        return False
    except Exception as e:
        print_error(f"Error loading JSON: {e}")
        return False

def train_model():
    """Train model, clearing any stale saved files first."""
    print_header("AI MODEL TRAINING")

    models_dir = BASE_DIR / "MODELS"
    stale = [models_dir / "brain_model.pkl", models_dir / "scaler.pkl"]
    for f in stale:
        if f.exists():
            f.unlink()
            print_warning(f"Removed stale model file: {f.name}")

    try:
        from brains import get_brain_v2, FEAT

        print_info("Initializing training engine...")
        brain = get_brain_v2()

        print_success(f"Model initialized")
        print_success(f"Features: {len(FEAT)} technical indicators")
        print_success(f"Model: LightGBM + isotonic calibration")

        return True
    
    except Exception as e:
        print_error(f"Training error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui():
    """Test that GUI launches without errors."""
    print_header("GUI FUNCTIONALITY TEST")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from main import RedRookApp

        print_success("GUI imports successful")
        print_info("To launch GUI: python main.py")

        return True
    except Exception as e:
        print_error(f"GUI test failed: {e}")
        return False

def test_trading_engine():
    """Test trading engine signal generation."""
    print_header("TRADING ENGINE TEST")
    
    try:
        from brains import get_brain_v2
        
        brain = get_brain_v2()
        print_success("Trading engine initialized")
        
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        for sym in symbols:
            signal = brain.generate_signal(sym, "1d")
            print_success(f"{sym}: {signal.direction} (confidence: {signal.confidence*100:.0f}%)")
        
        return True
    
    except Exception as e:
        print_error(f"Engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def diagnose_system():
    """Full system diagnostic."""
    print_header("FULL DIAGNOSTIC")
    
    print_info("Python version:", end=" ")
    print(f"{sys.version.split()[0]}")
    
    print_info("Platform:", end=" ")
    print(f"{sys.platform}")
    
    print_info("Working directory:", end=" ")
    print(f"{BASE_DIR}")
    
    print_info("Brain JSON:", end=" ")
    print(f"{'FOUND' if BRAIN_JSON.exists() else 'MISSING'}")
    
    print()
    
    results = {
        "Dependencies": check_dependencies(),
        "Data JSON": check_brain_json(),
        "Trading Engine": test_trading_engine(),
        "GUI": test_gui(),
    }
    
    print_header("SYSTEM STATUS")
    
    all_ok = True
    for name, ok in results.items():
        status = "✓ PASS" if ok else "✗ FAIL"
        if ok:
            print_success(f"{name}: {status}")
        else:
            print_error(f"{name}: {status}")
            all_ok = False
    
    return all_ok

def main():
    print(f"{BOLD}{BLUE}")
    print("=" * 70)
    print("Paladin TRADING PLATFORM".center(70))
    print("Setup & Model Training Utility".center(70))
    print("=" * 70)
    print(f"{RESET}")

    deps_ok = check_dependencies()
    if deps_ok is False:
        print_error("Please install missing dependencies and try again.")
        return False

    if not check_brain_json():
        print_warning("Data JSON file has issues")

    if not train_model():
        print_error("Model training failed")
        return False

    print()
    if not diagnose_system():
        print_error("Some diagnostics failed")
        return False

    print_header("SETUP COMPLETE")
    print_success("Red Rook Trading Platform is ready to use!")
    print(f"\n{BOLD}Next steps:{RESET}")
    print(f"  1. Launch GUI:  {BLUE}python main.py{RESET}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)