# 🔧 Troubleshooting Guide

## Common Issues and Solutions

---

## Installation Issues

### Docker Not Found

**Error:** `'docker' is not recognized as an internal or external command`

**Solutions:**
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop
2. Restart your computer after installation
3. Verify: `docker --version`

---

### Port Already in Use

**Error:** `Port 3000/8000/27017 is already allocated`

**Solutions:**

**Option 1: Stop conflicting services**
```cmd
# Find what's using the port
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :27017

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Option 2: Change ports in `docker-compose.yml`**
```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # Use 3001 instead
  backend:
    ports:
      - "8001:8000"  # Use 8001 instead
```

---

### Docker Compose Not Found

**Error:** `docker-compose: command not found`

**Solution:**
Docker Desktop includes Docker Compose. If missing:
1. Update Docker Desktop
2. Or use: `docker compose up -d` (newer syntax without hyphen)

---

## Runtime Issues

### Services Won't Start

**Error:** Containers exit immediately or won't start

**Diagnosis:**
```cmd
# Check container status
docker ps -a

# View logs
docker-compose logs

# Check specific service
docker-compose logs backend
```

**Common Causes:**

1. **MongoDB won't start:**
   ```cmd
   # Remove old data
   docker-compose down -v
   docker-compose up -d
   ```

2. **Backend crashes:**
   - Check Python dependencies: `docker-compose logs backend`
   - Verify .env file exists
   - Check MongoDB connection

3. **Frontend build fails:**
   - Check Node.js version in Dockerfile
   - Clear npm cache: `docker-compose build --no-cache frontend`

---

### Can't Access Frontend

**Issue:** http://localhost:3000 not loading

**Solutions:**

1. **Check if container is running:**
   ```cmd
   docker ps | findstr frontend
   ```

2. **Check logs:**
   ```cmd
   docker-compose logs frontend
   ```

3. **Wait longer:**
   - Initial build takes 2-3 minutes
   - Subsequent starts take 30-60 seconds

4. **Verify port mapping:**
   ```cmd
   docker ps
   # Should show: 0.0.0.0:3000->3000/tcp
   ```

5. **Try restart:**
   ```cmd
   docker-compose restart frontend
   ```

---

### Backend API Not Responding

**Issue:** http://localhost:8000 returns 404 or connection refused

**Solutions:**

1. **Check backend health:**
   ```cmd
   curl http://localhost:8000/health
   ```

2. **View backend logs:**
   ```cmd
   docker-compose logs -f backend
   ```

3. **Common issues:**
   - MongoDB not connected: Check connection string
   - Port conflict: Change port in docker-compose.yml
   - Python errors: Check requirements.txt

4. **Restart backend:**
   ```cmd
   docker-compose restart backend
   ```

---

### MongoDB Connection Failed

**Error:** `Failed to connect to MongoDB`

**Solutions:**

1. **Check MongoDB is running:**
   ```cmd
   docker ps | findstr mongodb
   ```

2. **Start MongoDB:**
   ```cmd
   docker-compose up -d mongodb
   ```

3. **Check connection string in `.env`:**
   ```
   MONGODB_URL=mongodb://mongodb:27017
   ```

4. **Test MongoDB directly:**
   ```cmd
   docker exec -it ubique-mongodb mongosh
   ```

5. **Reset MongoDB:**
   ```cmd
   docker-compose down -v
   docker-compose up -d mongodb
   ```

---

## Scanning Issues

### All Scans Return Error

**Issue:** Every URL shows error status

**Diagnosis:**

1. **Check backend logs:**
   ```cmd
   docker-compose logs backend | findstr ERROR
   ```

2. **Test scraper directly:**
   ```cmd
   cd scraper
   python scraper.py
   ```

**Common Causes:**

1. **Playwright not installed:**
   ```cmd
   docker exec -it ubique-backend bash
   playwright install chromium
   ```

2. **Timeout too short:**
   - Edit `.env`: `SCRAPER_TIMEOUT=60`
   - Restart: `docker-compose restart backend`

3. **Network issues:**
   - Check internet connection
   - Try different URLs
   - Check firewall settings

---

### Buttons Not Detected

**Issue:** Valid products showing "unavailable"

**Solutions:**

1. **Check URL in browser:**
   - Verify buttons exist on page
   - Confirm page loads correctly

2. **Review detection rules:**
   - Open `scraper/detection_rules.json`
   - Add site-specific selectors if needed

3. **Try with Playwright enabled:**
   - Edit `.env`: `SCRAPER_USE_PLAYWRIGHT=true`
   - Restart backend

4. **Test specific URL:**
   ```python
   from scraper import scrape_url
   result = await scrape_url("https://example.com/product")
   print(result)
   ```

5. **Add custom detection rule:**
   ```json
   {
     "add_to_cart": {
       "domains": {
         "yoursite.com": {
           "selectors": ["#custom-button-id"],
           "text": ["Custom Button Text"]
         }
       }
     }
   }
   ```

---

### Scans Are Too Slow

**Issue:** Takes too long to scan URLs

**Solutions:**

1. **Increase concurrency:**
   ```
   # In .env
   SCRAPER_MAX_CONCURRENT=10
   ```

2. **Disable Playwright for static sites:**
   ```
   SCRAPER_USE_PLAYWRIGHT=false
   ```

3. **Reduce timeout:**
   ```
   SCRAPER_TIMEOUT=15
   ```

4. **Check network speed:**
   - Test internet connection
   - Try fewer URLs at once

---

## Frontend Issues

### "Failed to fetch" Errors

**Issue:** Frontend can't communicate with backend

**Solutions:**

1. **Check API URL in browser console:**
   - Should be: `http://localhost:8000`

