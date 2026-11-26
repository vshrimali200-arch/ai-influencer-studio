# AI Influencer Studio — Free MVP

A local-first dashboard for managing an original fictional AI creator, drafting posts, storing media, planning a content calendar, and assembling a basic vertical slideshow Reel.

## Requirements
- Python 3.10+
- Optional: FFmpeg (for Reel export)

## Run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local address shown by Streamlit (usually http://localhost:8501).

## Notes
- This is a free starter dashboard, not a hosted service.
- It does not generate AI images/videos on its own. Upload assets made with tools you are permitted to use.
- Instagram auto-publishing is not included. Use manual publishing or add Meta's official API after confirming account eligibility and app setup.
- Data is stored in `data/studio.db` and uploaded media in `data/media/`. Back up the whole `data` folder.
