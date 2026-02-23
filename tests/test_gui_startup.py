#!/usr/bin/env python3
"""
Quick Start Script for JARVIS GUI
==================================
Run this to check if everything is installed and working correctly.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_requirements():
    """Check if all required packages are installed"""
    print("🔍 Checking requirements...\n")
    
    requirements = {
        'PyQt5': 'PyQt5 (GUI Framework)',
        'groq': 'Groq (LLM and Voice)',
        'sounddevice': 'sounddevice (Microphone Input)',
        'scipy': 'SciPy (Audio Processing)',
        'numpy': 'NumPy (Numerical Computing)',
    }
    
    missing = []
    
    for package, description in requirements.items():
        try:
            __import__(package)
            print(f"✅ {description}: OK")
        except ImportError:
            print(f"❌ {description}: MISSING")
            missing.append(package)
    
    print()
    
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        print("\n💡 Install with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("✅ All requirements met!")
    return True


def check_environment():
    """Check environment variables"""
    print("\n🔧 Checking environment...\n")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        print(f"✅ GROQ_API_KEY: Set ({len(api_key)} chars)")
    else:
        print(f"⚠️  GROQ_API_KEY: Not set")
        print("   Voice features may not work")
    
    return bool(api_key)


def test_imports():
    """Test if all modules can be imported"""
    print("\n📦 Testing imports...\n")
    
    modules = [
        ('agent.master_agent', 'Master Agent'),
        ('ui.app', 'GUI Application'),
        ('ui.chat_card', 'Chat Card'),
        ('widget.widget', 'Floating Widget'),
        ('voice.voice_listener', 'Voice Listener'),
    ]
    
    failed = []
    
    for module_path, description in modules:
        try:
            parts = module_path.split('.')
            module = __import__(module_path)
            for part in parts[1:]:
                module = getattr(module, part)
            print(f"✅ {description}: OK")
        except Exception as e:
            print(f"❌ {description}: {str(e)}")
            failed.append(description)
    
    return len(failed) == 0


def test_gui_startup():
    """Quick test of GUI startup"""
    print("\n🎨 Testing GUI startup...\n")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.app import JarvisGUIApp
        
        print("✅ GUI modules imported successfully")
        print("✅ GUI is ready to launch")
        return True
    except Exception as e:
        print(f"❌ GUI startup test failed: {str(e)}")
        return False


def main():
    """Run all checks"""
    print("="*60)
    print("🤖 JARVIS GUI - Quick Start Validation")
    print("="*60)
    print()
    
    checks = [
        ("Requirements", check_requirements),
        ("Environment", check_environment),
        ("Module Imports", test_imports),
        ("GUI Startup", test_gui_startup),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Validation Summary")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 Everything looks good! You can now run:")
        print("\n   python run_jarvis.py           # GUI mode")
        print("   python run_jarvis.py --gui-voice # GUI + Voice")
        print("   python run_jarvis.py --cli       # Terminal mode")
        print("   python run_jarvis.py --voice     # Terminal + Voice")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
