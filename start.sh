#!/bin/bash
# FinBot Startup Script
# Quick setup and run script for FinBot

echo "🏦 FinBot Startup Script"
echo "======================="

# Check if virtual environment exists
if [ ! -d "myenv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python -m venv myenv"
    echo "   source myenv/bin/activate  # Linux/Mac"
    echo "   myenv\\Scripts\\activate     # Windows"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your API keys:"
    echo "   OPENAI_API_KEY=your_key_here"
    echo "   SUPABASE_URL=your_url_here"
    echo "   SUPABASE_KEY=your_key_here"
    exit 1
fi

echo "✅ Environment checks passed"

# Function to show menu
show_menu() {
    echo ""
    echo "What would you like to do?"
    echo "1) 🌐 Start Web Interface"
    echo "2) 📊 Check Database Status"
    echo "3) 🕷️ Scrape Sample Data"
    echo "4) 🧹 Clear Database"
    echo "5) ❌ Exit"
    echo ""
    read -p "Enter your choice (1-5): " choice
}

# Main menu loop
while true; do
    show_menu
    case $choice in
        1)
            echo "🌐 Starting FinBot Web Interface..."
            python -m streamlit run main.py
            ;;
        2)
            echo "📊 Checking Database Status..."
            python cli.py db status
            ;;
        3)
            echo "🕷️ Scraping Sample Data..."
            python cli.py scrape --sample --branches 2 --records-per-branch 5
            ;;
        4)
            echo "⚠️  This will delete ALL data!"
            read -p "Are you sure? (y/N): " confirm
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                python cli.py db clear --confirm
            else
                echo "❌ Operation cancelled"
            fi
            ;;
        5)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please try again."
            ;;
    esac
done
