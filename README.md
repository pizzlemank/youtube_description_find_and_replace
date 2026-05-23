# POD Merch Tools

Tools for automating and identifying Print-on-Demand (POD) opportunities.

## Tools

### 1. YouTube Bulk Description Updater
A script to find and replace text across all video descriptions in a YouTube channel.
- **File:** `YT_bulk_update_description.py`
- **Setup:** See `readme.txt` for details.

### 2. Google Trends Merch Crawler
A script that crawls Google Trends to identify rising long-tail keywords for t-shirts and other apparel.
- **File:** `crawl_trends.py`
- **Output:** Updates `trends.md` with new findings.
- **Automation:** Configured to run daily via GitHub Actions.

## Requirements
Install dependencies using:
```bash
pip install -r requirements.txt
```

## Trends Data
The latest trends are documented in [trends.md](trends.md), sorted from newest to oldest. Potential IP infringing designs are flagged in a separate section for review.
