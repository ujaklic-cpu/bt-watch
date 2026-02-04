# Twingate connector for bt-watch

Run this connector on the hub machine to let probes (Android/ESP32/Chromebook) reach the aggregator without exposing any inbound ports. Traffic goes through Twingate’s zero-trust network.

## Prereqs
- Twingate tenant and an active Remote Network.
- Create a Connector in the Twingate Admin console; download or copy the access/refresh tokens and network name.
- Docker installed on the hub.

## Setup
```bash
cd twingate
cp .env.example .env
# edit .env with your values:
#  TWINGATE_NETWORK=your-network
#  TWINGATE_ACCESS_TOKEN=...
#  TWINGATE_REFRESH_TOKEN=...
docker compose -f docker-compose.twingate.yml up -d
```

The connector runs in host networking so it can reach `http://127.0.0.1:8000` (map_server) and any other local services.

## Using with bt-watch
- On probes, set `AGGREGATOR_URL` to the Twingate-provided DNS name or IP that resolves through the connector (e.g., `http://hub.internal:8000`).
- Keep map_server listening on 0.0.0.0:8000 (default). No public ports need to be opened.

## Notes
- Tokens are sensitive; keep `.env` out of version control.
- Restart policy is `unless-stopped`; the connector will reconnect automatically.
