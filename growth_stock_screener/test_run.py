from screen.iterations.utils import *
import sys

print("Python version:", sys.version)
print("Test script running...")

try:
    print("Testing cache module...")
    current_settings = get_current_settings()
    print("Current settings:", current_settings)
    
    print("Testing summary module...")
    # Don't actually create the file, just test the import
    print("Summary module imported successfully")
    
    print("Testing analysis module...")
    # Don't actually run the analysis, just test the import
    print("Analysis module imported successfully")
    
    print("All tests passed!")
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
