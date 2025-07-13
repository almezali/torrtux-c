# 🔍 Torrtux


 ████████╗ ██████╗ ██████╗ ██████╗ ████████╗██╗   ██╗██╗  ██╗          
 ╚══██╔══╝██╔═══██╗██╔══██╗██╔══██╗╚══██╔══╝██║   ██║╚██╗██╔╝          
    ██║   ██║   ██║██████╔╝██████╔╝   ██║   ██║   ██║ ╚███╔╝           
    ██║   ██║   ██║██╔══██╗██╔══██╗   ██║   ██║   ██║ ██╔██╗           
    ██║   ╚██████╔╝██║  ██║██║  ██║   ██║   ╚██████╔╝██╔╝ ██╗          
    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝          


                                v1.0.3

**A Professional Multi-Source Torrent Search Tool for Command Line**

*Search, filter, and export torrents from multiple sources with lightning speed* ⚡

---

## 🎯 Overview

**Torrtux** is a powerful, feature-rich torrent search tool designed for power users who demand efficiency and control. With its clean interface and advanced filtering capabilities, Torrtux transforms the way you search for torrents across multiple platforms.

## ✨ Key Features

🔍 **Multi-Source Search** - Query multiple torrent sites simultaneously with intelligent fallback  
⚡ **Lightning Fast** - Parallel processing for optimal search performance  
🎛️ **Advanced Filtering** - Filter by size, seeds, leeches, and content type  
📊 **Multiple Export Formats** - Export results to CSV or JSON  
🔗 **Magnet Link Support** - Extract magnet links with ease  
🎨 **Beautiful Output** - Clean, organized table display with color coding  
📈 **Progress Tracking** - Visual progress indicators and verbose modes  
🌐 **Universal Compatibility** - Works seamlessly across Linux, Windows, and macOS

## 📸 Screenshots

### Search Results Display
![Torrtux Search Results](https://github.com/almezali/torrtux-c/blob/main/01-Screenshot.png)
*Clean, organized table output with color-coded information*

### Advanced Filtering in Action
![Torrtux Advanced Filtering](https://github.com/almezali/torrtux-c/blob/main/02-Screenshot.png)
*Powerful filtering options for precise results*

## 🚀 Installation

### 📦 Arch Linux (AUR)
```bash
yay -S torrtux
```

### 🐍 From Source
```bash
# Clone the repository
git clone https://github.com/almezali/torrtux-c.git
cd torrtux-c

# Install dependencies
pip install -r requirements.txt

# Run Torrtux
python3 torrtux.py "your search query"
```

## 💻 Supported Platforms

| Platform | Status | Notes |
|----------|---------|-------|
| 🐧 **Linux** | ✅ Fully Supported | All major distributions |
| 🪟 **Windows** | ✅ Fully Supported | Python 3.7+ required |
| 🍎 **macOS** | ✅ Fully Supported | Python 3.7+ required |

## 📋 Requirements

- **Python 3.7+**
- **pip** (Python package manager)

### Dependencies
```bash
pip install requests beautifulsoup4 tabulate termcolor tqdm
```

## 🛠️ Usage Examples

### Basic Search
```bash
python3 torrtux.py "ubuntu"
```

### Show Latest Torrents
```bash
python3 torrtux.py --latest
```

### Search Specific Sites
```bash
python3 torrtux.py "game" --sites "1337x,The Pirate Bay"
```

### Export Results
```bash
# Export to CSV
python3 torrtux.py "movie" --export-csv results.csv

# Export to JSON
python3 torrtux.py "movie" --export-json results.json
```

### Advanced Filtering
```bash
# Filter by size and seeds
python3 torrtux.py "linux" --min-size 500MB --max-size 2GB --min-seeds 10

# Show only magnet links
python3 torrtux.py "linux" --magnets-only
```

## ⚙️ Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `-h, --help` | Show help message | `torrtux.py -h` |
| `-p, --pages N` | Number of pages to search | `torrtux.py "query" -p 3` |
| `-l, --limit N` | Maximum results to display | `torrtux.py "query" -l 50` |
| `--sites SITES` | Comma-separated site list | `torrtux.py "query" --sites "1337x,TPB"` |
| `--min-size SIZE` | Minimum torrent size | `torrtux.py "query" --min-size 100MB` |
| `--max-size SIZE` | Maximum torrent size | `torrtux.py "query" --max-size 5GB` |
| `--min-seeds N` | Minimum number of seeds | `torrtux.py "query" --min-seeds 5` |
| `--export-csv FILE` | Export to CSV | `torrtux.py "query" --export-csv out.csv` |
| `--export-json FILE` | Export to JSON | `torrtux.py "query" --export-json out.json` |
| `--magnets-only` | Show only magnet links | `torrtux.py "query" --magnets-only` |
| `--parallel` | Enable parallel search | `torrtux.py "query" --parallel` |
| `--progress` | Show progress indicator | `torrtux.py "query" --progress` |
| `--verbose` | Detailed output | `torrtux.py "query" --verbose` |
| `--quiet` | Suppress extra messages | `torrtux.py "query" --quiet` |

## 🔧 Advanced Configuration

### Size Formats
Torrtux supports various size formats:
- `500MB`, `1.5GB`, `2TB`
- `500M`, `1.5G`, `2T`
- Raw bytes: `524288000`

### Parallel Processing
Enable parallel search for faster results:
```bash
python3 torrtux.py "query" --parallel --progress
```

## 🌍 Platform-Specific Notes

### 🐧 Linux
- Works out of the box on Ubuntu, Debian, Fedora, Arch, and most distributions
- Optimized for terminals with Unicode and color support
- Update CA certificates if encountering SSL issues

### 🪟 Windows
- Compatible with Command Prompt, PowerShell
- Ensure Python 3.7+ is installed from python.org
- Use UTF-8 compatible terminal for best experience

### 🍎 macOS
- Works with system Python or python.org installation
- Use Terminal app for optimal display
- Homebrew Python installation recommended

## 🔒 Legal Notice

This tool is for educational and research purposes only. Users are responsible for complying with local laws and regulations regarding torrent usage. The developers do not encourage or support piracy.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License

---


**Made with ❤️ by the Torrtux Team**

⭐ Star us on GitHub if you find this project useful!

