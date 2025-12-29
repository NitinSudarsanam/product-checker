# 🧩 Ubique Buy-Button Detection System

## Overview

The Ubique Buy-Button Detection System is an automated web scraping application that detects the presence of "Add to Cart" and "Buy Now" buttons on e-commerce websites. This system helps track product availability across multiple URLs efficiently.

## Features

### POC Features (Current)
- ✅ Single and bulk URL input
- ✅ Web scraping with static and dynamic rendering
- ✅ Configurable button detection rules
- ✅ Real-time scan results display
- ✅ Database persistence (MongoDB)
- ✅ Comprehensive logging
- ✅ Manual scan triggering
- ✅ Docker containerization

### Future Enhancements
- ⏳ Scheduled automatic scans
- ⏳ Email/Slack notifications
- ⏳ Domain-specific detection patterns
- ⏳ Screenshot capture
- ⏳ AI-based fallback detection
- ⏳ Advanced concurrency/scaling

## Architecture

```
┌─────────────────┐
│  React Frontend │ (Next.js + Tailwind CSS)
└────────┬────────┘
         │ HTTP/REST
┌────────▼────────┐
│  FastAPI Backend│ (Python)
└────────┬────────┘
         │
    ┌────┴─────┬─────────────┐
    │          │             │
┌───▼───┐ ┌───▼───────┐ ┌──▼──────┐
│MongoDB│ │  Scraper  │ │ Logger  │
│  DB   │ │  Engine   │ │ System  │
└───────┘ └───────────┘ └─────────┘
          (BeautifulSoup + Playwright)
```

## Project Structure

```
Product Checker/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI app entry
│   │   ├── api/            # API endpoints
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Helper functions
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
│
├── scraper/                # Scraper engine
│   ├── scraper.py         # Main scraper logic
│   ├── detector.py        # Button detection
│   ├── detection_rules.json # Selector configuration
│   └── requirements.txt
│
├── frontend/              # React/Next.js UI
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Next.js pages
│   │   └── styles/       # CSS/Tailwind
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml    # Docker orchestration
├── .env.example         # Environment variables template
└── README.md           # This file
```

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Motor** - Async MongoDB driver
- **Pydantic** - Data validation

### Scraper
- **BeautifulSoup4** - Static HTML parsing
- **Playwright** - Dynamic JavaScript rendering
- **aiohttp** - Async HTTP requests

### Frontend
- **Next.js 14** - React framework
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client

### Database
- **MongoDB** - Document database for flexible schema

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Installation

1. **Clone the repository**
   ```bash
   cd "c:\Nitin Computer Science\Product Checker"
   ```

2. **Set up environment variables**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` with your configuration

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development Setup

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/urls/add` | Add single or multiple URLs |
| GET | `/api/urls` | Retrieve all stored URLs |
| DELETE | `/api/urls/{id}` | Delete a URL |
| POST | `/api/scan/run` | Trigger manual scan |
| GET | `/api/scan/results` | Get scan results |
| GET | `/api/logs` | Retrieve system logs |

## Configuration

### Detection Rules (`detection_rules.json`)

The scraper uses a configurable JSON file to define button detection patterns:

```json
{
  "add_to_cart": [
    "#add-to-cart",
    "button[id*='add']",
    ".add-to-cart",
    "button:contains('Add to Cart')"
  ],
  "buy_now": [
    "#buy-now",
    "button:contains('Buy Now')",
    ".buy-now"
  ]
}
```

You can customize these selectors for specific e-commerce platforms.

## Usage

1. **Add URLs**: Enter single or multiple URLs in the input field
2. **Run Scan**: Click "Run Scan" to start detection
3. **View Results**: Check the results table for button availability
4. **Review Logs**: Access logs for debugging and auditing

## Database Schema

### URLs Collection
```javascript
{
  _id: ObjectId,
  url: String,
  created_at: DateTime,
  group_name: String (optional)
}
```

### Scan Results Collection
```javascript
{
  _id: ObjectId,
  url: String,
  scanned_at: DateTime,
  add_to_cart: Boolean,
  buy_now: Boolean,
  status: String, // "available" | "unavailable" | "error"
  error_message: String (optional)
}
```

### Logs Collection
```javascript
{
  _id: ObjectId,
  event_type: String,
  details: Object,
  timestamp: DateTime
}
```

## Troubleshooting

### Scraper Issues
- **Timeout errors**: Increase timeout in scraper config
- **JS rendering fails**: Ensure Playwright browsers are installed
- **Button not detected**: Update detection rules in `detection_rules.json`

### Database Connection
- Verify MongoDB is running
- Check connection string in `.env`
- Ensure network access between containers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open a GitHub issue or contact the development team.

---

**Built for Ubique** - Making e-commerce monitoring effortless
