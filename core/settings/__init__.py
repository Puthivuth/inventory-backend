"""
Django settings module.
Load appropriate settings based on DJANGO_SETTINGS_MODULE environment variable.
"""

import os

# Determine which settings to use
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'core.settings.development')

if 'production' in settings_module:
    from .production import *
else:
    from .development import *
