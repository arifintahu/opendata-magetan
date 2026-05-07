# Open Data Magetan

> Structured, machine-readable data extracted from the official open data portal of Magetan Regency, East Java, Indonesia.

[![Data](https://img.shields.io/badge/datasets-454-blue)](#) [![Agencies](https://img.shields.io/badge/agencies-32-green)](#) [![Categories](https://img.shields.io/badge/categories-15-orange)](#)


This repository republishes data from [Satu Data Magetan](https://dasatama.magetan.go.id/) in a clean, queryable JSON format — covering health, education, population, agriculture, finance, and more. All source data is published by the regional government and freely accessible to the public without authentication.

---

## Quick start

All files are served directly via GitHub raw URLs — no API keys, no scraping.

```js
// Fetch the full dataset index
const res = await fetch(
  "https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/datasets_index.json"
);
const { datasets } = await res.json();

// Filter by category
const health = datasets.filter(d => d.category === "health" && d.status === "success");

// Load a single dataset
const detail = await fetch(
  `https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/datasets/${health[0].id}.json`
).then(r => r.json());
```

---

## Data files

| File | Description |
|---|---|
| [`data/agencies.json`](https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/agencies.json) | All 32 government agencies with their dataset IDs |
| [`data/datasets_index.json`](https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/datasets_index.json) | Index of all 454 datasets with series metadata |
| [`data/categories.json`](https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/categories.json) | Datasets grouped by thematic category |
| `data/datasets/{id}.json` | Full timeseries data for a single dataset |

**Base URL:** `https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/`

---

## Data format

<details>
<summary><strong>agencies.json</strong></summary>

```json
{
  "total": 32,
  "indexed_at": "2026-05-07T13:00:00Z",
  "agencies": [
    {
      "opd_id": 1,
      "name": "Dinas Kearsip dan Perpustakaan",
      "total_datasets": 8,
      "dataset_ids": [16, 17, 18]
    }
  ]
}
```
</details>

<details>
<summary><strong>datasets_index.json</strong></summary>

```json
{
  "total": 454,
  "success": 454,
  "failed": 0,
  "indexed_at": "2026-05-07T13:00:00Z",
  "datasets": [
    {
      "id": 16,
      "title": "Koleksi Buku Perpustakaan",
      "item_title": "Dinas Kearsip dan Perpustakaan",
      "opd_id": 1,
      "category": "education",
      "total_data": 3,
      "series": [
        {
          "name": "Judul Text-Book",
          "type": "integer",
          "years": { "total": 7, "min": 2019, "max": 2025 }
        }
      ],
      "scraped_at": "2026-05-07T13:00:00Z",
      "status": "success"
    }
  ]
}
```
</details>

<details>
<summary><strong>datasets/{id}.json</strong></summary>

```json
{
  "id": 16,
  "title": "Koleksi Buku Perpustakaan",
  "item_title": "Dinas Kearsip dan Perpustakaan",
  "opd_id": 1,
  "category": "education",
  "url": "https://dasatama.magetan.go.id/detail/16",
  "scraped_at": "2026-05-07T13:00:00Z",
  "metadata": {
    "concept": "Buku",
    "classification": "Jenis Buku",
    "measure": "Jumlah",
    "unit": "Judul; Eksemplar",
    "period": "Tahunan",
    "created_at": "2023-08-14 09:54:30",
    "updated_at": "2026-02-24 13:54:18"
  },
  "total_data": 3,
  "data": [
    {
      "name": "Judul Text-Book",
      "type": "integer",
      "years": { "total": 7, "min": 2019, "max": 2025 },
      "values": [
        { "year": 2019, "value": 298 },
        { "year": 2020, "value": 1064 }
      ]
    }
  ]
}
```
</details>

### Categories

`commodity-prices` · `livestock-fisheries` · `agriculture-food` · `health` · `education` · `demographics` · `tourism-culture` · `investment-sme` · `macro-economy` · `infrastructure` · `housing-settlement` · `social-labor` · `environment` · `disaster-security` · `governance`

---

## Data source

| | |
|---|---|
| **Portal** | https://dasatama.magetan.go.id/ |
| **Publisher** | Pemerintah Kabupaten Magetan |
| **Coverage** | 32 OPD, 454 datasets, 15 thematic categories |

Data is sourced from an official public government portal and is freely available without authentication. This repository provides a structured, versioned mirror for easier programmatic access.

---

## Updating the data

Requires Python 3.9+.

```bash
pip install -r requirements.txt

python scripts/extract_menu.py     # fetch agency sidebar → data/directories.json
python scripts/categorize.py       # classify datasets   → data/categories.json
python scripts/scrape_datasets.py  # scrape all datasets → data/datasets/
```

The scraper is incremental — already-downloaded files are skipped. Use `--force` to re-fetch everything or `--delay` to adjust request throttling (default `0.3s`).
