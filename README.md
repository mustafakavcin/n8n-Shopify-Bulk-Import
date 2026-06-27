# 🛍️ Shopify Bulk Product Importer — AI-Powered Turkish Descriptions

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-workflow-EA4B71?logo=n8n&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Haiku-blueviolet?logo=anthropic&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

> **Tedarikçi CSV → Veri Temizleme → AI Açıklama → Shopify Import**
> 
> Türkçe tedarikçi verilerini alıp otomatik olarak temizleyen, Claude AI ile SEO uyumlu Türkçe ürün açıklamaları üreten ve Shopify'a hazır CSV çıktısı veren tam otomasyon pipeline'ı.

---

## ✨ Özellikler

- 🧹 **Akıllı veri temizleme** — başlık normalizasyonu, kısaltma düzeltme (`1mt → 1m`), renk ve kategori eşleme
- 🤖 **AI açıklama üretimi** — Claude Haiku ile SEO uyumlu, 2-3 cümlelik Türkçe ürün açıklamaları
- ⚡ **Toplu işleme** — 500 ürüne kadar batch desteği, otomatik SKU deduplikasyonu
- 🔁 **Görsel otomasyon** — n8n workflow ile her adım izlenebilir ve düzenlenebilir
- 📋 **Hata raporu** — eksik fiyat, geçersiz alan ve API hatalarını ayrı JSON'a yazar
- 🐳 **Tek komutla ayağa kalkar** — Docker Compose ile n8n + FastAPI birlikte çalışır

---

## 🏗️ Mimari

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
          │         Parse CSV          │  ← binary upload veya test data
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │    Clean & Map Fields      │  ← Türkçe sütun mapping
          │                            │     başlık normalizasyonu
          │                            │     renk / kategori eşleme
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │    Split Into Batches      │  ← 10'arlı gruplar
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │       FastAPI Service      │  ← localhost:8000
          │    POST /process-batch     │     SKU deduplikasyon
          │                            │     fiyat validasyonu
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │      Claude Haiku API      │  ← Türkçe SEO açıklama
          │   claude-haiku-4-5-...     │     2-3 cümle / ürün
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │      Build Shopify CSV     │  ← Shopify column schema
          └──────┬──────────────┬──────┘
                 │              │
    ┌────────────▼───┐   ┌──────▼──────────┐
    │  shopify.csv   │   │ error_report.json│
    │  (import ready)│   │ (hatalı ürünler) │
    └────────────────┘   └─────────────────┘
```

---

## 🔄 n8n ve FastAPI Nasıl Birlikte Çalışır?

**n8n** — görsel orkestratör. CSV upload için UI sağlar, her adımı node olarak zincirler, retry ve hata yönetimini üstlenir. Manuel tetiklenebilir ya da webhook ile dış sistemlerden (Shopify, form, scheduler) çağrılabilir.

**FastAPI** — AI mantık katmanı. SKU deduplikasyonu, fiyat validasyonu, Türkçe alan temizleme ve Claude Haiku API entegrasyonunu yönetir. n8n'in HTTP Request node'u her batch'i buraya POST eder, zenginleştirilmiş sonuçları alır.

---

## 🚀 Kurulum

### Gereksinimler
- Docker & Docker Compose
- Anthropic API Key → [console.anthropic.com](https://console.anthropic.com)

```bash
git clone https://github.com/mustafakavcin/n8n-Shopify-Bulk-Import
cd n8n-Shopify-Bulk-Import

cp .env.example .env
# .env dosyasını aç → ANTHROPIC_API_KEY değerini gir

docker compose up --build
```

| Servis | URL |
|---|---|
| n8n UI | http://localhost:5678 |
| FastAPI Docs | http://localhost:8000/docs |

### Workflow Import

1. n8n UI → sağ üst → **Settings → Import Workflow**
2. `workflow.json` dosyasını seç
3. **Execute** — dahili örnek veriyle test çalışır

---

## 📡 FastAPI Endpoints

### `POST /generate-description`
Tek ürün için açıklama üretir.

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
500 ürüne kadar toplu işleme, otomatik SKU deduplikasyonu.

```json
{ "products": [ ...ProductInput ] }
```

### `GET /health`
```json
{ "status": "ok" }
```

---

## 📥 Tedarikçi CSV Formatı

`Stok Kodu` ve `Ürün Adı` zorunlu, diğerleri opsiyonel:

| Türkçe Sütun | İç Alan |
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

## 🧹 Veri Temizleme Kuralları

| Kural | Detay |
|---|---|
| Başlık normalizasyonu | Title Case, `1mt → 1m`, `kq → kg`, `lt → L` |
| Kategori mapping | `hali → Halılar & Kilimler`, `nevresim → Nevresim Takımları` vb. |
| Marka | Boşsa `Generic` |
| Stok | Boşsa `0` |
| Renk | Standart Türkçe renk adlarına normalize edilir |
| Fiyat | Eksik veya `0` ise error report'a düşer |
| SKU deduplikasyon | İlk kayıt korunur, tekrarlar silinir |

---

## 📤 Shopify Çıktı Kolonları

```
Handle | Title | Body (HTML) | Vendor | Product Category | Type | Tags |
Published | Option1 Name | Option1 Value | Variant SKU |
Variant Inventory Qty | Variant Price | Status
```

---

## ⚙️ Ortam Değişkenleri

`.env.example` dosyasını kopyalayın:

| Değişken | Zorunlu | Açıklama |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Claude API anahtarı |
| `N8N_HOST` | — | Varsayılan: `localhost` |
| `N8N_BASIC_AUTH_ACTIVE` | — | n8n giriş ekranı (varsayılan: kapalı) |
| `N8N_BASIC_AUTH_USER` | — | Kullanıcı adı |
| `N8N_BASIC_AUTH_PASSWORD` | — | Şifre |

---

## 📁 Proje Yapısı

```
n8n-Shopify-Bulk-Import/
├── main.py                   # FastAPI servisi — Claude entegrasyonu, veri temizleme
├── workflow.json              # n8n workflow (import edilebilir)
├── Dockerfile                 # FastAPI image
├── docker-compose.yml         # n8n + FastAPI birlikte
├── requirements.txt           # Python bağımlılıkları
├── .env.example               # API key şablonu
├── .gitignore
└── sample-documents/          # Demo veriler — örnek CSV, JSON ve Markdown
```

---

## 📄 Lisans

MIT
