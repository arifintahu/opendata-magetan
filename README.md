# opendata-magetan

Data extraction scripts for [Satu Data Magetan](https://dasatama.magetan.go.id/) — the open data portal of Magetan Regency, East Java, Indonesia. The portal publishes datasets from 32 regional government agencies (OPD) covering health, education, population, agriculture, finance, and more.

This repo provides structured, machine-readable versions of that data for analysis, integration, or archival purposes.

## Data source

**Portal:** https://dasatama.magetan.go.id/  
**Publisher:** Pemerintah Kabupaten Magetan  
**Coverage:** 32 OPD (Organisasi Perangkat Daerah), 454 dataset categories

## Scripts

| Script | Description | Output |
|---|---|---|
| `scripts/extract_menu.py` | Extracts the sidebar directory of all agencies and their dataset links | `data/directories.json` |
| `scripts/categorize.py` | Categorizes all datasets into 15 thematic sectors using keyword rules | `data/categories.json` |

Run in order — `categorize.py` reads the output of `extract_menu.py`.

## Prerequisites

Python 3.9+

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python scripts/extract_menu.py
python scripts/categorize.py
```

The `data/` directory is created automatically on first run.

## Output format

### `data/directories.json`

```json
{
  "total_items": 32,
  "items": [
    {
      "title": "Dinas Kearsip dan Perpustakaan",
      "total_sub_items": 8,
      "sub_items": [
        {
          "id": "16",
          "title": "Koleksi Buku Perpustakaan",
          "url": "https://dasatama.magetan.go.id/detail/16"
        }
      ]
    }
  ]
}
```

### `data/categories.json`

```json
{
  "total_categories": 15,
  "categories": [
    {
      "name": "health",
      "description": "Kesehatan",
      "sub_items": [
        {
          "id": "33",
          "title": "Kunjungan Pasien di Puskesmas",
          "item_title": "Dinas Kesehatan"
        }
      ]
    }
  ]
}
```

**Categories:** commodity-prices · livestock-fisheries · agriculture-food · health · education · demographics · tourism-culture · investment-sme · macro-economy · infrastructure · housing-settlement · social-labor · environment · disaster-security · governance

## Re-running

Scripts are idempotent — safe to run any number of times. Each run fetches fresh data and overwrites the output files atomically.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `Could not locate sidebar navigation` | Page HTML structure changed — inspect the live page and update `find_sidebar_ul()` selectors |
| Network errors / timeouts | Transient; the script retries 3 times automatically |
| Garbled Indonesian characters | Encoding mismatch; `apparent_encoding` handles this automatically |
| Items in wrong category | Adjust keyword rules in `CATEGORIES` inside `scripts/categorize.py` |
