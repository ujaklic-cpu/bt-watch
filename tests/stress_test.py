import json
import random
import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from map_server import app


def make_hosts(n):
    """Return mapping host_id -> (lat, lon) in a small grid."""
    base_lat, base_lon = 46.050, 14.500
    step = 0.001
    return {
        f"host-{i+1}": (base_lat + i * step, base_lon + (i % 3) * step)
        for i in range(n)
    }


def simulate(client, hosts, devices, events_per_host=50):
    for host, (lat, lon) in hosts.items():
        for d in devices:
            for _ in range(events_per_host):
                rssi = random.randint(-85, -35)
                payload = {
                    "host": host,
                    "address": d,
                    "name": f"dev-{d[-4:]}",
                    "rssi": rssi,
                    "ts": time.time(),
                }
                resp = client.post("/ingest", json=payload)
                assert resp.status_code == 200


def check_snapshot(client, hosts, devices):
    resp = client.get("/snapshot")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["hosts"]) == len(hosts)
    seen = {d["address"]: d for d in data["devices"]}
    assert set(seen.keys()) == set(devices)
    for d in seen.values():
        est = d["estimate"]
        assert est["lat"] is not None and est["lon"] is not None


def run_scenario(host_count):
    hosts = make_hosts(host_count)
    devices = [f"AA:BB:CC:DD:EE:{i:02X}" for i in range(3)]
    client = app.test_client()
    # Seed host coords into map_server globals via env-style injection
    # Since HOST_COORDS is read at import time, we rebuild the mapping here.
    from map_server import HOST_COORDS

    HOST_COORDS.clear()
    HOST_COORDS.update(hosts)

    simulate(client, hosts, devices)
    check_snapshot(client, hosts, devices)


def main():
    random.seed(42)
    start = time.time()
    for n in range(1, 11):
        run_scenario(n)
    elapsed = time.time() - start
    print(f"Stress test passed for 1..10 hosts in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
