# 🎯 Ubique Buy-Button Detection System - Implementation Plan

## Project Overview
Complete engineering blueprint for building a web scraping system that detects "Add to Cart" and "Buy Now" buttons on e-commerce websites.

---

## 📋 Phase 1: Backend + Database Setup

### Tasks
- [x] Create project folder structure
- [ ] Set up FastAPI application
- [ ] Create API endpoints:
  - `POST /api/urls/add` - Add URLs
  - `GET /api/urls` - List all URLs
  - `DELETE /api/urls/{id}` - Delete URL
  - `POST /api/scan/run` - Trigger scan
  - `GET /api/scan/results` - Get results
  - `GET /api/logs` - View logs
- [ ] Connect to MongoDB
- [ ] Create Pydantic models
- [ ] Implement database operations (CRUD)
- [ ] Add input validation and sanitization
- [ ] Set up logging layer

**Deliverables:**
- FastAPI backend running on port 8000
- MongoDB connection established
- All API endpoints functional
- Basic error handling

**Duration:** 2-3 days

---

## 🕷️ Phase 2: Scraper Engine

### Tasks
- [ ] Create scraper module structure
- [ ] Implement static HTML fetcher (requests + BeautifulSoup)
- [ ] Add Playwright for dynamic JS rendering
- [ ] Build selector-based detection logic
- [ ] Create `detection_rules.json` configuration
- [ ] Implement CSS selector matching
- [ ] Add text-based button detection fallback
- [ ] Handle timeouts and errors gracefully
- [ ] Return structured results (add_to_cart, buy_now, status)

**Deliverables:**
- Working scraper that can detect buttons on:
  - Static HTML sites
  - Dynamic JavaScript sites (Amazon, Shopify, etc.)
- Configurable detection rules
- Error handling for 404s, timeouts, invalid HTML

**Duration:** 3-4 days

---

## 🎨 Phase 3: Frontend Development

### Tasks
- [ ] Initialize Next.js 14 project
- [ ] Set up Tailwind CSS
- [ ] Create main layout and navigation
- [ ] Build URL input component (single)
- [ ] Build bulk URL import component (multi-line textarea)
- [ ] Create "Run Scan" button with loading state
- [ ] Build results table with columns:
  - URL
  - Add to Cart (✓/✗)
  - Buy Now (✓/✗)
  - Status
  - Last Scanned
- [ ] Add error message display
- [ ] Implement API integration with axios
- [ ] Add URL management (view, delete)
- [ ] Create responsive design for mobile

**Deliverables:**
- Fully functional React UI
- Clean, professional interface
- Real-time scan progress feedback
- Mobile-responsive design

**Duration:** 3-4 days

---

## 🔗 Phase 4: Integration & Testing

### Tasks
- [ ] Connect frontend to backend API
- [ ] Test URL submission workflow
- [ ] Test bulk URL import
- [ ] Test manual scan trigger
- [ ] Verify results display correctly
- [ ] Test error scenarios:
  - Invalid URLs
  - Timeout errors
  - Network failures
  - Button not found
- [ ] End-to-end testing with 20-50 real URLs
- [ ] Performance testing
- [ ] Fix bugs and edge cases

**Deliverables:**
- Fully integrated system
- Tested with real e-commerce sites
- All critical bugs resolved

**Duration:** 2-3 days

---

## ✨ Phase 5: Polish & Documentation

### Tasks
- [ ] Improve UI/UX based on testing
- [ ] Add better error messages
- [ ] Implement loading indicators
- [ ] Add success notifications
- [ ] Create user documentation
- [ ] Write API documentation
- [ ] Add code comments
- [ ] Create deployment guide
- [ ] Optimize performance
- [ ] Security review (input sanitization, CORS)

**Deliverables:**
- Production-ready POC
- Complete documentation
- Security-hardened code

**Duration:** 2 days

---

## 🐳 Phase 6: Docker Configuration

### Tasks
- [ ] Create Dockerfile for backend
- [ ] Create Dockerfile for frontend
- [ ] Create docker-compose.yml
- [ ] Configure MongoDB container
- [ ] Set up container networking
- [ ] Add volume mounts for persistence
- [ ] Test Docker deployment
- [ ] Create startup scripts

**Deliverables:**
- One-command deployment with Docker Compose
- Persistent data storage
- Easy environment configuration

**Duration:** 1-2 days

---

## 🚀 Future Enhancements (Post-POC)

### Phase 7: Scheduler Implementation
- [ ] Add Celery for task queue
- [ ] Create scheduled scan jobs
- [ ] Build scheduling UI
- [ ] Add cron-like configuration
- [ ] Implement background workers

### Phase 8: Notifications
- [ ] Email notification system
- [ ] Slack integration
- [ ] Webhook support
- [ ] Alert configuration UI

### Phase 9: Advanced Features
- [ ] URL grouping/categorization
- [ ] Screenshot capture on scan
- [ ] Historical trend tracking
- [ ] Domain-specific detection rules
- [ ] AI-based fallback detection
- [ ] Multi-threaded scraping
- [ ] Rate limiting
- [ ] Proxy rotation

### Phase 10: Analytics & Reporting
- [ ] Dashboard with statistics
- [ ] Export results (CSV, JSON)
- [ ] Scan history visualization
- [ ] Availability tracking over time

---

## 📊 Success Metrics

### POC Success Criteria
- ✅ Can add and store URLs
- ✅ Can scan URLs manually
- ✅ Correctly detects buy buttons on 80%+ of sites
- ✅ Results display in under 5 seconds per URL
- ✅ Clean, professional UI
- ✅ No critical bugs
- ✅ Docker deployment works

### Performance Targets
- Scan 100 URLs in under 5 minutes
- 95% uptime
- < 500ms API response time
- < 2MB memory per scan

---

## 🛠️ Technical Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend API | FastAPI (Python) | REST API, business logic |
| Frontend | Next.js 14 + React | User interface |
| Styling | Tailwind CSS | UI design |
| Scraper | BeautifulSoup + Playwright | Web scraping |
| Database | MongoDB | Data persistence |
| Containerization | Docker + Docker Compose | Deployment |
| Task Queue (Future) | Celery | Scheduled jobs |
| Notifications (Future) | SMTP, Slack API | Alerts |

---

## 📅 Timeline

**Total POC Duration:** 13-18 days

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Backend | 2-3 days | None |
| Phase 2: Scraper | 3-4 days | Phase 1 |
| Phase 3: Frontend | 3-4 days | Phase 1 |
| Phase 4: Integration | 2-3 days | Phase 1-3 |
| Phase 5: Polish | 2 days | Phase 4 |
| Phase 6: Docker | 1-2 days | Phase 1-5 |

---

## 🎯 Next Immediate Steps

1. **Set up backend FastAPI application** ✓ (Starting now)
2. **Create database models and connections**
3. **Build scraper engine core**
4. **Develop frontend UI**
5. **Integrate all components**
6. **Deploy with Docker**

---

## 💡 Key Design Decisions

### Why FastAPI?
- Modern, fast Python framework
- Automatic API documentation
- Async support for concurrent scraping
- Easy integration with Python scraping tools

### Why MongoDB?
- Flexible schema for varying HTML patterns
- Easy to scale
- JSON-like documents match our data structure
- Good for rapid prototyping

### Why Playwright over Selenium?
- Modern, actively maintained
- Better performance
- Built-in auto-wait functionality
- Cross-browser support

### Why Next.js?
- Server-side rendering option
- Great developer experience
- Built-in routing
- Production-ready out of the box

---

**This document is the complete roadmap for building the Ubique Buy-Button Detection System.**
