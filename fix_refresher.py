with open('/Users/mariomarcheggiani/RF-DIAG/wifi_tool.py', 'r') as f:
    content = f.read()

content = content.replace(
    "def background_refresher():\n    while True:\n        try:\n            refresh_cache()",
    "def background_refresher():\n    time.sleep(15)  # Wait for prober to trigger initial scan\n    while True:\n        try:\n            refresh_cache()"
)

with open('/Users/mariomarcheggiani/RF-DIAG/wifi_tool.py', 'w') as f:
    f.write(content)

print("Done!")
