#!/usr/bin/env python3
"""Dashboard integration validation script."""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_imports():
    """Validate all imports work correctly."""
    print("✓ Validating imports...")
    
    try:
        from app.dashboard.routes import router as dashboard_router
        print("  ✓ Dashboard router imported")
    except ImportError as e:
        print(f"  ✗ Failed to import dashboard router: {e}")
        return False
    
    try:
        from starlette.middleware.sessions import SessionMiddleware
        print("  ✓ SessionMiddleware imported")
    except ImportError as e:
        print(f"  ✗ Failed to import SessionMiddleware: {e}")
        return False
    
    try:
        from fastapi.staticfiles import StaticFiles
        print("  ✓ StaticFiles imported")
    except ImportError as e:
        print(f"  ✗ Failed to import StaticFiles: {e}")
        return False
    
    try:
        from fastapi import FastAPI
        print("  ✓ FastAPI imported")
    except ImportError as e:
        print(f"  ✗ Failed to import FastAPI: {e}")
        return False
    
    return True


def validate_files():
    """Validate all required files exist."""
    print("\n✓ Validating files...")
    
    required_files = [
        "app/dashboard/__init__.py",
        "app/dashboard/routes.py",
        "templates/dashboard.html",
        "templates/dashboard_login.html",
        "templates/dashboard_traffic.html",
        "templates/dashboard_security.html",
        "templates/dashboard_settings.html",
        "static/dashboard.js",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (missing)")
            all_exist = False
    
    return all_exist


def validate_requirements():
    """Validate requirements.txt has necessary packages."""
    print("\n✓ Validating requirements...")
    
    req_file = project_root / "requirements.txt"
    if not req_file.exists():
        print("  ✗ requirements.txt not found")
        return False
    
    content = req_file.read_text()
    required_packages = ["requests", "python-multipart", "Jinja2"]
    
    all_found = True
    for pkg in required_packages:
        if pkg in content:
            print(f"  ✓ {pkg}")
        else:
            print(f"  ✗ {pkg} (missing)")
            all_found = False
    
    return all_found


def validate_main_py():
    """Validate main.py has necessary integrations."""
    print("\n✓ Validating main.py integrations...")
    
    main_file = project_root / "app" / "main.py"
    if not main_file.exists():
        print("  ✗ app/main.py not found")
        return False
    
    content = main_file.read_text()
    
    integrations = [
        ("SessionMiddleware import", "from starlette.middleware.sessions import SessionMiddleware"),
        ("dashboard router import", "from .dashboard.routes import router as dashboard_router"),
        ("StaticFiles import", "from fastapi.staticfiles import StaticFiles"),
        ("SessionMiddleware added", "app.add_middleware"),
        ("router included", "app.include_router(dashboard_router)"),
        ("static files mounted", "app.mount"),
    ]
    
    all_found = True
    for name, check in integrations:
        if check in content:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")
            all_found = False
    
    return all_found


def main():
    """Run all validations."""
    print("=" * 60)
    print("Dashboard Integration Validation")
    print("=" * 60)
    
    results = []
    results.append(("Imports", validate_imports()))
    results.append(("Files", validate_files()))
    results.append(("Requirements", validate_requirements()))
    results.append(("main.py", validate_main_py()))
    
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All validations passed!")
        print("\nNext steps:")
        print("1. Update requirements: pip install -r requirements.txt")
        print("2. Start the application: python -m uvicorn app.main:app --reload")
        print("3. Access dashboard: http://localhost:8000/dashboard/login")
        print("4. Login with: admin / changeme")
        return 0
    else:
        print("\n✗ Some validations failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
