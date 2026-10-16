# GDACS Earthwatch dashboard

Run from this folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe dashboard.py
```

Open **http://127.0.0.1:8050**. Stop the server with Ctrl+C.

No Python dependencies or API keys are needed. Internet access is needed for Leaflet, Plotly, and OpenStreetMap tiles (no API key required). Event data is read by the local server and served to your browser; it is not uploaded to a hosted dashboard.

The default dataset is `.venv/data/gdacs_global_events_2024-10-16_to_2026-10-16.csv`. To use another file or port:

```powershell
.\.venv\Scripts\python.exe dashboard.py --data "path\to\events.csv" --port 8051
```

Features: interactive world map with event popups, monthly stacked timeline, hazard/alert comparison, country rankings, date/type/alert/country/text filters, paginated source-linked records, and filtered CSV export. All views share the filters.

Date filters are inclusive UTC calendar dates. The default shows events whose reported start/end interval overlaps 2024-10-16 through 2026-10-16. Choose **Starts in period** to exclude earlier starts. The timeline counts starts, not active events per month. The archive contains events starting before its filename range. Multi-country events count once per affected country in country rankings, so country totals can exceed unique events. Severity measures have different units across hazards; the dashboard does not combine them. Counts describe this archive, not all disasters or present conditions. The server reads the CSV at startup; restart after replacing the data.

Your existing notebook and `natural_disasters.py` are preserved. Keep a backup of the dataset outside `.venv` before recreating the environment.
