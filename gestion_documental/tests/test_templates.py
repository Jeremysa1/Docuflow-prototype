import os
import django
from django.template.loader import get_template
from django.template import TemplateSyntaxError

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import glob
templates = glob.glob('apps/**/templates/**/*.html', recursive=True)

errors = []
for template_path in templates:
    # Get the relative path that Django loader expects, e.g., 'documentos/aprobar_documentos.html'
    parts = template_path.split(os.sep)
    try:
        idx = parts.index('templates')
        rel_path = "/".join(parts[idx+1:])
        try:
            get_template(rel_path)
        except Exception as e:
            errors.append(f"{rel_path}: {e}")
    except ValueError:
        pass

if not errors:
    print("All templates parsed successfully.")
else:
    for err in errors:
        print(err)
