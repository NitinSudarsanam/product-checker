# 🚀 Setup and Installation Guide

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (recommended for easiest setup)
  - Windows: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Includes Docker and Docker Compose
  
- **Alternative: Local Development**
  - Python 3.11 or higher
  - Node.js 18 or higher
  - MongoDB 7.0 or higher

## Quick Start with Docker (Recommended)

### 1. Clone or Navigate to Project Directory

```cmd
cd "c:\Nitin Computer Science\Product Checker"
```

### 2. Create Environment File

```cmd
copy .env.example .env
```

Edit `.env` if you need to customize any settings (optional for local testing).

### 3. Start All Services

```cmd
docker-compose up -d
```

This single command will:
- Pull necessary Docker images
- Build the backend and frontend
- Start MongoDB, Backend API, and Frontend
- Set up networking between services

### 4. Access the Application

Wait 2-3 minutes for services to start, then:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Stop Services

```cmd
docker-compose down
```

To also remove data volumes:

```cmd
docker-compose down -v
```

---

## Local Development Setup

If you prefer to run services individually without Docker:

### Backend Setup

1. **Navigate to backend directory**
   ```cmd
   cd backend
   ```

2. **Create virtual environment**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```cmd
   playwright install chromium
   ```

5. **Start MongoDB**
   - Install MongoDB locally or use MongoDB Atlas
   - Update `MONGODB_URL` in `.env`

6. **Run the backend**
   ```cmd
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```cmd
   cd frontend
   ```

2. **Install dependencies**
   ```cmd
   npm install
   ```

3. **Start development server**
   ```cmd
   npm run dev
   ```

### Scraper Testing

To test the scraper independently:

```cmd
cd scraper
python scraper.py
```

---

## Configuration

### Environment Variables

Key variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://mongodb:27017` | MongoDB connection string |
| `MONGODB_DATABASE` | `ubique_product_checker` | Database name |
| `BACKEND_PORT` | `8000` | Backend API port |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API URL for frontend |
| `SCRAPER_TIMEOUT` | `30` | Scraper timeout in seconds |
| `SCRAPER_USE_PLAYWRIGHT` | `true` | Use Playwright for dynamic sites |
| `SCRAPER_MAX_CONCURRENT` | `5` | Max concurrent scraper tasks |
| `LOG_LEVEL` | `INFO` | Logging level |

### Detection Rules

Customize button detection in `scraper/detection_rules.json`:

```json
{
  "add_to_cart": {
    "css_selectors": ["#add-to-cart", ".add-to-cart"],
    "text_patterns": ["add to cart", "add to bag"],
    "domains": {
      "amazon.com": {
        "selectors": ["#add-to-cart-button"],
        "text": ["Add to Cart"]
      }
    }
  }
}
```

---

## Verification

### Check Service Health

1. **Backend Health**
   ```cmd
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy","database":"connected"}`

2. **Frontend**
   Open http://localhost:3000 in your browser

3. **MongoDB**
   ```cmd
   docker exec -it ubique-mongodb mongosh
   ```

### View Logs

```cmd
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongodb

# Follow logs in real-time
docker-compose logs -f backend
```

---

## Common Issues

### Port Already in Use

If ports 3000, 8000, or 27017 are already in use:

1. Stop the conflicting service
2. Or change ports in `docker-compose.yml`:
   ```yaml
   ports:
     - "8001:8000"  # Use port 8001 instead of 8000
   ```

### Playwright Installation Fails

```cmd
# In backend container or local environment
playwright install-deps
playwright install chromium
```

### MongoDB Connection Failed

- Ensure MongoDB container is running: `docker ps`
- Check connection string in `.env`
- Restart backend: `docker-compose restart backend`

### Frontend Can't Connect to Backend

- Check `NEXT_PUBLIC_API_URL` in `.env`
- Verify backend is running: http://localhost:8000/health
- Check browser console for CORS errors

---

## Updating the Application

### Pull Latest Changes

```cmd
git pull origin main
```

### Rebuild Docker Containers

```cmd
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Update Python Dependencies

```cmd
cd backend
pip install -r requirements.txt --upgrade
```

### Update Node Dependencies

```cmd
cd frontend
npm install
```

---

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Use strong MongoDB credentials
- [ ] Enable MongoDB authentication
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure firewall rules
- [ ] Disable debug mode (`BACKEND_RELOAD=false`)
- [ ] Set appropriate CORS origins
- [ ] Regular backups of MongoDB data

### Docker Production Build

```cmd
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production

```bash
MONGODB_URL=mongodb://username:password@mongodb:27017
SECRET_KEY=your-very-secure-secret-key-here
BACKEND_RELOAD=false
LOG_LEVEL=WARNING
CORS_ORIGINS=https://yourdomain.com
```

---

## Backup and Restore

### Backup MongoDB Data

```cmd
docker exec ubique-mongodb mongodump --out /backup
docker cp ubique-mongodb:/backup ./backup
```

### Restore MongoDB Data

```cmd
docker cp ./backup ubique-mongodb:/backup
docker exec ubique-mongodb mongorestore /backup
```

---

## Performance Tuning

### Increase Concurrent Scraping

Edit `.env`:
```
SCRAPER_MAX_CONCURRENT=10
```

### Disable Playwright for Static Sites

```
SCRAPER_USE_PLAYWRIGHT=false
```

### Increase Timeout for Slow Sites

```
SCRAPER_TIMEOUT=60
```

---

## Support

For issues and questions:

1. Check logs: `docker-compose logs`
2. Review this documentation
3. Check GitHub issues
4. Contact development team

---

## Next Steps

After successful installation:

1. ✅ Add test URLs through the UI
2. ✅ Run your first scan
3. ✅ Review results table
4. ✅ Customize detection rules if needed
5. ✅ Set up scheduled scans (future feature)

Happy scanning! 🎉
