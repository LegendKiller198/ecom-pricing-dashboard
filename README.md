# E-Commerce Pricing & Market Intelligence — Streamlit App

One app, one deploy. Reads from a real SQLite database populated by the
pipeline in `app/pipeline/` — not a static CSV dump.

Tested locally: runs with zero exceptions, filters/checkboxes verified
interactive and correct (see test output below).

## Run it locally (2 commands)

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Opens automatically at `http://localhost:8501`.

`ecom.db` is already included and pre-seeded (1,416 synthetic rows + 5
hand-verified real listings), so it works immediately — no bootstrap step
needed to just see it running. If you want to rebuild the database (e.g.
after adding a real scraper source), run:

```bash
python3 bootstrap.py
```

## Deploy for real — Streamlit Community Cloud (free, ~3 minutes)

This is the whole process, no other services needed:

1. **Push this folder to a GitHub repo** (public or private):
   ```bash
   git init
   git add -A
   git commit -m "ecom pricing dashboard"
   git remote add origin https://github.com/<you>/ecom-pricing-dashboard.git
   git push -u origin main
   ```

2. **Go to https://share.streamlit.io** and sign in with GitHub.

3. Click **"New app"** → pick your `ecom-pricing-dashboard` repo → set
   **Main file path** to `streamlit_app.py` → click **Deploy**.

4. Wait ~1–2 minutes for the build. You'll get a URL like:
   `https://ecom-pricing-dashboard.streamlit.app`

That's it — no backend to deploy separately, no CORS, no environment
variables to configure, no cold-start sleep issue like Render's free tier.
This URL is what goes on your resume.

## Updating the live data later

If you build a real scraper (see `app/pipeline/html_scraper_template.py` —
same pluggable-source pattern from the backend project), run it locally to
refresh `ecom.db`, then commit and push the updated `ecom.db` file.
Streamlit Cloud auto-redeploys on every push to `main`.

## What's real vs. synthetic

Same as the backend project this was built from:
- **Real, tested**: database schema, validated ingestion pipeline, this
  Streamlit app (verified with Streamlit's `AppTest` — zero exceptions,
  filters/checkboxes confirmed to change the numbers correctly).
- **Real data**: 5 hand-verified listings (see the "Source" column in the
  table for citation + retrieval date).
- **Synthetic**: 1,416 rows generated to mirror realistic cross-platform
  discount patterns, used for the historical trend view.
- **Not yet live**: the scraper template — structurally correct but needs
  a live target and real network access (not available in the dev sandbox
  this was built in) to actually pull fresh prices.

## Local test output (for reference)

```
App ran with NO exceptions
Metrics:
 - Listings tracked = 123
 - Avg discount = 31.8%
 - Deepest discount platform = Myntra (41.1% avg off)
 - Verified real listings = 5

Filter → Electronics category: Listings tracked = 32, correctly recalculated
Filter → Verified-only checkbox: Listings tracked = 4, Amazon.in deepest (80.0%)
```
