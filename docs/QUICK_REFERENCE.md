# ⚡ Quick Reference Card

## 🚀 Getting Started (30 seconds)

```cmd
cd "c:\Nitin Computer Science\Product Checker"
start.bat
```

Wait 2 minutes, then open: **http://localhost:3000**

---

## 🔗 Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main UI |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Health Check** | http://localhost:8000/health | Status |

---

## ⌨️ Essential Commands

### Docker

```cmd
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Restart service
docker-compose restart backend

# Check status
docker ps
```

### Backend (Local Development)

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend (Local Development)

```cmd
cd frontend
npm install
npm run dev
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `.env` | Configuration |
| `scraper/detection_rules.json` | Button detection rules |
| `docker-compose.yml` | Service orchestration |
| `backend/app/main.py` | API entry point |
| `frontend/src/pages/index.tsx` | Main UI |

---

## 🔧 Common Tasks

### Add Detection Rule

Edit `scraper/detection_rules.json`:

```json
{
  "add_to_cart": {
    "domains": {
      "yoursite.com": {
        "selectors": ["#buy-button"],
        "text": ["Purchase Now"]
      }
    }
  }
}
```

Restart: `docker-compose restart backend`

### Change Timeout

Edit `.env`:
```
SCRAPER_TIMEOUT=60
```

Restart: `docker-compose restart backend`

### Clear All Data

```cmd
docker-compose down -v
docker-compose up -d
```

### View Logs

```cmd
# All logs
docker-compose logs

# Backend only
docker-compose logs -f backend

# Last 50 lines
docker-compose logs --tail=50 backend
```

---

## 🐛 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Port in use | Change port in `docker-compose.yml` |
| Can't connect | `docker-compose restart` |
| Buttons not detected | Update `detection_rules.json` |
| Scan too slow | Increase `SCRAPER_MAX_CONCURRENT` in `.env` |
| Out of memory | Reduce `SCRAPER_MAX_CONCURRENT` |

---

## 📊 API Endpoints Cheat Sheet

```bash
# Add URLs
POST /api/urls/add
Body: {"urls": ["https://..."], "group_name": "Test"}

# Get URLs
GET /api/urls

# Run Scan
POST /api/scan/run
Body: {}

# Get Results
GET /api/scan/results/latest

# Get Stats
GET /api/logs/stats

# Delete URL
DELETE /api/urls/{id}
```

---

## 🎯 Testing Workflow

1. **Start system:** `start.bat`
2. **Open UI:** http://localhost:3000
3. **Add URL:** Paste product URL
4. **Run scan:** Click "Run Scan"
5. **Check results:** View table

Test URLs:
- Amazon: https://www.amazon.com/dp/B08N5WRWNW
- eBay: https://www.ebay.com/itm/123456

---

## 💾 Backup & Restore

### Backup MongoDB

```cmd
docker exec ubique-mongodb mongodump --out /backup
docker cp ubique-mongodb:/backup ./mongodb-backup
```

### Restore MongoDB

```cmd
docker cp ./mongodb-backup ubique-mongodb:/backup
docker exec ubique-mongodb mongorestore /backup
```

---

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://mongodb:27017` | DB connection |
| `SCRAPER_TIMEOUT` | `30` | Timeout (seconds) |
| `SCRAPER_MAX_CONCURRENT` | `5` | Parallel scans |
| `SCRAPER_USE_PLAYWRIGHT` | `true` | Dynamic rendering |
| `LOG_LEVEL` | `INFO` | Logging detail |

---

## 🔍 Debugging Checklist

- [ ] Check service status: `docker ps`
- [ ] View logs: `docker-compose logs`
- [ ] Test backend: http://localhost:8000/health
- [ ] Test frontend: http://localhost:3000
- [ ] Check `.env` file exists
- [ ] Verify ports not in use
- [ ] Restart services: `docker-compose restart`

---

## 📚 Documentation Quick Links

| Document | Purpose | When to Use |
|----------|---------|-------------|
| `README.md` | Overview | First time setup |
| `SETUP.md` | Installation | Installation issues |
| `USER_GUIDE.md` | Usage | Learning features |
| `TROUBLESHOOTING.md` | Problems | When stuck |
| `API_REFERENCE.md` | API docs | Integration |
| `DEVELOPMENT.md` | Dev guide | Coding |

---

## 🎨 UI Navigation

```
Main Dashboard
├── Statistics Bar (top)
│   ├── Total URLs
│   ├── Total Scans
│   ├── Available
│   ├── Unavailable
│   └── Errors
│
├── Add URLs Section
│   ├── Single URL Tab
│   └── Bulk Import Tab
│
├── Stored URLs Table
│   └── Delete actions
│
└── Scan Results Table
    ├── URL (clickable)
    ├── Add to Cart (✓/✗)
    ├── Buy Now (✓/✗)
    ├── Status badge
    └── Response time
```

---

## ⚡ Performance Tips

### For Speed
- Increase `SCRAPER_MAX_CONCURRENT=10`
- Disable Playwright for static sites
- Reduce timeout for fast sites

### For Reliability
- Decrease concurrent scans
- Increase timeout
- Enable Playwright

### For Resources
- Limit concurrent scans
- Clear old logs
- Remove unused containers

---

## 🎯 Status Indicators

| Icon/Color | Meaning |
|------------|---------|
| 🟢 Green checkmark | Button found |
| ❌ Gray X | Button not found |
| ✅ Available | At least one button found |
| ❌ Unavailable | No buttons found |
| ⚠️ Error | Scan failed |

---

## 🔐 Security Notes

- Change `SECRET_KEY` in production
- Use HTTPS in production
- Enable MongoDB authentication
- Set proper CORS origins
- Regular security updates

---

## 📱 Support

**Documentation:**
- Check relevant `.md` file
- Search TROUBLESHOOTING.md

**Logs:**
```cmd
docker-compose logs | findstr ERROR
```

**Reset:**
```cmd
docker-compose down -v
docker-compose up -d
```

---

## ✅ Daily Checklist

- [ ] Start system: `start.bat`
- [ ] Check health: http://localhost:8000/health
- [ ] Add URLs
- [ ] Run scans
- [ ] Review results
- [ ] Check for errors
- [ ] Stop when done: `stop.bat`

---

## 🎓 Learning Path

1. Read `README.md` - Understand project
2. Run `start.bat` - See it work
3. Follow `USER_GUIDE.md` - Learn features
4. Try `API_REFERENCE.md` - Test APIs
5. Read `DEVELOPMENT.md` - Customize

---

## 💡 Pro Tips

- Use groups to organize URLs
- Run scans during off-peak hours
- Check logs regularly
- Keep detection rules updated
- Test with known products first
- Start with few URLs
- Monitor response times

---

**Print this card for quick reference! 📄**

---

**Need help? Check TROUBLESHOOTING.md** 🆘
