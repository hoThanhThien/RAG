from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.services.rag.intents import extract_query_intents, segment_instruction


def build_context(sources: List[Dict[str, Any]], max_context_chars: int) -> str:
    parts: List[str] = []
    current_length = 0
    for index, source in enumerate(sources, start=1):
        block = (
            f"[{index}] TourID={source.get('tour_id')} | Title={source.get('title')} | "
            f"Location={source.get('location')} | Category={source.get('category_name')} | "
            f"Price={source.get('price')} | ChunkType={source.get('chunk_type')}\n"
            f"{source.get('text')}"
        )
        if current_length + len(block) > max_context_chars:
            break
        parts.append(block)
        current_length += len(block)
    return "\n\n".join(parts)


def build_system_prompt(segment: Optional[Dict[str, Any]]) -> str:
    personalization = segment_instruction(segment)
    return (
        "Ban la tro ly tu van tour du lich su dung RAG tren du lieu noi bo. "
        "Chi duoc phep dua tren context va metadata duoc cung cap. "
        "Khong duoc tu suy dien thong tin khong co trong context. "
        "Neu khong du du lieu thi phai noi ro: 'Chua co thong tin trong he thong'. "
        "Segment khach hang chi la tin hieu uu tien mem de xep thu tu goi y, khong phai bang chung su that. "
        "Tra loi bang tieng Viet, gon, thuc dung, uu tien 1-3 lua chon sat nhat. "
        "Neu de xuat tour, moi dong nen co: ten tour, dia diem, gia neu co, ly do ngan. "
        "QUAN TRONG: Neu context khong chua tour thoa man yeu cau nguoi dung (vi du: yeu cau tour bien nhung context chi co tour nui), "
        "tuyet doi khong duoc goi y cac tour do. Phai noi thang: 'Hien chua co tour phu hop voi yeu cau nay trong du lieu'. "
        "Neu intent la 'gia re nhat' thi chi liet ke cac tour co gia thap nhat trong context, sap xep tu re den dat. "
        "Neu intent la 'cao cap' thi chi liet ke cac tour co gia cao nhat trong context, sap xep tu dat den re. "
        f"{personalization}"
    )


def build_user_prompt(query: str, segment: Optional[Dict[str, Any]], context: str, focus_tour_id: Optional[int] = None, focus_source: Optional[Dict[str, Any]] = None) -> str:
    intents = extract_query_intents(query)
    hard_intents = {k: v for k, v in intents.items() if v and k in ("beach", "mountain", "international", "hot_weather")}
    price_sort_hint = ""
    if intents.get("budget"):
        price_sort_hint = "- User muon tour GIA RE NHAT: chi liet ke tour co gia thap nhat, sap xep tang dan theo gia.\n"
    elif intents.get("premium"):
        price_sort_hint = "- User muon tour CAO CAP: chi liet ke tour co gia cao nhat, sap xep giam dan theo gia.\n"
    hard_filter_hint = ""
    if hard_intents:
        hard_filter_hint = (
            f"- HARD FILTER: Nguoi dung chi muon {list(hard_intents.keys())}. "
            "Neu context khong co tour thoa man dieu kien nay, "
            "KHONG duoc goi y tour khac. Tra loi: 'Hien chua co tour phu hop voi yeu cau nay'.\n"
        )
    similar_hint = ""
    if intents.get("similar") and focus_tour_id:
        focus_title = str(focus_source.get("title") or f"tour ID {focus_tour_id}") if focus_source else f"tour ID {focus_tour_id}"
        focus_cat = str(focus_source.get("category_name") or "") if focus_source else ""
        focus_loc = str(focus_source.get("location") or "") if focus_source else ""
        similar_hint = (
            f"- SIMILAR FILTER: User dang xem '{focus_title}' (ID={focus_tour_id}"
            + (f", danh muc: {focus_cat}" if focus_cat else "")
            + (f", dia diem: {focus_loc}" if focus_loc else "")
            + "). Chi goi y cac tour KHAC co cung danh muc hoac cung dia diem. "
            "TUYET DOI KHONG duoc noi lai chinh tour do. "
            "Neu khong co tour tuong tu thi noi ro.\n"
        )
    return (
        f"Cau hoi nguoi dung: {query}\n"
        f"Intent da nhan dien: {json.dumps(intents, ensure_ascii=False)}\n"
        f"Thong tin segment: {json.dumps(segment or {}, ensure_ascii=False)}\n\n"
        "Context noi bo:\n"
        f"{context}\n\n"
        "Yeu cau tra loi:\n"
        f"{similar_hint}"
        f"{hard_filter_hint}"
        f"{price_sort_hint}"
        "- Neu khong co tour phu hop thi noi ro ly do.\n"
        "- Khong nhac den thong tin khong nam trong context.\n"
        "- Khong liet ke qua 3 tour.\n"
        "- Khong lap lai query goc."
    )