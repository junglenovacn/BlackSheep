import sys
print("Python executable:", sys.executable)
print("Python path:", sys.path)

try:
    import guardpost
    print("guardpost imported successfully")
except Exception as e:
    print("guardpost import error:", e)

try:
    import essentials
    print("essentials imported successfully")
except Exception as e:
    print("essentials import error:", e)
