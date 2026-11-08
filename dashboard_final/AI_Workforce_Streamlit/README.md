# AI Workforce Investment Planner — Streamlit Deployment

This folder is the current, self-contained deployment package for the AI Workforce Investment Planner. The Streamlit launcher loads the bundled dashboard and preserves its filters, charts, maps, tables, and CSV downloads.

> **Use this folder for deployment.** The recommended Streamlit Community Cloud entrypoint is `dashboard_final/AI_Workforce_Streamlit/streamlit_app.py`.

## Quick Start

From the repository root:

```powershell
python -m pip install -r dashboard_final/AI_Workforce_Streamlit/requirements.txt
python -m streamlit run dashboard_final/AI_Workforce_Streamlit/streamlit_app.py
```

The application normally opens at `http://localhost:8501`.

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

The HTML file is intentionally committed with the deployment package because it contains the dashboard interface, public data, and browser-side interactions required at runtime.

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

## Deploy

1. Review the local changes and confirm that the required deployment files are included.
2. Commit and push the reviewed files to the `main` branch of `Hardcore-LEO/dso576-project`.
3. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub.
4. Select **Create app**, then **Yup, I have an app**.
5. Select repository `Hardcore-LEO/dso576-project` and branch `main`.
6. Enter `dashboard_final/AI_Workforce_Streamlit/streamlit_app.py` as the main file path.
7. In **Advanced settings**, select Python `3.12`. No secrets are required for this app.
8. Select **Deploy** and wait for the app to finish building.

After deployment, add the verified public `.streamlit.app` URL here:

```text
Public app URL: not published yet
```

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

## Updating This Deployment Package

Treat this directory as one unit. When the dashboard changes:

1. Replace `AI_Workforce_Investment_Planner.html` with the latest generated dashboard.
2. Keep `streamlit_app.py` and `requirements.txt` in this same directory.
3. Run the app locally and complete the verification checklist above.
4. Review the Git diff before committing so the deployment package and its documentation change together.

The similarly named files directly under `dashboard_final/` are not the recommended Community Cloud entrypoint. Do not combine the two copies when configuring the deployment.

## Official Documentation

- [Streamlit installation](https://docs.streamlit.io/get-started/installation)
- [Streamlit Community Cloud deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
