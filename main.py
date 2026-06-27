import os
import re
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic

app = FastAPI(title="Shopify Product Description Generator", version="1.0.0")
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

ABBREVIATION_MAP = {
    r"\b1mt\b": "1m",
    r"\b2mt\b": "2m",
    r"\b3mt\b": "3m",
    r"\bmt\b": "m",
    r"\bkq\b": "kg",
    r"\blt\b": "L",
    r"\bpcs\b": "adet",
}

CATEGORY_MAP = {
    "hali": "Halılar & Kilimler",
    "kilim": "Halılar & Kilimler",
    "perde": "Perdeler & Tüller",
    "tul": "Perdeler & Tüller",
    "yatak": "Yatak Örtüleri",
    "yastik": "Yastıklar & Kırlentler",
    "masa": "Masa Örtüleri",
    "banyo": "Banyo Tekstili",
    "havlu": "Havlular",
    "nevresim": "Nevresim Takımları",
    "pike": "Pike & Battaniye",
    "battaniye": "Pike & Battaniye",
}

COLOR_NORM = {
    "beyaz": "Beyaz",
    "siyah": "Siyah",
    "kirmizi": "Kırmızı",
    "mavi": "Mavi",
    "yesil": "Yeşil",
    "sari": "Sarı",
    "mor": "Mor",
    "pembe": "Pembe",
    "turuncu": "Turuncu",
    "gri": "Gri",
    "bej": "Bej",
    "kahve": "Kahverengi",
    "ekru": "Ekru",
    "lacivert": "Lacivert",
    "krem": "Krem",
}


class ProductInput(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    extra_info: Optional[str] = None


class ProductOutput(ProductInput):
    description: str
    cleaned_name: str
    cleaned_category: str
    cleaned_brand: str
    cleaned_stock: int
    cleaned_color: Optional[str]
    error: Optional[str] = None


class BatchRequest(BaseModel):
    products: list[ProductInput]


class BatchResponse(BaseModel):
    results: list[ProductOutput]
    total: int
    success_count: int
    error_count: int


def normalize_title(text: str) -> str:
    if not text:
        return text
    text = text.strip()
    for pattern, replacement in ABBREVIATION_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return " ".join(w.capitalize() for w in text.split())


def guess_category(name: str, raw_category: Optional[str]) -> str:
    if raw_category and raw_category.strip():
        for key, val in CATEGORY_MAP.items():
            if key in raw_category.lower():
                return val
        return raw_category.strip().title()
    for key, val in CATEGORY_MAP.items():
        if key in name.lower():
            return val
    return "Genel Tekstil"


def normalize_color(color: Optional[str]) -> Optional[str]:
    if not color:
        return None
    c = color.lower().strip()
    for key, val in COLOR_NORM.items():
        if key in c:
            return val
    return color.strip().title()


def validate_price(price: Optional[float]) -> tuple[Optional[float], Optional[str]]:
    if price is None:
        return None, "Fiyat eksik"
    if price <= 0:
        return None, f"Geçersiz fiyat: {price}"
    return price, None


def clean_product(product: ProductInput) -> dict:
    cleaned_name = normalize_title(product.name)
    cleaned_category = guess_category(product.name, product.category)
    cleaned_brand = product.brand.strip().title() if product.brand else "Generic"
    cleaned_stock = product.stock if product.stock is not None else 0
    cleaned_color = normalize_color(product.color)
    price, price_error = validate_price(product.price)
    return {
        "cleaned_name": cleaned_name,
        "cleaned_category": cleaned_category,
        "cleaned_brand": cleaned_brand,
        "cleaned_stock": cleaned_stock,
        "cleaned_color": cleaned_color,
        "validated_price": price,
        "price_error": price_error,
    }


def call_claude(product: ProductInput, cleaned: dict) -> str:
    parts = [f"Ürün: {cleaned['cleaned_name']}"]
    if cleaned["cleaned_category"] != "Genel Tekstil":
        parts.append(f"Kategori: {cleaned['cleaned_category']}")
    if cleaned["cleaned_brand"] != "Generic":
        parts.append(f"Marka: {cleaned['cleaned_brand']}")
    if cleaned["cleaned_color"]:
        parts.append(f"Renk: {cleaned['cleaned_color']}")
    if product.size:
        parts.append(f"Boyut: {product.size}")
    if product.material:
        parts.append(f"Malzeme: {product.material}")
    if product.extra_info:
        parts.append(f"Ek Bilgi: {product.extra_info}")

    prompt = (
        "Sen bir Türk e-ticaret uzmanısın. Aşağıdaki ürün bilgilerine göre "
        "Shopify ürün sayfası için SEO uyumlu, 2-3 cümlelik Türkçe bir ürün açıklaması yaz. "
        "Açıklama doğal, ikna edici ve arama motorlarına uygun olmalı. "
        "Sadece açıklama metnini yaz, başlık veya ek bilgi ekleme.\n\n"
        + "\n".join(parts)
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


@app.post("/generate-description", response_model=ProductOutput)
def generate_single(product: ProductInput):
    cleaned = clean_product(product)
    error = cleaned.get("price_error")
    try:
        description = call_claude(product, cleaned)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {e}")
    return ProductOutput(
        **product.model_dump(),
        description=description,
        cleaned_name=cleaned["cleaned_name"],
        cleaned_category=cleaned["cleaned_category"],
        cleaned_brand=cleaned["cleaned_brand"],
        cleaned_stock=cleaned["cleaned_stock"],
        cleaned_color=cleaned["cleaned_color"],
        error=error,
    )


@app.post("/process-batch", response_model=BatchResponse)
def process_batch(request: BatchRequest):
    seen_skus: set[str] = set()
    unique_products: list[ProductInput] = []
    for p in request.products:
        if p.sku not in seen_skus:
            seen_skus.add(p.sku)
            unique_products.append(p)

    results: list[ProductOutput] = []
    success_count = 0
    error_count = 0

    for product in unique_products:
        cleaned = clean_product(product)
        error = cleaned.get("price_error")
        description = ""
        try:
            description = call_claude(product, cleaned)
            success_count += 1
        except Exception as e:
            error = f"Description error: {e}"
            error_count += 1
        results.append(
            ProductOutput(
                **product.model_dump(),
                description=description,
                cleaned_name=cleaned["cleaned_name"],
                cleaned_category=cleaned["cleaned_category"],
                cleaned_brand=cleaned["cleaned_brand"],
                cleaned_stock=cleaned["cleaned_stock"],
                cleaned_color=cleaned["cleaned_color"],
                error=error,
            )
        )

    return BatchResponse(
        results=results,
        total=len(unique_products),
        success_count=success_count,
        error_count=error_count,
    )


@app.get("/health")
def health():
    return {"status": "ok"}
