import os

environment = os.getenv('APP_ENVIRONMENT', 'local')

if environment == 'production':
    from .production import *
else:
    from .local import *