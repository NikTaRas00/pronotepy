# Pronote Viewer

A small Flask app using [pronotepy](https://github.com/bain3/pronotepy) to show your grades more nicely: per-subject averages (with class average, min, max and every grade) and a **main average** computed as the mean of your subject averages. Pronote's own overall average is shown next to it.

## Run locally
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # fill it in, then set the vars in your shell
python app.py
```
(`app.py` reads real environment variables; use your host's env settings, or `set VAR=value` locally.)

## Deploy
This needs a **Python host** (pronotepy talks to Pronote server-side), so GitHub Pages / plain static hosting won't work. Any host that deploys from GitHub and runs Python works (Render, Railway, Fly.io, PythonAnywhere, cPanel "Setup Python App"...):

- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app` (see `Procfile`)
- Set env vars: `PRONOTE_URL`, `PRONOTE_USERNAME`, `PRONOTE_PASSWORD`, `APP_PASSWORD` (and `PRONOTE_ENT` if needed)
- Point your custom domain at the host and enable HTTPS.

The site is protected by HTTP basic auth using `APP_PASSWORD` (any username), since it's on a public domain.

## Notes
- Data is cached for `CACHE_SECONDS` (default 300) to avoid logging into Pronote on every page load.
- The main average is an unweighted mean of subject averages; edit `calculated` in `app.py` if you want coefficients.
