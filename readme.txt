# YouTube Bulk Description Updater

YouTube Studio doesn't have find-and-replace. 
This script let's you do that.

---

## Features

- Find and replace any text across all video descriptions
- Supports multiple find/replace pairs in one run
- Dry-run mode to preview changes before applying them
- Skips videos that don't match — saves API quota
- Handles channels with 500+ videos via pagination

---

## Requirements

- Python 3.8+
- A Google Cloud project with YouTube Data API v3 enabled
- OAuth 2.0 Desktop credentials (`client_secrets.json`)

---

## Roadmap / Future Plans

- A webpage textbox workflow
- Preview, select, and toggle which videos to update.

---

## Setup

### 1. Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **YouTube Data API v3** — [direct link](https://console.cloud.google.com/apis/library/youtube.googleapis.com)
4. Go to **Credentials** → **Create Credentials** → **OAuth client ID**
   - Configure consent screen if prompted (External, add your email as a test user)
   - Application type: **Desktop app**
5. Download the JSON file and rename it to `client_secrets.json`
6. Place `client_secrets.json` in the same folder as the script

### 2. Install dependencies

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 3. Configure your replacements

Open `update_descriptions.py` and edit the `REPLACEMENTS` list:

```python
REPLACEMENTS = [
    ("https://old-link.com",  "https://new-link.com"),
    ("@oldhandle",            "@newhandle"),
]
```

Add as many pairs as you need.

---

## Usage

### Dry run first (recommended)

At the top of the script, `DRY_RUN = True` by default. Run it as-is to preview what would change:

```bash
python update_descriptions.py
```

It will print every video that would be updated and exactly what would be replaced — nothing is written to YouTube.

### Apply changes

When the preview looks correct, open the script and set:

```python
DRY_RUN = False
```

Run again. The script will update every matching video.

---

## API Quota

YouTube's free quota is **10,000 units/day**. Each video update costs ~50 units, so you can update roughly 200 videos per day. If you have more, run the script on consecutive days — already-updated videos will be skipped automatically.

---

## Security

- Never commit `client_secrets.json` or `token.pickle` to version control
- A `.gitignore` is included in this repo to prevent this
- Each user must set up their own Google Cloud credentials — do not share yours

---

## License


MIT
