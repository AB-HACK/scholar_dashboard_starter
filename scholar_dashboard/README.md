# University Research Analytics Dashboard

A Streamlit starter app for uploading department staff lists, discovering candidate Google Scholar profiles through SerpApi, retrieving profile metrics, and exporting CSV/Excel reports.

## Important limitations

- Google Scholar does not offer an official public API for bulk profile and citation-metric retrieval.
- This app uses SerpApi as a third-party provider. Check its current pricing, quotas, data terms, and Google Scholar-related terms before use.
- Profile discovery is not identity proof. Results are deliberately marked `Needs verification`; check the profile name, affiliation, and publications before using results in official reports.
- Metrics may be missing for profiles that are private, unavailable, or not indexed.

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Create and activate a virtual environment (optional but recommended):

   Windows PowerShell:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Start the app:

   ```powershell
   streamlit run app.py
   ```

6. Add your SerpApi key in the sidebar, upload the staff Excel file, and click **Discover profiles and collect metrics**.

You can alternatively set `SERPAPI_API_KEY` as an environment variable before starting the app.

## Expected input

An Excel or CSV file with a staff-name column and preferably a department column. Column names such as `Names`, `Staff Name`, `Full Name`, `Department`, and `Dept` are detected automatically.

## Next improvements

- Add a review screen to select the correct candidate when multiple profiles are returned.
- Persist verified profile IDs and past snapshots in SQLite.
- Add charts and department summary KPIs.
- Add retries, provider quota tracking, and caching.
- Compare results against manually verified Google Scholar profile values before formal reporting.
