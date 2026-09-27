# API Reference

Base URL: `http://localhost:8080` (Docker and local default). Interactive docs: http://localhost:8080/docs.

There is no authentication and no rate limiting.

Errors use FastAPI's standard shape, `{"detail": "..."}`. Request body validation failures return `422`.

---

## Health

### `GET /health`

```json
{ "status": "healthy", "database": "connected" }
```

`status` is `"degraded"` and `database` is `"disconnected"` if MongoDB doesn't respond.

### `GET /`

Returns the API name, version, and a link to `/docs`.

---

## URLs

### `POST /api/urls/add` → 201

```json
{
  "urls": ["https://www.walmart.com/ip/21130579", "https://www.target.com/p/-/A-88920975"],
  "group_name": "Electronics"
}
```

- 1 to 500 URLs per request. Surrounding whitespace is trimmed.
- Each URL must start with `http://` or `https://`.
- URLs pointing at private, loopback, link-local, or reserved addresses (`localhost`, `10.x`, `192.168.x`, `*.internal` and similar) are rejected with 422, to prevent the scraper being aimed at internal services.
- URLs that already exist are skipped.

```json
{ "message": "Successfully added 2 URLs", "added_count": 2, "duplicate_count": 0 }
```

### `GET /api/urls`

Query: `group_name`, `limit` (default 100), `skip` (default 0).

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "url": "https://www.walmart.com/ip/21130579",
    "created_at": "2026-05-05T18:06:51Z",
    "group_name": "Electronics"
  }
]
```

### `GET /api/urls/{url_id}`

One URL in the same shape. 400 for a malformed ID, 404 if not found.

### `DELETE /api/urls/{url_id}`

Deletes the URL and all of its scan results.

```json
{ "message": "URL deleted successfully" }
```

### `DELETE /api/urls`

Deletes every URL and every scan result.

```json
{ "message": "All URLs and scan results deleted successfully", "urls_deleted": 10, "scans_deleted": 25 }
```

---

## Scans

### `POST /api/scan/run`

Starts a scan job. The body is optional: send `{}` (or `{"url_ids": null}`) to scan every URL, or list specific IDs.

```json
{ "url_ids": ["507f1f77bcf86cd799439011"] }
```

Returns immediately. The worker does the scraping.

```json
{
  "message": "Scan queued for 1 URLs",
  "job_id": "3f7c9a2e-5b1d-4c8e-9f0a-2d6b7e1c4a53",
  "url_count": 1,
  "status": "queued"
}
```

400 if an ID is malformed or no URLs match. Nothing stops you from starting a second scan while one is running.

### `GET /api/scan/{job_id}/status`

Progress for one job. Poll this until `status` is `done`, `failed`, or `cancelled`.

```json
{
  "job_id": "3f7c9a2e-5b1d-4c8e-9f0a-2d6b7e1c4a53",
  "status": "running",
  "created_at": "2026-05-05T19:33:28Z",
  "started_at": "2026-05-05T19:33:29Z",
  "finished_at": null,
  "total_urls": 10,
  "completed": 4,
  "success": 3,
  "error": 1,
  "available_count": 2,
  "unavailable_count": 1,
  "availability_summary": "some_unavailable",
  "rate_urls_per_sec": 0.052,
  "eta_seconds": 115,
  "last_update_at": "2026-05-05T19:34:45Z"
}
```

| `status` | Meaning |
|----------|---------|
| `queued` | Waiting for a worker |
| `running` | URLs are being scraped |
| `done` | Every URL has a result (some may be errors) |
| `failed` | No URLs were found when the worker started |
| `cancelled` | Workers skip remaining URLs. No endpoint sets this yet; change it directly in MongoDB |

`availability_summary` only counts successful scrapes: `all_available`, `some_unavailable`, `none_available`, or `unknown` (nothing succeeded yet).

### `GET /api/scan/status`

```json
{ "scanning": true }
```

True if any job is `queued` or `running`.

### `GET /api/scan/results`

Every stored result, newest first. Query: `url`, `status_filter` (`available` / `unavailable` / `error`), `limit` (default 200), `skip`.

```json
[
  {
    "id": "663fd3a1c2b4e5f6a7b8c9d0",
    "url": "https://www.walmart.com/ip/21130579",
    "url_id": "507f1f77bcf86cd799439011",
    "job_id": "3f7c9a2e-5b1d-4c8e-9f0a-2d6b7e1c4a53",
    "scanned_at": "2026-05-05T19:34:15Z",
    "status": "available",
    "add_to_cart": true,
    "buy_now": false,
    "error_message": null,
    "blocked_reason": null,
    "response_time": 18.42,
    "scrape_method": "playwright",
    "html_primary_source": "playwright",
    "variants": { "Small": "available", "Large": "unavailable" },
    "variants_checked": true,
    "unavailability_override": false
  }
]
```

- `status: "error"` covers fetch failures, timeouts, and block pages. Block pages have `error_message` like `"blocked:captcha"` or `"blocked:robot or human"`.
- `scrape_method` is the fetch method behind the final result (`playwright`, `scrapingbee`, `static`, or `error`). `html_primary_source` is the method that returned HTML first. They differ when a result was re-checked, e.g. Wayfair results from ScrapingBee are confirmed with Playwright.
- `blocked_reason` is part of the schema but the worker doesn't store it yet. Use `error_message`.

### `GET /api/scan/results/latest`

The most recent result for each URL, same shape. Query: `limit` (default 500).

### `DELETE /api/scan/results`

Deletes all scan results but keeps the URLs.

```json
{ "message": "All scan results cleared", "deleted_count": 25 }
```

---

## Logs and statistics

### `GET /api/logs`

Application events. Query: `event_type`, `level` (`INFO` / `WARNING` / `ERROR`), `hours` (default 24), `limit` (default 100), `skip`.

```json
[
  {
    "id": "663fd3a1c2b4e5f6a7b8c9d1",
    "event_type": "urls_added",
    "details": { "count": 2, "group": "Electronics" },
    "timestamp": "2026-05-05T18:00:00Z",
    "level": "INFO"
  }
]
```

Logs older than 30 days are deleted automatically by a TTL index.

### `DELETE /api/logs`

Query: `older_than_days` (default 30).

```json
{ "message": "Cleared logs older than 30 days", "deleted_count": 150 }
```

### `GET /api/logs/stats`

```json
{
  "total_urls": 50,
  "total_scans": 200,
  "available_count": 38,
  "unavailable_count": 7,
  "error_count": 5
}
```

`total_scans` counts every stored result. The three status counts use only the latest result per URL.

---

## Example (Python)

```python
import time
import requests

API = "http://localhost:8080"

requests.post(f"{API}/api/urls/add", json={"urls": ["https://www.wayfair.com/..."]})

job = requests.post(f"{API}/api/scan/run", json={}).json()
while True:
    s = requests.get(f"{API}/api/scan/{job['job_id']}/status").json()
    print(f"{s['completed']}/{s['total_urls']}")
    if s["status"] in ("done", "failed", "cancelled"):
        break
    time.sleep(5)

for r in requests.get(f"{API}/api/scan/results/latest").json():
    print(r["status"], r["url"], r.get("error_message") or "")
```
