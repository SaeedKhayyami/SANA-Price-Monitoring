<div align="center">

# SANA — Market Price Monitoring

**A Persian desktop application for collecting, exploring, and analyzing historical iron & steel market prices.**

Python · PySide6 · Playwright · SQLite · PyInstaller

</div>

## Overview

SANA is a Windows-oriented desktop price-monitoring application designed to bring market data collection, historical price review, filtering, run management, and lightweight price-change analysis into one interface.

This repository is the **Portfolio Edition** of the project. It intentionally excludes organizational branding, production credentials, private datasets, legacy source archives, and design source files.

## Key Features

- Modern right-to-left Persian desktop UI built with **PySide6**.
- Automated market data collection using **Playwright**.
- Local historical storage with **SQLite**.
- Product filtering by type, size, specification, company/brand, and location.
- Daily, monthly, and seasonal history aggregation.
- Latest-vs-previous price-change analysis.
- Collection-run history with detailed results and run deletion.
- Collector error reporting and diagnostic logs.
- Database selection, backup, and configurable UI font settings.
- Splash screen, login flow, and Windows executable build script.
- Jalali/Persian date presentation for historical views.

## Product Categories

The collector currently supports several common steel-market categories, including rebar, black sheet, beam, profile, channel, and angle products.

## Architecture

```text
SANA-Price-Monitoring/
├── app/
│   ├── main_window.py
│   ├── services/
│   │   ├── collector_runner.py
│   │   ├── database.py
│   │   ├── jalali.py
│   │   └── settings.py
│   └── ui/
│       └── theme.py
├── collector/
│   └── market_collector_v14.py
├── data/
│   └── prices.db
├── resources/
├── docs/screenshots/
├── main.py
├── requirements.txt
├── run.bat
└── build_exe.bat
```

The GUI and the collector are deliberately separated. The desktop app starts the collector as a child process and passes the selected database path through environment variables. This allows the collector implementation to be replaced without tightly coupling it to the UI.

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop UI | PySide6 / Qt |
| Browser automation | Playwright |
| Database | SQLite |
| Image handling | Pillow |
| Packaging | PyInstaller |
| Language | Python 3.11+ |

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/SANA-Price-Monitoring.git
cd SANA-Price-Monitoring
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure local demo login

The public portfolio edition does **not** contain a hard-coded production password. Configure local environment variables before starting the app:

PowerShell:

```powershell
$env:SANA_DEMO_USER="demo"
$env:SANA_DEMO_PASSWORD="your-local-password"
python main.py
```

For a quick Windows demo, `run_demo.bat` supplies disposable demo credentials (`demo / demo1234`) to the local process and launches the application.

## Run on Windows

You can also run:

```text
run.bat
```

after setting `SANA_DEMO_USER` and `SANA_DEMO_PASSWORD` in your environment.

## Build the Windows Application

```text
build_exe.bat
```

The build script packages the GUI and collector with PyInstaller and creates the distributable application under `dist/PriceMonitor/`.

> Note: Playwright browser requirements should be tested on the target Windows environment before distributing a build.

## Screenshots

For portfolio presentation, add sanitized screenshots under `docs/screenshots/`. Recommended views are listed in [`docs/screenshots/README.md`](docs/screenshots/README.md).

## Data & Privacy

The SQLite database included in this portfolio package contains schema only and no production price records. Do not commit real credentials, cookies, customer information, organizational datasets, or private logs.

## Responsible Collection

The collector accesses publicly available market pages. Anyone adapting this project should verify the target website's current Terms of Service, robots policy, rate limits, and applicable rules before running automated collection. Website markup can change, so selectors and parsers may require maintenance over time.

## Portfolio Notes

This public edition was prepared to demonstrate software engineering work such as desktop UI development, process orchestration, browser automation, SQLite data modeling, historical analysis, packaging, and defensive error handling. Organizational logos, internal documents, legacy archives, and private operational data are intentionally excluded.

## Roadmap

Potential future improvements include secure multi-user authentication backed by a server, automated tests, chart-based visualization, CSV/Excel export, configurable collector adapters, and CI checks for code quality and packaging.

---

### فارسی

**سانا** یک نرم‌افزار دسکتاپ فارسی برای جمع‌آوری، نگهداری و بررسی تاریخچه قیمت بازار آهن‌آلات است. نسخه موجود در این Repository نسخه‌ی Portfolio است و اطلاعات ورود واقعی، داده‌های سازمانی و فایل‌های داخلی در آن قرار نگرفته‌اند.
