# opendata-magetan

Data extraction scripts for [Satu Data Magetan](https://dasatama.magetan.go.id/) — the open data portal of Magetan Regency, East Java, Indonesia. The portal publishes datasets from 32 regional government agencies (OPD) covering health, education, population, agriculture, finance, and more.

This repo provides structured, machine-readable versions of that data for analysis, integration, or archival purposes.

## Data source

**Portal:** https://dasatama.magetan.go.id/  
**Publisher:** Pemerintah Kabupaten Magetan  
**Coverage:** 32 OPD (Organisasi Perangkat Daerah), 454 datasets

## Scripts

| Script | Description | Output |
|---|---|---|
| `scripts/extract_menu.py` | Extracts the sidebar directory of all agencies and their dataset links | `data/directories.json` |
| `scripts/categorize.py` | Categorizes all datasets into 15 thematic sectors using keyword rules | `data/categories.json` |
| `scripts/scrape_datasets.py` | Fetches timeseries data and metadata for every dataset via the portal API | `data/datasets/{id}.json`, `data/datasets_index.json` |

Run in order — each script reads the output of the previous one.

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
python scripts/scrape_datasets.py
```

Optional flags for `scrape_datasets.py`:

```bash
python scripts/scrape_datasets.py --delay 0.5   # seconds between requests (default: 0.3)
python scripts/scrape_datasets.py --force        # re-scrape already downloaded datasets
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
      "total_category_sub_items": 61,
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

### `data/datasets/{id}.json`

One file per dataset. Data columns are normalized to named timeseries arrays.

```json
{
  "id": "16",
  "title": "Koleksi Buku Perpustakaan",
  "item_title": "Dinas Kearsip dan Perpustakaan",
  "opd_id": 1,
  "category": "education",
  "url": "https://dasatama.magetan.go.id/detail/16",
  "scraped_at": "2026-05-07T10:00:00",
  "metadata": {
    "concept":        "Buku",
    "classification": "Jenis Buku",
    "measure":        "Jumlah",
    "unit":           "Judul; Eksemplar",
    "period":         "Tahunan",
    "created_at":     "2023-08-14 09:54:30",
    "updated_at":     "2026-02-24 13:54:18"
  },
  "year_range": { "min": 2019, "max": 2025 },
  "total_periods": 7,
  "data": [
    {
      "name": "Judul Text-Book",
      "type": "integer",
      "values": [
        { "year": 2019, "value": 298 },
        { "year": 2020, "value": 1064 }
      ]
    }
  ]
}
```

### `data/datasets_index.json`

Aggregated index of all datasets built from disk after scraping.

```json
{
  "total": 454,
  "success": 451,
  "failed": 3,
  "indexed_at": "2026-05-07T10:00:00",
  "datasets": [
    {
      "id": "16",
      "title": "Koleksi Buku Perpustakaan",
      "item_title": "Dinas Kearsip dan Perpustakaan",
      "opd_id": 1,
      "category": "education",
      "year_range": { "min": 2019, "max": 2025 },
      "total_periods": 7,
      "series": [
        { "name": "Judul Text-Book",        "type": "integer" },
        { "name": "Judul E-Book",           "type": "integer" },
        { "name": "Jumlah Text-Book (Eks)", "type": "integer" }
      ],
      "scraped_at": "2026-05-07T10:00:00",
      "status": "success"
    },
    {
      "id": "99",
      "title": "Some Dataset",
      "item_title": "Some Agency",
      "status": "failed",
      "error": "HTTP 500"
    }
  ]
}
```

## Re-running

All scripts are idempotent — safe to run any number of times. `scrape_datasets.py` skips already-downloaded dataset files unless `--force` is passed.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `Could not locate sidebar navigation` | Page HTML structure changed — inspect the live page and update `find_sidebar_ul()` selectors |
| Network errors / timeouts | Transient; the script retries 3 times automatically |
| Garbled Indonesian characters | Encoding mismatch; `apparent_encoding` handles this automatically |
| Items in wrong category | Adjust keyword rules in `CATEGORIES` inside `scripts/categorize.py` |
| Dataset shows `"status": "failed"` in index | Check the `error` field; common causes are HTTP 404/500 or malformed API responses |
