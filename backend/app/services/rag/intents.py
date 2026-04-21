from __future__ import annotations

import unicodedata
from typing import Any, Dict


BEACH_TERMS = ["bien", "beach", "island", "coast", "phu quoc", "nha trang", "da nang", "ha long", "quy nhon", "con dao", "vung tau"]
MOUNTAIN_TERMS = ["nui", "mountain", "sapa", "sa pa", "da lat", "moc chau", "tam dao", "phan xi pang"]
FAMILY_TERMS = ["gia dinh", "family", "tre em", "kids"]
BUDGET_TERMS = ["gia re", "gia tot", "tiet kiem", "budget", "cheap", "affordable", "sale", "khuyen mai"]
PREMIUM_TERMS = ["cao cap", "premium", "luxury", "sang trong", "resort 5 sao"]
INTERNATIONAL_TERMS = ["nuoc ngoai", "du lich ngoai nuoc", "quoc te", "international", "abroad", "thai lan", "singapore", "han quoc", "nhat ban", "phap", "france", "uc", "australia", "uae", "dubai", "chau au"]
DOMESTIC_TERMS = ["trong nuoc", "du lich trong nuoc", "domestic", "viet nam", "quang ninh", "lao cai", "ninh binh", "vinh long", "da nang"]
HOT_WEATHER_TERMS = ["nong", "nong qua", "troi nong", "oi buc", "mat me", "tranh nong", "doi gio"]
RELAX_TERMS = ["nghi duong", "resort", "relax", "thu gian", "yen tinh"]


def normalize_text(text: Any) -> str:
    normalized = unicodedata.normalize("NFKD", " ".join(str(text or "").split()))
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return normalized.lower()


def extract_query_intents(query: str) -> Dict[str, bool]:
    text = normalize_text(query)
    return {
        "beach": any(term in text for term in BEACH_TERMS),
        "mountain": any(term in text for term in MOUNTAIN_TERMS),
        "family": any(term in text for term in FAMILY_TERMS),
        "budget": any(term in text for term in BUDGET_TERMS),
        "premium": any(term in text for term in PREMIUM_TERMS),
        "international": any(term in text for term in INTERNATIONAL_TERMS),
        "hot_weather": any(term in text for term in HOT_WEATHER_TERMS),
        "relax": any(term in text for term in RELAX_TERMS),
    }


def source_match_text(item: Dict[str, Any]) -> str:
    return normalize_text(
        " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("location") or ""),
                str(item.get("category_name") or ""),
                str(item.get("text") or ""),
            ]
        )
    )


def segment_instruction(segment: Dict[str, Any] | None) -> str:
    segment_name = str((segment or {}).get("segment_name") or "Khach moi")
    mapping = {
        "Khách mua nhiều": "Uu tien tour cao cap, lich trinh thoai mai, nhan manh gia tri dich vu.",
        "Khách săn sale": "Uu tien tour gia tot, neu ro muc gia va gia tri/chi phi.",
        "Khách ít tương tác": "Uu tien tour pho bien, de quyet dinh, mo ta ngan gon.",
        "Khách mới": "Uu tien tour de di, de hieu, duoc nhieu nguoi chon.",
        "Khách trung thành": "Uu tien tour moi, noi bat, phu hop so thich da the hien.",
    }
    favorite_category = str((segment or {}).get("favorite_category") or "General")
    return f"{mapping.get(segment_name, 'Ca nhan hoa la tin hieu uu tien mem, khong phai su that bo sung.')} Danh muc quan tam gan day: {favorite_category}."