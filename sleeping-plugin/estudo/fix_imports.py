import sys
print("Python executable:", sys.executable)
print("\nPython version:", sys.version)
print("\nPython path:")
for path in sys.path:
    print(f"  {path}")
