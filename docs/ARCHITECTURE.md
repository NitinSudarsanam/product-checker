# 🎨 System Architecture & Diagrams

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│                    (http://localhost:3000)                      │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ HTTP/REST
             ▼
┌────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js + React)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  URL Input   │  │   Results    │  │  Statistics  │        │
│  │  Component   │  │    Table     │  │   Dashboard  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              API Client (axios)                          │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────┬───────────────────────────────────────────────────┘
             │
             │ HTTP/REST API Calls
             ▼
┌────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  URLs API    │  │   Scan API   │  │   Logs API   │        │
│  │  /api/urls   │  │  /api/scan   │  │  /api/logs   │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                │
│                            │                                    │
│  ┌─────────────────────────▼──────────────────────────────┐   │
│  │              Business Logic Layer                       │   │
│  │  - Input Validation                                     │   │
│  │  - Error Handling                                       │   │
│  │  - Logging                                              │   │
│  └─────────────────────────┬──────────────────────────────┘   │
└────────────────────────────┼───────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   SCRAPER      │  │    MONGODB     │  │    LOGGER      │
│   ENGINE       │  │    DATABASE    │  │    SYSTEM      │
│                │  │                │  │                │
│ • BeautifulSoup│  │ • urls         │  │ • File logs    │
│ • Playwright   │  │ • scan_results │  │ • DB logs      │
│ • Detector     │  │ • logs         │  │ • Console      │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## 🔄 Data Flow Diagrams

### Adding URLs Flow

```
┌─────────┐
│  User   │
│ enters  │
│  URLs   │
└────┬────┘
     │
     ▼
┌──────────────────┐
│  URLInput.tsx    │
│  - Validates     │
│  - Formats       │
└────┬─────────────┘
     │
     │ api.addURLs()
     ▼
┌──────────────────┐
│  api.ts          │
│  POST request    │
└────┬─────────────┘
     │
     │ HTTP POST /api/urls/add
     ▼
┌──────────────────┐
│  urls.py         │
│  - Sanitize      │
│  - Check dupes   │
└────┬─────────────┘
     │
     │ db.urls.insert_many()
     ▼
┌──────────────────┐
│  MongoDB         │
│  urls collection │
└────┬─────────────┘
     │
     │ Response
     ▼
┌──────────────────┐
│  Frontend        │
│  - Update state  │
│  - Show success  │
│  - Refresh list  │
└──────────────────┘
```

### Scanning Flow

```
┌─────────┐
│  User   │
│ clicks  │
│  "Scan" │
└────┬────┘
     │
     ▼
┌──────────────────┐
│  index.tsx       │
│  runScan()       │
└────┬─────────────┘
     │
     │ api.runScan()
     ▼
┌──────────────────┐
│  api.ts          │
│  POST request    │
└────┬─────────────┘
     │
     │ HTTP POST /api/scan/run
     ▼
┌──────────────────┐
│  scan.py         │
│  - Get URLs      │
│  - Start task    │
└────┬─────────────┘
     │
     │ For each URL
     ▼
┌──────────────────┐
│  scraper.py      │
│  - Fetch HTML    │
│  - Parse DOM     │
└────┬─────────────┘
     │
     │ HTML content
     ▼
┌──────────────────┐
│  detector.py     │
│  - Match rules   │
│  - Find buttons  │
└────┬─────────────┘
     │
     │ Detection result
     ▼
┌──────────────────┐
│  scan.py         │
│  - Format result │
│  - Save to DB    │
└────┬─────────────┘
     │
     │ db.scan_results.insert()
     ▼
┌──────────────────┐
│  MongoDB         │
│  scan_results    │
└────┬─────────────┘
     │
     │ Frontend polls
     ▼
┌──────────────────┐
│  ResultsTable    │
│  - Display data  │
│  - Show status   │
└──────────────────┘
```

---

## 🔌 Component Interactions

### Frontend Components

