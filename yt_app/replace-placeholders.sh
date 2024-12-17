#!/bin/bash

TEMPLATE_PATH="/app/templates/dashboard.html"
OUTPUT_PATH="/app/templates/dashboard_rendered.html"
export SERVICE ENVIRO API_KEY CLIENTTOKEN APPID
if [ ! -f "$TEMPLATE_PATH" ]; then
    echo "Error: $TEMPLATE_PATH not found!"
    ls -l /app/templates
    exit 1
fi
envsubst '${SERVICE} ${ENVIRO} ${API_KEY} ${CLIENTTOKEN} ${APPID}' < "$TEMPLATE_PATH" > "$OUTPUT_PATH"
exec "$@"
