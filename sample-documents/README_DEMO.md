# Demo Guide — Shopify Bulk Product Importer

> **AI-Powered Turkish Product Description Generator**
> Automatically clean, enrich, and export supplier CSV data to Shopify using Claude Haiku AI.

---

## Overview

This demo package showcases a production-grade pipeline that:

1. Reads a messy Turkish supplier CSV file (25 sample products)
2. Cleans and normalizes product data (names, colors, categories, sizes)
3. Detects and reports data errors (duplicates, missing prices, invalid values)
4. Generates SEO-optimized Turkish HTML descriptions via Claude Haiku
5. Exports a Shopify-compatible CSV ready for direct import
6. Produces a structured error report in JSON format

The entire pipeline runs via n8n → FastAPI → Claude API → Shopify CSV, and can be deployed with a single `docker compose up` command.

---

## Folder Structure

```
sample-documents/
├── supplier_sample.csv        # 25 raw supplier products (intentionally messy)
├── shopify_output_sample.csv  # 21 cleaned + AI-enriched Shopify-ready products
├── error_report.json          # 10 errors/warnings from the cleaning stage
├── sample_api_request.json    # Example POST /generate-description payload
├── sample_api_response.json   # Example API response with AI-generated description
├── workflow_overview.md       # Full pipeline documentation with Mermaid flowchart
└── README_DEMO.md             # This file
```

---

## Input CSV Example

The supplier CSV contains intentionally messy real-world data. Below is a representative sample:

| Stok Kodu | Ürün Adı | Kategori | Marka | Fiyat | Stok | Renk | Boyut |
|-----------|----------|----------|-------|-------|------|------|-------|
| TXT001 | pamuklu yatak örtüsü 200x220 | yatak odası | Taç | 450.00 | 50 | beyaz | 200x220 cm |
| TXT002 | akrilik hali 160x230 | salon | *(missing)* | 890.00 | 15 | mavi | 160x230 |
| TXT006 | yastik 50x70 beyaz | yastık | Özdilek | 85.00 | 100 | **beya** | 50x70 |
| TXT001 | pamuklu yatak ortusu | yatak odası | Taç | 450.00 | 50 | beyaz | 200x220 |
| TXT011 | keten perde beyaz | oturma odası | Özdilek | *(missing)* | 25 | beyaz | 140x240 |
| TXT016 | *(missing)* | havlu | Mürdüm | 75.00 | 80 | turuncu | 50x90 |
| TXT022 | çocuk odası halı yıkanabilir | çocuk | Asos | **-1** | 25 | renkli | 100x150 |

**Intentional issues shown above:**
- `TXT006`: Color typo `beya` instead of `beyaz`
- `TXT001` (row 10): Duplicate SKU
- `TXT011`: Missing price
- `TXT016`: Missing product name
- `TXT022`: Invalid price `-1`

---

## Output CSV Example

After the pipeline processes the input, a clean Shopify-ready CSV is produced. Example rows:

| Handle | Title | Vendor | Variant SKU | Variant Price | Variant Inventory Qty | Status |
|--------|-------|--------|-------------|---------------|----------------------|--------|
| pamuklu-yatak-ortusu-200x220-cm-beyaz | Pamuklu Yatak Örtüsü 200x220 cm – Beyaz \| Taç | Taç | TXT001 | 450.00 | 50 | active |
| akrilik-salon-halisi-160x230-cm-mavi | Akrilik Salon Halısı 160x230 cm – Mavi | Genel | TXT002 | 890.00 | 15 | active |
| yun-battaniye-cift-kisilik-gri | Yün Battaniye Çift Kişilik 200x220 cm – Gri \| Yataş | Yataş | TXT004 | 675.00 | 25 | active |

Each row also includes a full `Body (HTML)` column with an AI-generated Turkish description.

---

## API Example

### Request — `POST /generate-description`

```json
{
  "sku": "TXT004",
  "name": "yün battaniye çift kişilik",
  "category": "battaniye",
  "brand": "Yataş",
  "color": "gri",
  "size": "200x220",
  "material": "Yün",
  "price": 675.00,
  "stock": 25
}
```

### Response

```json
{
  "status": "success",
  "model_used": "claude-haiku-4-5-20251001",
  "output": {
    "cleaned_name": "Yün Battaniye Çift Kişilik 200x220 cm – Gri | Yataş",
    "cleaned_category": "Battaniye",
    "cleaned_color": "Gri",
    "description": "<p>Soğuk kış gecelerinde doğanın sıcaklığını hissedin...</p>",
    "error": null
  }
}
```

Full request and response examples are in `sample_api_request.json` and `sample_api_response.json`.

---

## Expected Pipeline Results

Given the 25-row `supplier_sample.csv` input, the pipeline produces:

| Metric | Value |
|--------|-------|
| Total rows processed | 25 |
| Valid products exported | 21 |
| Rows skipped (errors) | 4 |
| Critical errors | 1 (TXT022: negative price) |
| Errors | 3 (TXT001 duplicate, TXT011 no price, TXT016 no name) |
| Warnings (auto-resolved) | 6 (typos, casing, missing brand/stock) |
| AI descriptions generated | 21 |
| Avg. processing time per product | ~1.2 seconds |
| Total pipeline duration | ~15 seconds |

---

## How to Run the Demo

### Prerequisites

```bash
# Clone the repository
git clone https://github.com/mustafakavcin/n8n-Shopify-Bulk-Import
cd n8n-Shopify-Bulk-Import

# Copy environment template
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Option A — Docker (Recommended)

```bash
docker compose up --build
```

This starts:
- **FastAPI** on `http://localhost:8000`
- **n8n** on `http://localhost:5678`

Import the workflow in n8n:
1. Open `http://localhost:5678`
2. Settings → **Import Workflow** → select `workflow.json`
3. Click **Execute** to run with the built-in test data

### Option B — Test the API Directly

```bash
curl -X POST http://localhost:8000/generate-description \
  -H "Content-Type: application/json" \
  -d @sample-documents/sample_api_request.json
```

---

## Notes

- All sample data uses synthetic Turkish home-textile products (SKU range TXT001–TXT024)
- The API key shown in sample files (`sk-shopify-importer-demo-key-2024`) is a placeholder — replace with your actual Anthropic API key
- Claude Haiku was chosen for its speed and cost efficiency; the model can be swapped for Claude Sonnet or Opus in `.env` for higher-quality descriptions

---

*Built with Python · FastAPI · n8n · Claude Haiku · Docker · Shopify CSV*
