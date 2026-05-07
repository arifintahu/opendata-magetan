# Open Data Magetan

Structured data extracted from [Satu Data Magetan](https://dasatama.magetan.go.id/) — the open data portal of Magetan Regency, East Java, Indonesia. Covers 454 datasets from 32 regional government agencies (OPD) across health, education, population, agriculture, finance, and more.

## Data source

This data is extracted from the official public open data portal of Magetan Regency and is freely available for public use. All datasets are published by the regional government and accessible without authentication on the source portal.

**Portal:** https://dasatama.magetan.go.id/  
**Publisher:** Pemerintah Kabupaten Magetan  
**Coverage:** 32 OPD, 454 datasets, 15 thematic categories

---

## Using the data

All data files are accessible directly via GitHub raw URLs — no scraping or API keys needed.

**Base URL:**
```
https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/
```

### Endpoints

| File | URL |
|---|---|
| All agencies | [`data/agencies.json`](https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/agencies.json) |
| Dataset index | [`data/datasets_index.json`](https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/datasets_index.json) |
| Category list | [`data/categories.json`](https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/categories.json) |
| Single dataset | `data/datasets/{id}.json` |

### Fetch a dataset

```js
const res = await fetch(
  "https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/datasets/16.json"
);
const dataset = await res.json();
```

### Discover datasets via the index

```js
const res = await fetch(
  "https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/datasets_index.json"
);
const { datasets } = await res.json();

// Filter by category
const health = datasets.filter(d => d.category === "health" && d.status === "success");
```

### List agencies

```js
const res = await fetch(
  "https://raw.githubusercontent.com/arifintahu/opendata-magetan/refs/heads/main/data/agencies.json"
);
const { agencies } = await res.json();
```

---

## Data format

### `data/agencies.json`

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

### `data/datasets_index.json`

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
        { "name": "Judul Text-Book", "type": "integer", "years": { "total": 7, "min": 2019, "max": 2025 } }
      ],
      "scraped_at": "2026-05-07T13:00:00Z",
      "status": "success"
    }
  ]
}
```

### `data/datasets/{id}.json`

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

**Categories:** commodity-prices · livestock-fisheries · agriculture-food · health · education · demographics · tourism-culture · investment-sme · macro-economy · infrastructure · housing-settlement · social-labor · environment · disaster-security · governance

---

## Updating the data

Scripts are in `scripts/` and require Python 3.9+.

```bash
pip install -r requirements.txt

python scripts/extract_menu.py       # fetch sidebar → data/directories.json
python scripts/categorize.py         # categorize → data/categories.json
python scripts/scrape_datasets.py    # scrape all datasets → data/datasets/
```

`scrape_datasets.py` is incremental — skips already-downloaded files. Use `--force` to re-scrape everything, `--delay` to adjust request throttling (default 0.3s).
