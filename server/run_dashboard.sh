#!/bin/bash

# Learning Dashboard Launcher
# Minimalistic single-user learning journey dashboard

echo "🎓 Starting Learning Journey Dashboard..."
echo "================================================"
echo ""

# Check if we're in the correct directory
if [ ! -f "dashboard.py" ]; then
    echo "❌ Error: dashboard.py not found!"
    echo "Please run this script from the server directory."
    exit 1
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit not found. Installing..."
    pip install streamlit --break-system-packages -q
fi

# Check if plotly is installed
if ! python -c "import plotly" 2>/dev/null; then
    echo "⚠️  Plotly not found. Installing..."
    pip install plotly --break-system-packages -q
fi

echo "✅ All dependencies ready"
echo ""
echo "📊 Opening dashboard in your browser..."
echo "================================================"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

# Run the dashboard
streamlit run dashboard.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
