FROM python:3.12-slim

# Install Bluetooth stack userspace and dependencies for bleak (BlueZ + glib).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      bluez \
      dbus \
      libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bt_watch.py .

# Default port; can override with -p/ -e FLASK_RUN_PORT.
EXPOSE 5000

ENV PYTHONUNBUFFERED=1 \
    TARGET_MACS=""

CMD ["python", "bt_watch.py"]
