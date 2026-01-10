#!/bin/bash
# Start Reasoning Core web server

echo "🧠 Starting Reasoning Core Web Server..."
echo ""

# Try python3 first, fall back to python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.9+ first."
    exit 1
fi

# Check if dependencies are installed
$PYTHON_CMD -c "import fastapi" 2>/dev/null || {
    echo "❌ FastAPI not installed. Installing web dependencies..."
    if command -v pip3 &> /dev/null; then
        pip3 install -r requirements-web.txt
    else
        pip install -r requirements-web.txt
    fi
}

# Start the server
echo "🚀 Starting server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo "🌐 Web UI: http://localhost:3000 (run 'cd web && npm run dev' in another terminal)"
echo ""
$PYTHON_CMD -m reasoning_core.web.server