2. **Verify CORS settings:**
   ```python
   # In backend/app/main.py
   CORS_ORIGINS=http://localhost:3000
   ```

3. **Check backend is accessible:**
   ```cmd
   curl http://localhost:8000/health
   ```

4. **Clear browser cache:**
   - Ctrl + Shift + Delete
   - Clear all cache
   - Refresh page

---

### UI Not Updating

**Issue:** Data doesn't refresh after actions

**Solutions:**

1. **Hard refresh browser:**
   - Ctrl + F5 (Windows)
   - Cmd + Shift + R (Mac)

2. **Check browser console:**
   - F12 → Console tab
   - Look for JavaScript errors

3. **Clear browser cache:**
   - Settings → Clear browsing data
   - Refresh page

4. **Restart frontend:**
   ```cmd
   docker-compose restart frontend
   ```

---

## Data Issues

### URLs Not Saving

**Issue:** Added URLs disappear

**Solutions:**

1. **Check MongoDB persistence:**
   ```cmd
   docker exec -it ubique-mongodb mongosh
   use ubique_product_checker
   db.urls.find()
   ```

2. **Verify volume mounting:**
   ```cmd
   docker volume ls | findstr mongodb
   ```

3. **Check backend logs:**
   ```cmd
   docker-compose logs backend | findstr "add"
   ```

4. **Test API directly:**
   ```cmd
   curl -X POST http://localhost:8000/api/urls/add ^
     -H "Content-Type: application/json" ^
     -d "{\"urls\":[\"https://example.com\"]}"
   ```

---

### Database Reset Needed

**Issue:** Need to clear all data

**Solutions:**

1. **Via API:**
   ```cmd
   curl -X DELETE http://localhost:8000/api/urls
   curl -X DELETE http://localhost:8000/api/scan/results
   ```

2. **Via MongoDB:**
   ```cmd
   docker exec -it ubique-mongodb mongosh
   use ubique_product_checker
   db.dropDatabase()
   ```

3. **Complete reset:**
   ```cmd
   docker-compose down -v
   docker-compose up -d
   ```

---

