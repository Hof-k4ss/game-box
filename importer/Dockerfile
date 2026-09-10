FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends p7zip-full \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY import_roms.py /app/import_roms.py
ENTRYPOINT ["python", "/app/import_roms.py"]
