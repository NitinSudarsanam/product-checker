# API Reference - Ubique Product Checker

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required (POC version).

---

## Endpoints

### Health Check

#### `GET /health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## URL Management

### Add URLs

#### `POST /api/urls/add`

Add single or multiple URLs to the system.

**Request Body:**
```json
{
  "urls": [
    "https://www.amazon.com/product1",
    "https://www.walmart.com/product2"
  ],
  "group_name": "Electronics"
}
```

**Response:**
```json
{
  "message": "Successfully added 2 URLs",
  "added_count": 2,
  "duplicate_count": 0
}
```

---

### Get All URLs

#### `GET /api/urls`

Retrieve all stored URLs with optional filtering.

**Query Parameters:**
- `group_name` (optional): Filter by group
- `limit` (optional, default: 100): Max results
- `skip` (optional, default: 0): Pagination offset

**Example:**
```
GET /api/urls?group_name=Electronics&limit=50
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "url": "https://www.amazon.com/product",
    "created_at": "2024-12-12T10:30:00Z",
    "group_name": "Electronics"
  }
]
```

---

### Get Single URL

#### `GET /api/urls/{url_id}`

Get a specific URL by ID.

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "url": "https://www.amazon.com/product",
  "created_at": "2024-12-12T10:30:00Z",
  "group_name": "Electronics"
}
```

---

### Delete URL

#### `DELETE /api/urls/{url_id}`

Delete a specific URL and its scan results.

**Response:**
```json
{
  "message": "URL deleted successfully"
}
```

---

### Delete All URLs

#### `DELETE /api/urls`

Delete all URLs and scan results.

**Response:**
```json
{
  "message": "All URLs and scan results deleted successfully",
  "urls_deleted": 10,
  "scans_deleted": 25
}
```

---

## Scanning

### Run Scan

#### `POST /api/scan/run`

Trigger a manual scan for all URLs or specific URL IDs.

**Request Body:**
```json
{
  "url_ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]
}
```

Or leave empty to scan all:
```json
{}
```

**Response:**
```json
{
  "message": "Scan started for 10 URLs",
  "url_count": 10,
  "status": "running"
}
```

---

### Get Scan Results

#### `GET /api/scan/results`

Retrieve scan results with optional filtering.

**Query Parameters:**
- `url` (optional): Filter by specific URL
- `status_filter` (optional): Filter by status (available/unavailable/error)
- `limit` (optional, default: 100): Max results
- `skip` (optional, default: 0): Pagination offset

**Example:**
```
GET /api/scan/results?status_filter=available&limit=20
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439013",
    "url": "https://www.amazon.com/product",
    "scanned_at": "2024-12-12T10:35:00Z",
    "add_to_cart": true,
    "buy_now": true,
    "status": "available",
    "error_message": null,
    "response_time": 2.5
  }
]
```

---

### Get Latest Results

#### `GET /api/scan/results/latest`

Get the most recent scan result for each URL.

**Query Parameters:**
- `limit` (optional, default: 50): Max results

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439013",
    "url": "https://www.amazon.com/product",
    "scanned_at": "2024-12-12T10:35:00Z",
    "add_to_cart": true,
    "buy_now": false,
    "status": "available",
    "response_time": 2.5
  }
]
```

---

### Clear Scan Results

#### `DELETE /api/scan/results`

Clear all scan results (keeps URLs).

**Response:**
```json
{
  "message": "All scan results cleared",
  "deleted_count": 25
}
```

---

## Logs and Statistics

### Get Logs

#### `GET /api/logs`

Retrieve system logs with filtering.

**Query Parameters:**
- `event_type` (optional): Filter by event type
- `level` (optional): Filter by log level (INFO/WARNING/ERROR)
- `hours` (optional, default: 24): Time window in hours
- `limit` (optional, default: 100): Max results
- `skip` (optional, default: 0): Pagination offset

**Example:**
```
GET /api/logs?level=ERROR&hours=48
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439014",
    "event_type": "scan_error",
    "details": {
      "url": "https://example.com",
      "error": "Timeout"
    },
    "timestamp": "2024-12-12T10:30:00Z",
    "level": "ERROR"
  }
]
```

---

### Clear Logs

#### `DELETE /api/logs`

Clear old logs.

**Query Parameters:**
- `older_than_days` (optional, default: 30): Delete logs older than X days

**Response:**
```json
{
  "message": "Cleared logs older than 30 days",
  "deleted_count": 150
}
```

---

### Get Statistics

#### `GET /api/logs/stats`

Get system-wide statistics.

**Response:**
```json
{
  "total_urls": 50,
  "total_scans": 200,
  "available_count": 150,
  "unavailable_count": 30,
  "error_count": 20
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid URL ID format"
}
```

### 404 Not Found
```json
{
  "detail": "URL not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to fetch URLs: connection error"
}
```

---

## Rate Limiting

**Current:** No rate limiting (POC version)

**Future:** 
- 100 requests per minute per IP
- 1000 scans per day

---

## Webhooks (Future Feature)

Subscribe to events:
- `scan.completed` - When a scan finishes
- `url.added` - When URLs are added
- `button.detected` - When availability changes

---

## Code Examples

### Python

```python
import requests

API_URL = "http://localhost:8000"

# Add URLs
response = requests.post(
    f"{API_URL}/api/urls/add",
    json={
        "urls": ["https://www.amazon.com/product"],
        "group_name": "Test"
    }
)
print(response.json())

# Run scan
response = requests.post(f"{API_URL}/api/scan/run", json={})
print(response.json())

# Get results
response = requests.get(f"{API_URL}/api/scan/results/latest")
results = response.json()
for result in results:
    print(f"{result['url']}: {result['status']}")
```

### JavaScript

```javascript
const API_URL = 'http://localhost:8000';

// Add URLs
async function addURLs() {
  const response = await fetch(`${API_URL}/api/urls/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      urls: ['https://www.amazon.com/product'],
      group_name: 'Test'
    })
  });
  const data = await response.json();
  console.log(data);
}

// Run scan
async function runScan() {
  const response = await fetch(`${API_URL}/api/scan/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  const data = await response.json();
  console.log(data);
}

// Get results
async function getResults() {
  const response = await fetch(`${API_URL}/api/scan/results/latest`);
  const results = await response.json();
  results.forEach(result => {
    console.log(`${result.url}: ${result.status}`);
  });
}
```

### cURL

```bash
# Add URLs
curl -X POST http://localhost:8000/api/urls/add \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://www.amazon.com/product"],"group_name":"Test"}'

# Run scan
curl -X POST http://localhost:8000/api/scan/run \
  -H "Content-Type: application/json" \
  -d '{}'

# Get results
curl http://localhost:8000/api/scan/results/latest
```

---

## Interactive API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation where you can test all endpoints directly.
