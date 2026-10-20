# RoadWatch AI — Smart Pothole Detection & Road Damage Reporting

A local Flask web application for submitting road-damage reports, storing them in SQLite, tracking repair status, viewing mapped reports, analysing trends and exporting data.

## Features
- Responsive overview dashboard and report counters
- Road-image upload with file type and size validation
- GPS coordinates or manually entered location
- Report detail page and repair-status workflow (Pending / In Progress / Resolved)
- Damage map using Leaflet/OpenStreetMap (internet required for map tiles)
- Search reports by title, description or damage type
- Filter reports by status and severity
- Analytics page: status distribution, severity distribution, damage categories, monthly trend, resolution rate and open high-risk count
- Export filtered or all report records to CSV for Excel
- Print analytics page to PDF using the browser's Print dialog
- SQLite database created automatically on first run; starts empty so graphs are based on submitted reports, not fabricated sample records
- Optional YOLO integration when a compatible trained model is supplied

## Run on Windows / VS Code
1. Extract the ZIP file.
2. Open the extracted `RoadWatch_AI_Project` folder in VS Code.
3. Open **Terminal → New Terminal**. Confirm the terminal path ends with `RoadWatch_AI_Project`.
4. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
5. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt terminal and run `.venv\Scripts\activate.bat`, or run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then activate again.
6. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
7. Start the app:
   ```powershell
   python app.py
   ```
8. Open `http://127.0.0.1:5000` in Chrome.
9. Stop the server with `Ctrl+C` in the terminal.

## Important AI note
Without `models/pothole.pt`, image analysis runs in clearly labelled demo mode; it is not a real model prediction. To enable AI inference, add a pothole/road-damage YOLO model compatible with your installed Ultralytics version at `models/pothole.pt`, install `requirements-ai.txt`, and test against labelled images. A trained model is not bundled. Never present demo confidence as measured accuracy.

## Data and privacy
Reports and uploaded images are stored locally in `roadwatch.db` and `static/uploads/`. Back up these files before deleting or moving the project. This is a hackathon prototype, not a production-secured public service; add authentication, authorization, CSRF protection and deployment hardening before public deployment.
