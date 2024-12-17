#!/bin/bash

set -e

# Connect to the default 'postgres' database to perform administrative tasks
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    DROP DATABASE IF EXISTS youtube_db;
    CREATE DATABASE youtube_db;
EOSQL