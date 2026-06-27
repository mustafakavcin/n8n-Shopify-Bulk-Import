# Shopify Bulk Product Importer with AI Descriptions

An n8n automation pipeline that takes messy Turkish supplier CSVs, cleans the data, generates SEO-friendly Turkish product descriptions via Claude AI, and outputs a ready-to-import Shopify CSV.

## Architecture

```
Webhook / Manual Trigger
        ↓
   Parse CSV
        ↓
 Clean & Map Fields     ← title normalization, abbreviation fixes (1mt→1m),
        ↓                  category mapping, stock/brand defaults, color normalization
Split Into Batches (10)
        ↓
  FastAPI Service       ← POST /process-batch
        ↓                  SKU deduplication, price validation
  Claude Haiku API      ← Turkish SEO descriptions (2-3 sentences)
        ↓
  Build Shopify CSV     ← Shopify-compatible column schema
        ↓
 Error Report JSON      ← Invalid price, missing fields, API errors
```

## Tech Stack

| Layer | Tool |
|---|---|
| Workflow automation | [n8n](https://n8n.io) |
| AI descriptions | [Anthropic Claude Haiku](https://www.anthropic.com) |
| Microservice | FastAPI (Python 3.12) |
| Containerization | Docker + Docker Compose |

## Quick Start

```bash
git clone <repo>
cd shopify-bulk-importer

cp .env.example .env
# edit .env → set ANTHROPIC_API_KEY

docker compose up --build
```

- **n8n UI:** http://localhost:5678
- **FastAPI docs:** http://localhost:8000/docs

### Import the Workflow

1. Open n8n → Settings → **Import Workflow**
2. Select `workflow.json`
3. Click **Execute** to test with built-in sample data

## FastAPI Endpoints

### `POST /generate-description`
Generate a description for a single product.

```json
{
  "sku": "TXT-001",
  "name": "pamuk yatak ortüsü 1mt",
  "category": "yatak",
  "brand": "ÖRNEK",
  "price": 250.0,
  "stock": 15,
  "color": "beyaz",
  "size": "200x220",
  "material": "Pamuk"
}
```

### `POST /process-batch`
Process up to 500 products at once with automatic SKU deduplication.

```json
{ "products": [ ...ProductInput ] }
```

### `GET /health`

## Supplier CSV Format

The pipeline expects a Turkish-language CSV with these columns (`Stok Kodu` and `Ürün Adı` are required, rest optional):

| Turkish Column | Maps To |
|---|---|
| Stok Kodu | sku |
| Ürün Adı | name |
| Kategori | category |
| Marka | brand |
| Fiyat | price |
| Stok | stock |
| Renk | color |
| Boyut | size |
| Malzeme | material |
| Açıklama | extra_info |

## Data Cleaning Rules

- **Title normalization:** Title Case, abbreviations fixed (`1mt → 1m`, `kq → kg`, `lt → L`)
- **Category mapping:** Turkish keywords auto-mapped (e.g. `hali → Halılar & Kilimler`)
- **Brand:** Defaults to `Generic` if missing
- **Stock:** Defaults to `0` if missing
- **Color:** Normalized to standard Turkish color names
- **Price:** Rows with missing/zero price are flagged in the error report
- **SKU deduplication:** First occurrence wins; duplicates are silently dropped

## Shopify Output Columns

`Handle, Title, Body (HTML), Vendor, Product Category, Type, Tags, Published, Option1 Name, Option1 Value, Variant SKU, Variant Inventory Qty, Variant Price, Status`

## Environment Variables

See `.env.example` for the full list.

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `N8N_HOST` | — | Defaults to `localhost` |
| `N8N_BASIC_AUTH_ACTIVE` | — | Enable n8n login (default: false) |
