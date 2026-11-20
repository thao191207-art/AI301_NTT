import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Let's inspect the build_complete_app.py file to do targeted edits or rewrite
builder_path = os.path.join(BASE_DIR, 'scripts', 'build_complete_app.py')
with open(builder_path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add JSZip reading
if 'jszip_js' not in code:
    code = code.replace(
        "with open(os.path.join(BASE_DIR, 'vendor', 'lucide.min.js'), 'r', encoding='utf-8') as f:\n    lucide_js = f.read()",
        "with open(os.path.join(BASE_DIR, 'vendor', 'lucide.min.js'), 'r', encoding='utf-8') as f:\n    lucide_js = f.read()\n\nwith open(os.path.join(BASE_DIR, 'vendor', 'jszip.min.js'), 'r', encoding='utf-8') as f:\n    jszip_js = f.read()"
    )
    print("Added jszip_js reading.")

# 2. Add JSZip script to complete_html head
if '<script>\n{jszip_js}\n  </script>' not in code:
    code = code.replace(
        "  <script>\n{lucide_js}\n  </script>",
        "  <script>\n{lucide_js}\n  </script>\n  <script>\n{jszip_js}\n  </script>"
    )
    print("Added jszip_js script tag in HTML head.")

with open(builder_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated build_complete_app.py successfully.")
