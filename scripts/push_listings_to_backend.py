import json
import os
import sys
import urllib.request


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/push_listings_to_backend.py <payload.json>")
        return 1

    payload_path = sys.argv[1]
    ingest_url = os.getenv("MAIN_BACKEND_INGEST_URL", "http://localhost:8080/internal/ingestion/listings")
    service_token = os.getenv("APP_INGESTION_SERVICE_TOKEN", "dealradar-ingestion-token")

    with open(payload_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    request = urllib.request.Request(
        ingest_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Service-Token": service_token,
        },
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        print(response.read().decode("utf-8"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
