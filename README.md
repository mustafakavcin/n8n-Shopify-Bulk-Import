# 🛍️ Shopify Bulk Product Importer — AI-Powered Turkish Descriptions

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-workflow-EA4B71?logo=n8n&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Haiku-blueviolet?logo=anthropic&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

> **Supplier CSV → Data Cleaning → AI Description → Shopify Import**
>
> A full automation pipeline that ingests raw Turkish supplier data, cleans it automatically, generates SEO-optimized Turkish product descriptions with Claude AI, and outputs a Shopify-ready CSV.

---

## ✨ Features

- 🧹 **Smart data cleaning** — title normalization, abbreviation expansion (`1mt → 1m`), color and category mapping
- 🤖 **AI description generation** — SEO-optimized 2–3 sentence Turkish product descriptions via Claude Haiku
- ⚡ **Batch processing** — supports up to 500 products per run with automatic SKU deduplication
- 🔁 **Visual automation** — every pipeline step is visible and editable in the n8n workflow UI
- 📋 **Error reporting** — missing prices, invalid fields, and API errors are written to a separate JSON report
- 🐳 **One-command startup** — n8n + FastAPI run together via Docker Compose

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        n8n UI                           │
│                  localhost:5678                         │
└───────────────────────┬─────────────────────────────────┘
                        │
          ┌─────────────▼──────────────┐
          │     Webhook / Manual       │
          │         Trigger            │
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │         Parse CSV          │  ← binary upload or test data
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │    Clean & Map Fields      │  ← Turkish column mapping
          │                            │     title normalization
          │                            │     color / category mapping
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │    Split Into Batches      │  ← groups of 10
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │       FastAPI Service      │  ← localhost:8000
          │    POST /process-batch     │     SKU deduplication
          │                            │     price validation
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │      Claude Haiku API      │  ← Turkish SEO description
          │   claude-haiku-4-5-...     │     2-3 sentences / product
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │      Build Shopify CSV     │  ← Shopify column schema
          └──────┬──────────────┬──────┘
                 │              │
    ┌────────────▼───┐   ┌──────▼──────────┐
    │  shopify.csv   │   │ error_report.json│
    │  (import ready)│   │ (skipped items)  │
    └────────────────┘   └─────────────────┘
```

---

## 🔄 How n8n and FastAPI Work Together

**n8n** — the visual orchestrator. It provides a UI for CSV uploads, chains every step as a node, and handles retries and error routing. The workflow can be triggered manually or called from external systems (Shopify webhooks, forms, schedulers) via webhook.

**FastAPI** — the AI logic layer. It handles SKU deduplication, price validation, Turkish field normalization, and the Claude Haiku API integration. n8n's HTTP Request node POSTs each batch here and receives the enriched results.

---

## 🚀 Setup

### Requirements
- Docker & Docker Compose
- Anthropic API Key → [console.anthropic.com](https://console.anthropic.com)

```bash
git clone https://github.com/mustafakavcin/n8n-Shopify-Bulk-Import
cd n8n-Shopify-Bulk-Import

cp .env.example .env
# Open .env and set your ANTHROPIC_API_KEY

docker compose up --build
```

| Service | URL |
|---|---|
| n8n UI | http://localhost:5678 |
| FastAPI Docs | http://localhost:8000/docs |

### Workflow Import

1. n8n UI → top right → **Settings → Import Workflow**
2. Select `workflow.json`
3. Click **Execute** — runs immediately with the built-in sample data

---

## 📡 FastAPI Endpoints

### `POST /generate-description`
Generates an AI description for a single product.

```json
{
  "sku": "TXT-001",
  "name": "pamuk yatak örtüsü 1mt",
  "category": "yatak",
  "brand": "ÖRNEK",
  "price": 250.0,
  "stock": 15,
  "color": "beyaz",
  "size": "200x220",
  "material": "Pamuk"
}
```

**Response:**
```json
{
  "sku": "TXT-001",
  "description": "Doğal pamuktan üretilen bu yatak örtüsü...",
  "cleaned_name": "Pamuk Yatak Örtüsü 1m",
  "cleaned_category": "Yatak Örtüleri",
  "cleaned_color": "Beyaz",
  "error": null
}
```

### `POST /process-batch`
Batch processing for up to 500 products with automatic SKU deduplication.

```json
{ "products": [ ...ProductInput ] }
```

### `GET /health`
```json
{ "status": "ok" }
```

---

## 📥 Supplier CSV Format

`Stok Kodu` (SKU) and `Ürün Adı` (Product Name) are required; all other columns are optional:

| Turkish Column | Internal Field |
|---|---|
| Stok Kodu | `sku` |
| Ürün Adı | `name` |
| Kategori | `category` |
| Marka | `brand` |
| Fiyat | `price` |
| Stok | `stock` |
| Renk | `color` |
| Boyut | `size` |
| Malzeme | `material` |
| Açıklama | `extra_info` |

---

## 🧹 Data Cleaning Rules

| Rule | Detail |
|---|---|
| Title normalization | Title Case, `1mt → 1m`, `kq → kg`, `lt → L` |
| Category mapping | `hali → Halılar & Kilimler`, `nevresim → Nevresim Takımları`, etc. |
| Brand | Defaults to `Generic` if missing |
| Stock | Defaults to `0` if missing |
| Color | Normalized to standard Turkish color names |
| Price | Routed to error report if missing or `0` |
| SKU deduplication | First occurrence kept; duplicates discarded |

---

## 📤 Shopify Output Columns

```
Handle | Title | Body (HTML) | Vendor | Product Category | Type | Tags |
Published | Option1 Name | Option1 Value | Variant SKU |
Variant Inventory Qty | Variant Price | Status
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in your values:

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Your Claude API key |
| `N8N_HOST` | — | Default: `localhost` |
| `N8N_BASIC_AUTH_ACTIVE` | — | Enable n8n login screen (default: false) |
| `N8N_BASIC_AUTH_USER` | — | n8n username |
| `N8N_BASIC_AUTH_PASSWORD` | — | n8n password |

---

## 📁 Project Structure

```
n8n-Shopify-Bulk-Import/
├── main.py                   # FastAPI service — Claude integration, data cleaning
├── workflow.json              # n8n workflow (importable)
├── Dockerfile                 # FastAPI image
├── docker-compose.yml         # n8n + FastAPI together
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── .gitignore
└── sample-documents/          # Demo data — sample CSVs, JSON, and Markdown
```

---

## 📄 License

MIT
