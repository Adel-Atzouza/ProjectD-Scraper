# ProjectD-Scraper

A powerful web scraping platform with a modern React frontend and FastAPI backend, designed for efficient website crawling and content extraction. The system features real-time progress tracking, duplicate detection, and organized output management.

## 🚀 Features

- **Intelligent Web Crawling**: Automatically discovers and crawls internal URLs from target websites
- **Modern Dashboard**: React + TypeScript frontend with real-time scraping progress
- **Progress Tracking**: Live monitoring of scraping jobs with detailed statistics
- **Duplicate Detection**: SHA-256 hashing to avoid re-scraping unchanged content
- **Batch Processing**: Concurrent crawling with configurable limits
- **Output Management**: Organized data storage by domain and date
- **API-First Design**: RESTful API for all operations
- **Real-time Updates**: WebSocket-like polling for live progress updates

## 🏗️ Architecture

```
ProjectD-Scraper/
├── Project_D_Scraper/
│   ├── Backend/               # FastAPI backend
│   │   ├── main.py           # API endpoints
│   │   ├── CrawlscraperA.py  # Core scraping engine
│   │   ├── utils.py          # Utility functions
│   │   ├── progress/         # Job progress tracking
│   │   └── backend_tests/    # Backend tests
│   ├── Frontned2.0/          # React frontend
│   │   ├── src/              # Source code
│   │   ├── pages/            # Page components
│   │   └── components/       # Reusable components
│   └── tests/                # Integration tests
├── requirements.txt          # Python dependencies
└── .github/workflows/        # CI/CD pipeline
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Crawl4AI** - Advanced web crawling library
- **BeautifulSoup4** - HTML parsing
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Modern CSS** - Responsive design

### Development
- **GitHub Actions** - CI/CD pipeline
- **Playwright** - Browser automation
- **Pytest** - Testing framework
- **ESLint** - Code linting

## 📦 Installation

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm or yarn

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Adel-Atzouza/ProjectD-Scraper.git
   cd ProjectD-Scraper
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **Start the backend server**
   ```bash
   cd Project_D_Scraper/Backend
   py -m uvicorn main:app
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd Project_D_Scraper/Frontned2.0
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```
   The dashboard will be available at `http://localhost:5173`

## 🚀 Usage

### Adding Websites
1. Open the dashboard in your browser
2. Click "Add Website" button
3. Enter the target URL
4. The website will be added to your scraping queue

### Starting a Scrape
1. Select websites from your list
2. Click "Start Scraping"
3. Monitor progress in real-time through the dashboard
4. View detailed statistics and success rates

### Monitoring Progress
- **Active Jobs**: See currently running scraping tasks
- **Progress Bars**: Real-time completion percentage
- **Statistics**: Success rates, failed attempts, total pages
- **Activity Log**: Historical view of all scraping activities

### Accessing Results
- Scraped data is organized by domain and date
- JSON output files contain structured content
- Hash-based duplicate detection prevents redundant processing
- Access via `/output/{date}/{domain}.json` endpoints

## 📊 API Documentation

### Core Endpoints

#### Websites Management
- `GET /websites` - List all registered websites
- `POST /websites` - Add a new website
- `DELETE /websites/{id}` - Remove a website

#### Scraping Operations
- `POST /start-scrape` - Start scraping selected URLs
- `POST /stop-scrape` - Stop all running scraping jobs
- `GET /scrape-progress/{job_id}` - Get progress for specific job

#### Statistics & Monitoring
- `GET /stats` - Get overall scraping statistics
- `GET /activity` - List all scraping activities
- `DELETE /activity/{job_id}` - Remove activity entry

#### Output Management
- `GET /runs` - List available output dates
- `GET /output/{date}` - Get files for specific date
- `GET /output/{date}/{filename}` - Download specific output file

### Example API Usage

```python
import requests

# Add a website
response = requests.post('http://localhost:8000/websites', 
                        json={'url': 'https://example.com'})

# Start scraping
response = requests.post('http://localhost:8000/start-scrape',
                        json={'urls': ['https://example.com']})

# Check progress
job_id = response.json()['jobs'][0]['job_id']
progress = requests.get(f'http://localhost:8000/scrape-progress/{job_id}')
```

## 🧪 Testing

### Running Tests
```bash
# Backend tests
cd Project_D_Scraper/Backend
pytest backend_tests/ --disable-warnings

# Integration tests
cd Project_D_Scraper
pytest tests/ --disable-warnings

# Frontend linting
cd Project_D_Scraper/Frontned2.0
npm run lint
```

### CI/CD Pipeline
The project includes automated testing via GitHub Actions:
- Runs on pushes to `main`, `dev`, and `TestBranch`
- Tests Python code formatting with autopep8
- Executes pytest suite with coverage
- Validates import statements and dependencies

## 🔧 Configuration

### Scraping Settings
- **MAX_CONCURRENT**: Maximum concurrent requests (default: 15)
- **Browser Configuration**: Headless mode enabled
- **Content Filtering**: CSS selectors for main content extraction
- **Exclusions**: File types and irrelevant content filtering

### File Organization
- **Progress Tracking**: `progress/` directory with JSON files
- **Output Storage**: `output/{date}/{domain}.json` structure
- **Hash Storage**: `hashes.json` for duplicate detection
- **Website Database**: `websites.json` for registered URLs
