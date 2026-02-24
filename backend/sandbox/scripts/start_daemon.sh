#!/bin/bash

# Start Docker Daemon if available and privileged
if [ -x "$(command -v dockerd)" ]; then
    dockerd > /var/log/dockerd.log 2>&1 &
fi

# Start other background services here (e.g., logging agent)

# Keep container alive or start shell
exec "$@"
