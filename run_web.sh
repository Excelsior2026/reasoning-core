#!/bin/bash
# Start Reasoning Core web server

echo "🧠 Starting Reasoning Core Web Server..."
echo ""

# Check if dependencies are installed
python -c "import fastapi" 2>/dev/null || {
    echo "❌ FastAPI not installed. Installing web dependencies..."
    pip install -r requirements-web.txt
}

# Start the server
echo "🚀 Starting server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
python -m reasoning_core.web.server