```
index.tsx (Main Page)
│
├── URLInput.tsx
│   ├── Input fields
│   ├── Validation logic
│   └── Submit handler → api.addURLs()
│
├── URLList.tsx
│   ├── Fetch URLs → api.getURLs()
│   ├── Display table
│   └── Delete handler → api.deleteURL()
│
├── ResultsTable.tsx
│   ├── Fetch results → api.getLatestResults()
│   ├── Display results
│   └── Status indicators
│
└── StatsCard.tsx
    ├── Fetch stats → api.getStats()
    └── Display metrics
```

### Backend Endpoints

```
main.py (FastAPI App)
│
├── /api/urls/* (urls.py)
│   ├── POST /add → Add URLs
│   ├── GET / → List URLs
│   ├── GET /{id} → Get URL
│   ├── DELETE /{id} → Delete URL
│   └── DELETE / → Delete all
│
├── /api/scan/* (scan.py)
│   ├── POST /run → Start scan
│   ├── GET /results → Get results
│   ├── GET /results/latest → Latest results
│   └── DELETE /results → Clear results
│
└── /api/logs/* (logs.py)
    ├── GET / → Get logs
    ├── DELETE / → Clear logs
    └── GET /stats → Get statistics
```

---

## 🗄️ Database Schema

```
MongoDB: ubique_product_checker
│
├── Collection: urls
│   ├── _id: ObjectId (PK)
│   ├── url: String (unique)
│   ├── created_at: DateTime
│   └── group_name: String (optional)
│
├── Collection: scan_results
│   ├── _id: ObjectId (PK)
│   ├── url: String
│   ├── url_id: String (FK to urls._id)
│   ├── scanned_at: DateTime
│   ├── add_to_cart: Boolean
│   ├── buy_now: Boolean
│   ├── status: String (available/unavailable/error)
│   ├── error_message: String (optional)
│   └── response_time: Float
│
└── Collection: logs
    ├── _id: ObjectId (PK)
    ├── event_type: String
    ├── details: Object
    ├── timestamp: DateTime
    └── level: String (INFO/WARNING/ERROR)
```

---

## 🔍 Scraper Engine Architecture

```
scraper.py (Main Controller)
│
├── fetch_static_html()
│   ├── Use: aiohttp
│   ├── For: Simple HTML pages
│   └── Fast but limited
│
├── fetch_dynamic_html()
│   ├── Use: Playwright
│   ├── For: JavaScript-heavy sites
│   └── Slower but comprehensive
│
└── scrape_url()
    ├── Try Playwright first
    ├── Fallback to static
    └── Pass HTML to detector
    
detector.py (Detection Engine)
│
├── Load detection_rules.json
│
├── detect_button(html, url, type)
│   ├── Parse HTML with BeautifulSoup
│   ├── Check domain-specific rules
│   ├── Try CSS selectors
│   ├── Try text patterns
│   └── Return result
│
└── detect_all_buttons()
    ├── Detect "Add to Cart"
    ├── Detect "Buy Now"
    └── Determine overall status

detection_rules.json (Configuration)
│
├── add_to_cart
│   ├── css_selectors: []
│   ├── text_patterns: []
│   └── domains: {}
│
├── buy_now
│   ├── css_selectors: []
│   ├── text_patterns: []
│   └── domains: {}
│
└── settings
    ├── case_sensitive
    ├── partial_match
    └── timeout
```

---

## 🐳 Docker Container Architecture

```
docker-compose.yml
│
├── Network: ubique-network
│   └── Bridge network for inter-container communication
│
├── Service: mongodb
│   ├── Image: mongo:7.0
│   ├── Port: 27017
│   ├── Volume: mongodb_data
│   └── Database: ubique_product_checker
│
├── Service: backend
│   ├── Build: ./backend/Dockerfile
│   ├── Port: 8000
│   ├── Depends: mongodb
│   ├── Volumes:
│   │   ├── ./backend/logs:/app/logs
│   │   └── ./scraper:/app/scraper
│   └── Environment:
│       ├── MONGODB_URL
│       ├── SCRAPER_TIMEOUT
│       └── LOG_LEVEL
│
└── Service: frontend
    ├── Build: ./frontend/Dockerfile
    ├── Port: 3000
    ├── Depends: backend
    └── Environment:
        └── NEXT_PUBLIC_API_URL
```

---

## 📊 Request/Response Cycle

### Example: Running a Scan

