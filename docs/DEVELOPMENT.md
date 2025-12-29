# 🛠️ Developer Guide

## Development Workflow

### Project Structure

```
Product Checker/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── models/      # Data models
│   │   ├── utils/       # Utilities
│   │   ├── config.py    # Configuration
│   │   ├── database.py  # MongoDB connection
│   │   └── main.py      # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
│
├── scraper/             # Scraper engine
│   ├── scraper.py      # Main scraper logic
│   ├── detector.py     # Button detection
│   └── detection_rules.json
│
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── lib/        # API client
│   │   ├── pages/      # Next.js pages
│   │   └── styles/     # CSS
│   └── package.json
│
└── docker-compose.yml
```

---

## Setting Up Development Environment

### Backend Development

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```cmd
cd frontend
npm install

# Run development server
npm run dev
```

### Running MongoDB Locally

```cmd
# With Docker
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Update .env
MONGODB_URL=mongodb://localhost:27017
```

---

## Code Style

### Python (Backend)

- Follow PEP 8
- Use type hints
- Write docstrings for functions

```python
async def scrape_url(url: str, use_playwright: bool = True) -> Dict:
    """
    Scrape a URL and detect buy buttons
    
    Args:
        url: URL to scrape
        use_playwright: Whether to use Playwright
    
    Returns:
        Dict containing scan results
    """
    pass
```

### TypeScript (Frontend)

- Use TypeScript for type safety
- Follow React best practices
- Use functional components with hooks

```typescript
interface URLInputProps {
  onAdd: (urls: string[], groupName?: string) => Promise<void>;
  loading: boolean;
}

const URLInput: React.FC<URLInputProps> = ({ onAdd, loading }) => {
  // Component code
};
```

---

## Testing

### Backend Tests

```cmd
cd backend
pytest tests/ -v
```

### Frontend Tests

```cmd
cd frontend
npm test
```

### Integration Tests

```cmd
# Start all services
docker-compose up -d

# Run integration tests
pytest integration_tests/ -v
```

---

## Adding New Features

### Adding a New API Endpoint

1. **Create endpoint in `backend/app/api/`**

```python
# backend/app/api/new_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/feature", tags=["Feature"])

@router.get("/")
async def get_feature():
    return {"message": "New feature"}
```

2. **Register router in `main.py`**

```python
from app.api import new_feature

app.include_router(new_feature.router)
```

3. **Update frontend API client**

```typescript
// frontend/src/lib/api.ts
export const getFeature = async () => {
  const response = await api.get('/api/feature');
  return response.data;
};
```

### Adding Detection Rules

Edit `scraper/detection_rules.json`:

```json
{
  "add_to_cart": {
    "domains": {
      "newsite.com": {
        "selectors": ["#custom-add-button"],
        "text": ["Add Product"]
      }
    }
  }
}
```

### Creating New UI Components

```typescript
// frontend/src/components/NewComponent.tsx
import React from 'react';

interface NewComponentProps {
  data: string;
}

const NewComponent: React.FC<NewComponentProps> = ({ data }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold">{data}</h2>
    </div>
  );
};

export default NewComponent;
```

---

## Database Operations

### Adding New Collections

1. **Create model in `backend/app/models/schemas.py`**

```python
class NewModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    field1: str
    field2: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

2. **Use in API endpoints**

```python
@router.post("/")
async def create_item(item: NewModel):
    db = get_database()
    result = await db.new_collection.insert_one(item.dict())
    return {"id": str(result.inserted_id)}
```

### MongoDB Queries

```python
# Find one
item = await db.collection.find_one({"field": "value"})

# Find many with filter
items = await db.collection.find({"status": "active"}).to_list(100)

# Insert
result = await db.collection.insert_one(document)

# Update
result = await db.collection.update_one(
    {"_id": ObjectId(id)},
    {"$set": {"field": "new_value"}}
)

# Delete
result = await db.collection.delete_one({"_id": ObjectId(id)})
```

---

## Debugging

### Backend Debugging

**Using logs:**
```python
from app.utils.logger import logger

logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

**Using pdb:**
```python
import pdb; pdb.set_trace()
```

**VS Code launch.json:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Frontend Debugging

**Browser DevTools:**
- Console logs: `console.log()`
- Network tab: Check API calls
- React DevTools extension

**VS Code debugger:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next.js: debug",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/frontend/node_modules/.bin/next",
      "args": ["dev"],
      "cwd": "${workspaceFolder}/frontend"
    }
  ]
}
```

---

## Common Development Tasks

### Update Dependencies

**Python:**
```cmd
cd backend
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

**Node:**
```cmd
cd frontend
npm update
npm audit fix
```

### Clear Database

```cmd
docker exec -it ubique-mongodb mongosh
use ubique_product_checker
db.dropDatabase()
```

### View Logs

```cmd
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Rebuild Containers

```cmd
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Performance Optimization

### Backend

**Use async/await properly:**
```python
# Good
results = await asyncio.gather(*[scrape_url(url) for url in urls])

# Bad
results = [await scrape_url(url) for url in urls]
```

**Database indexing:**
```python
# Create indexes
await db.urls.create_index("url", unique=True)
await db.scan_results.create_index([("url", 1), ("scanned_at", -1)])
```

### Frontend

**Code splitting:**
```typescript
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('@/components/Heavy'), {
  loading: () => <p>Loading...</p>,
});
```

**Memoization:**
```typescript
import { useMemo, useCallback } from 'react';

const expensiveValue = useMemo(() => computeExpensiveValue(data), [data]);
const handleClick = useCallback(() => doSomething(), []);
```

---

## Security Best Practices

### Input Validation

**Backend:**
```python
from pydantic import BaseModel, validator, HttpUrl

class URLInput(BaseModel):
    url: HttpUrl  # Pydantic validates URL format
    
    @validator('url')
    def validate_url(cls, v):
        if not str(v).startswith(('http://', 'https://')):
            raise ValueError('Invalid URL')
        return v
```

**Frontend:**
```typescript
const validateURL = (url: string): boolean => {
  try {
    new URL(url);
    return url.startsWith('http://') || url.startsWith('https://');
  } catch {
    return false;
  }
};
```

### Environment Variables

Never commit sensitive data:
```python
# Use python-dotenv
from dotenv import load_dotenv
import os

load_dotenv()
secret_key = os.getenv('SECRET_KEY')
```

---

## Deployment Checklist

- [ ] Update `.env` with production values
- [ ] Change `SECRET_KEY`
- [ ] Set `BACKEND_RELOAD=false`
- [ ] Configure MongoDB authentication
- [ ] Set up HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Enable logging to file
- [ ] Set up backups
- [ ] Configure firewall
- [ ] Test all endpoints
- [ ] Load testing
- [ ] Security audit

---

## Contributing

### Branch Strategy

- `main` - Production-ready code
- `develop` - Development branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Commit Messages

Follow conventional commits:

```
feat: add new detection rule for shopify
fix: resolve timeout issue in scraper
docs: update API documentation
chore: update dependencies
test: add tests for URL validation
```

### Pull Request Process

1. Create feature branch
2. Make changes
3. Write/update tests
4. Update documentation
5. Submit PR with description
6. Address review comments
7. Merge after approval

---

## Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Playwright Docs](https://playwright.dev/)
- [MongoDB Docs](https://docs.mongodb.com/)

### Tools
- [Postman](https://www.postman.com/) - API testing
- [MongoDB Compass](https://www.mongodb.com/products/compass) - Database GUI
- [React DevTools](https://react.dev/learn/react-developer-tools)

---

Happy coding! 🚀
