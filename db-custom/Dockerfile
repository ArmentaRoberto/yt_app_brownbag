FROM postgres:13

# Install vim for debugging (optional)
RUN apt-get update && apt-get install -y vim && rm -rf /var/lib/apt/lists/*

# Copy the init script into the correct directory
COPY init-db.sh /docker-entrypoint-initdb.d/init-db.sh

# Ensure the script is executable
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh
