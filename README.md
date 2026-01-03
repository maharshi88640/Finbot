# 🏦 FinBot - Financial Document Assistant

An AI-powered assistant for querying and analyzing financial documents from the Gujarat Finance Department.

## 🚀 Features

- **💬 AI Chat Interface** - Natural language queries about financial documents
- **🔍 Advanced Search** - Filter by branch, date, GR number, and content
- **📄 PDF Processing** - Automatic text extraction and summarization
- **🕷️ Web Scraping** - Automated data collection from government websites
- **🌐 Multi-language Support** - English and Gujarati
- **⚡ Vector Search** - Semantic similarity search using embeddings

## 📁 Project Structure

```
FinBot/
├── src/                          # Source code modules
│   ├── config/                   # Configuration and clients
│   │   └── __init__.py          # Config and client management
│   ├── core/                     # Core business logic
│   │   ├── database.py          # Database operations
│   │   └── ai.py                # AI and OpenAI operations
│   ├── scraper/                  # Web scraping module
│   │   └── __init__.py          # Scraping functionality
│   └── chat/                     # Chat interface logic
│       └── __init__.py          # Chat and tool calling
├── utilities/                    # Utility scripts
├── deprecated/                   # Old/deprecated files
├── archive/                      # Database backups and setup files
├── main.py                       # Main Streamlit application
├── cli.py                        # Command-line interface
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
└── README.md                     # This file
```

## 🛠️ Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd FinBot
   ```

2. **Create virtual environment**

   ```bash
   python -m venv myenv
   # Windows
   myenv\Scripts\activate
   # Linux/Mac
   source myenv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install numpy  # Install NumPy first
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Set up Supabase database**
   - Create a new Supabase project
   - Run the SQL from `archive/restore_finbot_db.sql` in SQL Editor
   - Enable the `vector` extension
   - Update `.env` with your Supabase credentials

## 🚀 Quick Start

### Web Interface

```bash
python -m streamlit run main.py
```

### Command Line Interface

```bash
# Check database status
python cli.py db status

# Scrape sample data
python cli.py scrape --sample --branches 2 --records-per-branch 10

# Full scraping
python cli.py scrape --branches 5 --records-per-branch 100
```

## 📋 Environment Variables

Create a `.env` file with:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_anon_key_here
```

## 🔧 Configuration

The application can be configured through `src/config/__init__.py`:

- **AI Models**: Change OpenAI models used
- **Chunk Settings**: Adjust text chunking for embeddings
- **Scraping Settings**: Modify scraping behavior
- **Database Settings**: Configure batch sizes

## 📊 Usage Examples

### Chat Interface

1. Open the web app: `http://localhost:8501`
2. Ask questions like:
   - "Show me documents about employee bonuses"
   - "Find all documents from March 2024"
   - "What is document પગર-૧૦૨૦૨૩-૦૧-મ about?"

### CLI Operations

```bash
# Get database statistics
python cli.py db status

# Scrape new data
python cli.py scrape --sample

# Clear database (careful!)
python cli.py db clear
```

## 🧩 Modules

### Core Modules

- **`src/config/`** - Configuration management and API clients
- **`src/core/database.py`** - All database operations and queries
- **`src/core/ai.py`** - OpenAI integration and AI operations

### Feature Modules

- **`src/scraper/`** - Web scraping from government websites
- **`src/chat/`** - Chat interface and function calling

### Applications

- **`main.py`** - Streamlit web interface
- **`cli.py`** - Command-line tools

## 🔒 Security

- Environment variables for API keys
- `.gitignore` configured to exclude sensitive files
- Row Level Security (RLS) enabled on database tables

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're running from the project root
2. **Database connection**: Verify your Supabase credentials
3. **Scraping fails**: Check if ChromeDriver is installed
4. **Memory issues**: Reduce batch sizes in config

### Debug Mode

Set environment variable for detailed logging:

```bash
export FINBOT_DEBUG=1
```

## 📈 Performance

- **Database**: Uses indexes for fast queries
- **AI**: Configurable chunk sizes for optimal token usage
- **Scraping**: Batch processing for memory efficiency
- **Vector Search**: Optimized similarity search with thresholds

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Review the configuration options
3. Check logs in the sidebar of the web interface
