# UniScholar Analytics Platform — Academic Research Dashboard

An executive research intelligence dashboard for university faculties. Upload department staff rosters, automatically discover Google Scholar profiles via SerpApi, extract citation metrics ($all$ & $recent$, $h$-index, $i10$-index), resolve candidate disambiguation, and generate formatted institutional reports.

---

## 🌟 Key Features

- **Executive Web Dashboard**: High-aesthetic, responsive dark/light mode dashboard with Chart.js analytics.
- **Automated Column Mapper**: Intelligently identifies faculty names and department columns in Excel (`.xlsx`, `.xls`) and CSV files.
- **Candidate Disambiguation Studio**: When multiple scholars match a name, review all candidates and switch profiles with one click.
- **Department Research Footprint**: Aggregate and compare citation impact, average $h$-index, and leaderboards across disciplines.
- **Smart Quota Caching & Demo Mode**: Avoid redundant paid SerpApi requests with local response caching and zero-credit simulated demo data.
- **Multi-Sheet Excel & CSV Export**: Export formatted executive reports with summary KPIs, full rosters, and verification follow-up lists.

---

## 🚀 Running the Modern Web Dashboard (Recommended)

1. Activate your virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. Start the executive web dashboard:

   ```powershell
   python main.py
   ```

3. Open your browser at **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

---

## 💻 Alternative: Running via Streamlit

If you prefer the companion Streamlit interface:

```powershell
streamlit run app.py
```

---

## 📁 Architecture Overview

```
scholar_dashboard/
├── core/                     # Modular analytics & API engine
│   ├── config.py             # Safe credential & secrets handling
│   ├── parser.py             # Excel/CSV parser & fuzzy column detection
│   ├── scholar_client.py     # SerpApi Google Scholar client & caching
│   ├── analytics.py          # Department aggregation & KPI calculations
│   └── exporter.py           # Multi-sheet Excel and CSV export generator
├── static/                   # Modern Web Dashboard assets
│   ├── index.html            # Dashboard semantic layout & Chart.js containers
│   ├── css/styles.css        # Glassmorphism styling, CSS tokens & themes
│   └── js/app.js             # Real-time state management, filters & modals
├── server.py                 # FastAPI backend server linking UI to core engine
├── main.py                   # Single-command runner for the modern web app
└── app.py                    # Streamlit companion app
```
