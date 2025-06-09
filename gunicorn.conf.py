import os

# Increase worker timeout for long running operations
# Default is 30 seconds which is too short for large downloads/conversions

timeout = int(os.getenv("GUNICORN_TIMEOUT", "300"))
# Allow some time for graceful shutdowns
graceful_timeout = 30

# Bind to the port expected by Azure App Service
bind = "0.0.0.0:80"
