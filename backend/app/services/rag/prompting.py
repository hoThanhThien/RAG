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
        f"{personalization}"
    )


def build_user_prompt(query: str, segment: Optional[Dict[str, Any]], context: str) -> str:
    intents = extract_query_intents(query)
    return (
        f"Cau hoi nguoi dung: {query}\n"
        f"Intent da nhan dien: {json.dumps(intents, ensure_ascii=False)}\n"
        f"Thong tin segment: {json.dumps(segment or {}, ensure_ascii=False)}\n\n"
        "Context noi bo:\n"
        f"{context}\n\n"
        "Yeu cau tra loi:\n"
        "- Neu khong co tour phu hop thi noi ro ly do.\n"
        "- Khong nhac den thong tin khong nam trong context.\n"
        "- Khong liet ke qua 3 tour.\n"
        "- Khong lap lai query goc."
    )