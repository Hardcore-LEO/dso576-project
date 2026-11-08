# AI Workforce Investment Planner — Streamlit

An interactive workforce investment planning dashboard delivered as a Streamlit app. The app embeds a self-contained HTML, JavaScript, CSS, and data bundle inside a scrollable Streamlit component.

## Requirements

- Python 3.12 recommended (the current Streamlit Community Cloud default)
- Streamlit 1.67.0, the latest stable release as of November 8, 2026

The Streamlit version is pinned in `requirements.txt` to keep local and cloud deployments reproducible.

## Run Locally

From this directory, create and activate a virtual environment, install the dependency, and start the app.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit will print the local app URL in the terminal, typically `http://localhost:8501`.

## Deploy to Streamlit Community Cloud

1. Upload this directory to a GitHub repository. Keep `app.py`, `generate_ai_workforce_planner.py`, and `requirements.txt` together.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and select **Create app**.
3. Select the repository and branch containing the project.
4. Set the entrypoint file path to this directory's `app.py`. For example:

   ```text
   project/dashboard_final/AI_Workforce_Streamlit/app.py
   ```

5. In **Advanced settings**, select Python 3.12.
6. Select **Deploy**.

Upload the extracted project files to GitHub rather than uploading a ZIP archive. If this directory is moved, update the entrypoint path to match its new repository location.

## Project Files

- `app.py` — Streamlit entrypoint that renders the planner in an embedded, scrollable component.
- `generate_ai_workforce_planner.py` — Contains the complete HTML, JavaScript, CSS, and dataset as embedded bytes. It can also regenerate a standalone HTML file.
- `requirements.txt` — Pins the Streamlit version used for local and cloud deployments.
- `AI_Workforce_Investment_Planner (4).html` — Standalone HTML export of the planner; it is not required by `app.py`.

## Regenerate the Standalone HTML

```bash
python generate_ai_workforce_planner.py "AI_Workforce_Investment_Planner.html"
```

The generator uses only the Python standard library.

## Data and Browser Behavior

The planner's interactions run inside the embedded browser component. Data saved by the browser remains local to that browser and is not automatically synchronized with the Streamlit server or other users.

## Official Documentation

- [Install Streamlit](https://docs.streamlit.io/get-started/installation)
- [Deploy an app on Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit release notes](https://docs.streamlit.io/develop/quick-reference/release-notes)
