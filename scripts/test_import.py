#!/usr/bin/env python
"""Quick test to verify app imports correctly."""

import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

try:
    import app.main
    print("✅ App imports successfully!")
    print("✅ Dashboard is ready to run")
    sys.exit(0)
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