## Performance Issues

### High Memory Usage

**Issue:** Docker using too much RAM

**Solutions:**

1. **Check resource usage:**
   ```cmd
   docker stats
   ```

2. **Limit container memory in `docker-compose.yml`:**
   ```yaml
   services:
     backend:
       mem_limit: 512m
   ```

3. **Reduce concurrent scans:**
   ```
   SCRAPER_MAX_CONCURRENT=3
   ```

4. **Disable Playwright:**
   ```
   SCRAPER_USE_PLAYWRIGHT=false
   ```

---

### Disk Space Issues

**Issue:** Docker using too much disk space

**Solutions:**

1. **Check disk usage:**
   ```cmd
   docker system df
   ```

2. **Clean up:**
   ```cmd
   docker system prune -a
   docker volume prune
   ```

3. **Clear logs:**
   ```cmd
   # Delete log files
   del backend\logs\*.log
   ```

---

## Development Issues

### Python Dependencies Won't Install

**Issue:** pip install fails

**Solutions:**

1. **Update pip:**
   ```cmd
   python -m pip install --upgrade pip
   ```

2. **Install build tools:**
   - Install Visual Studio Build Tools
   - Or: Microsoft C++ Build Tools

3. **Try one package at a time:**
   ```cmd
   pip install fastapi
   pip install uvicorn
   # etc.
   ```

4. **Use virtual environment:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

---

### Node Modules Issues

**Issue:** npm install fails or modules not found

**Solutions:**

1. **Clear npm cache:**
   ```cmd
   npm cache clean --force
   ```

2. **Delete node_modules:**
   ```cmd
   rmdir /s /q node_modules
   npm install
   ```

3. **Update npm:**
   ```cmd
   npm install -g npm@latest
   ```

4. **Use correct Node version:**
   - Install Node 18 LTS
   - Check: `node --version`

---

### Playwright Installation Fails

**Issue:** `playwright install` errors

**Solutions:**

1. **Install system dependencies:**
   ```cmd
   playwright install-deps
   ```

2. **Install specific browser:**
   ```cmd
   playwright install chromium
   ```

3. **Use Docker:**
   - Playwright is pre-installed in Docker image
   - No manual installation needed

---

## Logging and Debugging

### Enable Debug Logging

**Backend:**
```
# In .env
LOG_LEVEL=DEBUG
```

**Frontend:**
```typescript
// In browser console
localStorage.setItem('debug', '*');
```

---

### View All Logs

```cmd
# All services
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb

# Save logs to file
docker-compose logs > debug.log
```

---

### Access Container Shell

```cmd
# Backend
docker exec -it ubique-backend bash

# Frontend
docker exec -it ubique-frontend sh

# MongoDB
docker exec -it ubique-mongodb mongosh
```

---

## Getting Help

### Before Asking for Help

1. ✅ Check this troubleshooting guide
2. ✅ Review error messages in logs
3. ✅ Try restarting services
4. ✅ Check all documentation files
5. ✅ Test with simple examples

### What to Include

When reporting issues, provide:
- Error message (exact text)
- Relevant logs
- Steps to reproduce
- System information
- What you've already tried

### Useful Commands

```cmd
# System info
docker --version
docker-compose --version
python --version
node --version

# Container status
docker ps -a

# All logs
docker-compose logs > all-logs.txt

# Resource usage
docker stats --no-stream
```

---

## Still Having Issues?

1. **Review documentation:**
   - README.md
   - SETUP.md
   - USER_GUIDE.md
   - DEVELOPMENT.md

2. **Check logs carefully:**
   - Often error messages contain the solution

3. **Try fresh start:**
   ```cmd
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. **Contact support:**
   - Provide detailed error information
   - Include steps to reproduce
   - Share relevant logs

---

**Remember:** Most issues can be resolved by:
- Checking logs
- Restarting services
- Verifying configuration
- Reading error messages carefully

Good luck! 🍀
