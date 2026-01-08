# Reasoning Core Web UI

Web interface for Reasoning Core - upload documents, analyze websites, or paste text to extract knowledge graphs.

## Setup

### Backend (FastAPI)

1. Install dependencies:
```bash
cd /path/to/reasoning-core
pip install -e ".[web]"
```

Or install manually:
```bash
pip install fastapi uvicorn python-multipart requests beautifulsoup4 PyPDF2 python-docx
```

2. Run the server:
```bash
python -m reasoning_core.web.server
# Or
uvicorn reasoning_core.web.server:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend (React + Vite)

1. Install dependencies:
```bash
cd web
npm install
```

2. Run development server:
```bash
npm run dev
```

The UI will be available at `http://localhost:3000`

3. Build for production:
```bash
npm run build
```

## Features

- **File Upload**: Upload PDF, DOCX, TXT, HTML, or Markdown files
- **Website Analysis**: Enter a URL to scrape and analyze website content
- **Text Input**: Paste or type text directly for analysis
- **Domain Selection**: Choose domain type (Medical, Business, Meeting, Generic)
- **Knowledge Graph Visualization**: Interactive graph viewer using Cytoscape
- **Real-time Results**: View concepts, relationships, reasoning chains, and questions

## API Endpoints

- `POST /api/analyze/text` - Analyze text directly
- `POST /api/analyze/file` - Upload and analyze document
- `POST /api/analyze/url` - Scrape and analyze website
- `GET /api/results/{task_id}` - Get analysis results
- `GET /api/health` - Health check

## Usage Example

```javascript
// Analyze text
const response = await fetch('/api/analyze/text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Patient has fever and cough',
    domain: 'medical'
  })
})

const { task_id } = await response.json()

// Get results
const results = await fetch(`/api/results/${task_id}`)
const data = await results.json()
```

## Development

The frontend proxies API requests to the backend running on port 8000 (configured in `vite.config.js`).

Make sure both servers are running:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
