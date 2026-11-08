# AI Workforce Investment Planner - Streamlit

This deployment package publishes the AI Workforce Investment Planner with Streamlit Community Cloud. The Streamlit launcher loads the self-contained dashboard and preserves its filters, charts, maps, tables, and CSV downloads.

## Application Architecture

- **Application type:** Streamlit app with an embedded browser-based HTML/JavaScript dashboard
- **Entrypoint:** `streamlit_app.py`
- **Data source:** Public data bundled inside `AI_Workforce_Investment_Planner.html`
- **Runtime behavior:** Filtering, chart updates, maps, and downloads run in the embedded browser component
- **Server-side secrets:** None required
- **External database:** None required

The app uses a project-relative path to load the HTML file from the same directory. It does not depend on an absolute path or a hard-coded localhost URL.

## Exact Streamlit Community Cloud Settings

| Setting | Value |
| --- | --- |
| Repository | `Hardcore-LEO/dso576-project` |
| Branch | `main` |
| Main file path | `dashboard_final/AI_Workforce_Streamlit/streamlit_app.py` |
| Python version | `3.12` |
| Dependency file | `dashboard_final/AI_Workforce_Streamlit/requirements.txt` |
| Streamlit version | `1.67.0` |

## Required Deployment Files

- `streamlit_app.py` - Starts the Streamlit application and embeds the dashboard.
- `AI_Workforce_Investment_Planner.html` - Contains the dashboard interface, JavaScript interactions, charts, and public data.
- `requirements.txt` - Pins the Streamlit dependency for reproducible deployment.
- `generate_ai_workforce_planner.py` - Copies the canonical standalone dashboard to a requested output path.

Keep these files together in this directory when deploying.

## Run Locally

Run the following commands from the repository root.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r dashboard_final/AI_Workforce_Streamlit/requirements.txt
python -m streamlit run dashboard_final/AI_Workforce_Streamlit/streamlit_app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r dashboard_final/AI_Workforce_Streamlit/requirements.txt
python -m streamlit run dashboard_final/AI_Workforce_Streamlit/streamlit_app.py
```

The local application is normally available at `http://localhost:8501`.

## Deploy

1. Review the local changes and confirm that the required deployment files are included.
2. Commit and push the reviewed files to the `main` branch of `Hardcore-LEO/dso576-project`.
3. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub.
4. Select **Create app**, then **Yup, I have an app**.
5. Select repository `Hardcore-LEO/dso576-project` and branch `main`.
6. Enter `dashboard_final/AI_Workforce_Streamlit/streamlit_app.py` as the main file path.
7. In **Advanced settings**, select Python `3.12`. No secrets are required for this app.
8. Select **Deploy** and wait for the app to finish building.

## Verification Checklist

### Before committing

- Start the app locally without an import or missing-file error.
- Apply at least one filter and confirm that the displayed results update.
- Confirm that at least one chart renders and responds to the filter.
- Confirm that downloads, if used, still work.
- Review the Git diff and keep `.streamlit/secrets.toml`, `.env`, virtual environments, and cache files out of GitHub.

### After deployment

- Open the `.streamlit.app` URL in an incognito window.
- Test two filter selections and compare the results with the local app.
- Confirm that a chart and any required download work.
- Open the public URL on another device.
- Add the verified public URL to this README.

## Regenerate a Standalone Copy

From this directory, run:

```bash
python generate_ai_workforce_planner.py "AI_Workforce_Investment_Planner_copy.html"
```

The generator uses only the Python standard library.

## Official Documentation

- [Streamlit installation](https://docs.streamlit.io/get-started/installation)
- [Streamlit Community Cloud deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
