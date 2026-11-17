from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List


BEACH_TERMS = ["bien", "beach", "island", "coast", "phu quoc", "nha trang", "da nang", "ha long", "quy nhon", "con dao", "vung tau"]
MOUNTAIN_TERMS = ["nui", "mountain", "sapa", "sa pa", "da lat", "moc chau", "tam dao", "phan xi pang"]
FAMILY_TERMS = ["gia dinh", "family", "tre em", "kids"]
BUDGET_TERMS = ["gia re", "gia tot", "tiet kiem", "budget", "cheap", "affordable", "sale", "khuyen mai"]
PREMIUM_TERMS = ["cao cap", "premium", "luxury", "sang trong", "resort 5 sao"]
INTERNATIONAL_TERMS = ["nuoc ngoai", "du lich ngoai nuoc", "quoc te", "international", "abroad", "thai lan", "singapore", "han quoc", "nhat ban", "phap", "france", "australia", "chau uc", "uae", "dubai", "chau au"]
DOMESTIC_TERMS = ["trong nuoc", "du lich trong nuoc", "noi dia", "domestic", "viet nam", "quang ninh", "lao cai", "ninh binh", "vinh long", "da nang"]
DOMESTIC_EXPLICIT_TERMS = ["trong nuoc", "du lich trong nuoc", "noi dia", "domestic", "viet nam"]
HOT_WEATHER_TERMS = ["nong", "nong qua", "troi nong", "oi buc", "mat me", "tranh nong", "doi gio"]
RELAX_TERMS = ["nghi duong", "resort", "relax", "thu gian", "yen tinh"]
SIMILAR_TERMS = [
    "tuong tu", "giong", "similar", "like this", "nhu vay", "nhu the",
    "cung loai", "cung danh muc", "cung dia diem", "tuong duong",
    "tour nao khac", "tour khac", "co tour nao", "goi y them",
    "tour nao con", "tour nao kia",
]


FOLLOWUP_PATTERNS = [
    "tour do",
    "tour nay",
    "tour dau",
    "tour thu",
    "cai dau",
    "cai thu",
    "cai do",
    "cai nay",
    "con cho",
    "con slot",
    "may ngay",
    "bao lau",
    "gia bao nhieu",
    "gia sao",
    "nhieu tien",
    "di bang gi",
    "phuong tien",
    "lich trinh",
    "khi nao",
    "khoi hanh",
    "them thong tin",
    "chi tiet hon",
]

QUERY_STOPWORDS = {
    "toi", "minh", "ban", "em", "anh", "chi", "co", "chu", "bac", "quy", "khach",
    "cho", "hoi", "muon", "can", "tim", "xem", "kiem", "khong", "la", "gi", "nao",
    "dau", "tai", "va", "hay", "hoac", "nhung", "cac", "mot", "nhieu", "ve", "voi",
    "cua", "trong", "ngoai", "tren", "duoi", "sau", "truoc", "nay", "kia", "do",
    "tour", "du", "lich", "chuyen", "di", "gia", "bao", "nhieu", "tien", "ngay",
    "dem", "thang", "nam", "tu", "van", "goi", "y", "nhe", "vay", "a", "oi",
    "the", "sao", "nhu", "de", "duoc", "thi", "ma", "con", "het", "dang", "se",
    "da", "vua", "moi", "tot", "nhat", "re", "cao", "cap", "binh", "phu", "hop",
    "nhung", "ai", "lam", "giup", "xin", "chao", "cam", "on", "vui", "long",
    "for", "the", "and", "with", "what", "where", "when", "how", "can", "you",
    "please", "about", "want", "find", "book", "trip", "travel",
}


def normalize_text(text: Any) -> str:
    cleaned = " ".join(str(text or "").split()).replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFKD", cleaned)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return normalized.lower()


def extract_meaningful_tokens(query: str) -> List[str]:
    normalized = normalize_text(query)
    raw_tokens = re.findall(r"[a-z0-9]+", normalized)
    meaningful: List[str] = []
    seen = set()
    for token in raw_tokens:
        if len(token) < 2 or token in QUERY_STOPWORDS:
            continue
        if token not in seen:
            seen.add(token)
            meaningful.append(token)
    return meaningful


def is_followup_query(query: str) -> bool:
    normalized = normalize_text(query)
    if not normalized:
        return False
    if any(pattern in normalized for pattern in FOLLOWUP_PATTERNS):
        return True
    if any(extract_query_intents(query).values()):
        return False
    tokens = extract_meaningful_tokens(query)
    word_count = len(normalized.split())
    return word_count <= 4 and len(tokens) == 0


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
        "similar": any(term in text for term in SIMILAR_TERMS),
        "domestic": any(term in text for term in DOMESTIC_EXPLICIT_TERMS),
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