```
1. User Action
   └─→ Click "Run Scan" button

2. Frontend
   └─→ handleRunScan()
       └─→ api.runScan()
           └─→ axios.post('/api/scan/run', {})

3. Network
   └─→ HTTP POST to http://localhost:8000/api/scan/run
       Headers: { Content-Type: application/json }
       Body: {}

4. Backend
   └─→ FastAPI receives request
       └─→ scan.py: run_scan()
           ├─→ Validate request
           ├─→ Get URLs from DB
           ├─→ Create background task
           └─→ Return response immediately

5. Background Task
   └─→ run_scan_task()
       ├─→ For each URL:
       │   ├─→ Call scraper.scrape_url()
       │   │   ├─→ Fetch HTML
       │   │   └─→ detector.detect_all_buttons()
       │   ├─→ Save result to DB
       │   └─→ Log event
       └─→ Complete

6. Response
   └─→ {
         "message": "Scan started for 10 URLs",
         "url_count": 10,
         "status": "running"
       }

7. Frontend
   └─→ Receive response
       ├─→ Show notification
       ├─→ Set scanning state
       └─→ Start polling for results

8. Polling
   └─→ Every 5 seconds:
       └─→ api.getLatestResults()
           └─→ GET /api/scan/results/latest
               └─→ Update ResultsTable

9. Display
   └─→ ResultsTable.tsx
       └─→ Show scan results with status indicators
```

---

## 🔐 Security Flow

```
Frontend Request
│
├─→ URL Validation
│   └─→ Check format (http/https)
│
├─→ CORS Check
│   └─→ Origin must be in allowed list
│
├─→ Input Sanitization
│   └─→ Remove malicious characters
│
├─→ API Request
│   └─→ Send to backend
│
Backend Processing
│
├─→ Pydantic Validation
│   └─→ Verify request schema
│
├─→ Input Sanitization
│   └─→ Clean dangerous inputs
│
├─→ Business Logic
│   └─→ Process request
│
└─→ Database Operation
    └─→ Use parameterized queries
```

---

## 🔄 State Management

### Frontend State Flow

```
Application State
│
├── URLs State
│   ├── Source: MongoDB via API
│   ├── Update: On add/delete
│   └── Display: URLList component
│
├── Results State
│   ├── Source: MongoDB via API
│   ├── Update: After scans
│   └── Display: ResultsTable component
│
├── Stats State
│   ├── Source: Aggregated from DB
│   ├── Update: On data changes
│   └── Display: StatsCard component
│
└── UI State
    ├── loading: Boolean
    ├── scanning: Boolean
    └── notification: Object
```

---

## 📈 Performance Optimization

```
Frontend Optimizations
├── React Memoization
│   ├── useMemo for expensive calculations
│   └── useCallback for functions
│
├── Code Splitting
│   └── Dynamic imports for heavy components
│
└── Lazy Loading
    └── Load data on demand

Backend Optimizations
├── Async Operations
│   ├── AsyncIO for database
│   ├── Concurrent scanning
│   └── Background tasks
│
├── Database Indexing
│   ├── Index on url field
│   └── Compound index on url + scanned_at
│
└── Caching (Future)
    └── Redis for frequent queries

Scraper Optimizations
├── Concurrent Requests
│   └── asyncio.gather() for parallel scraping
│
├── Smart Rendering
│   ├── Static fetch for simple sites
│   └── Playwright only when needed
│
└── Timeout Management
    └── Configurable per-site timeouts
```

---

## 🎯 Key Design Patterns

### Backend
- **Repository Pattern** - Database abstraction
- **Service Layer** - Business logic separation
- **Dependency Injection** - Via FastAPI
- **Background Tasks** - For async operations

### Frontend
- **Component Composition** - Reusable UI pieces
- **Custom Hooks** - Shared logic
- **Props Drilling** - Simple state management
- **Fetch-on-Render** - Data loading pattern

### Scraper
- **Strategy Pattern** - Multiple fetch strategies
- **Factory Pattern** - Scraper instantiation
- **Configuration Pattern** - JSON-based rules
- **Fallback Pattern** - Graceful degradation

---

**These diagrams show the complete system architecture!** 🎨
