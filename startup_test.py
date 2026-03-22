import sys
try:
    print("Testing imports...")
    import app.main
    print("Import OK")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
