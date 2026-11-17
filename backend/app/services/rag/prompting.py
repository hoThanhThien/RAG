from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.services.rag.intents import extract_query_intents, normalize_text, segment_instruction


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


def build_system_prompt(segment: Optional[Dict[str, Any]], custom_addon: str = "") -> str:
    personalization = segment_instruction(segment)
    addon_block = f"\n\nHƯỚNG DẪN BỔ SUNG TỪ QUẢN TRỊ VIÊN:\n{custom_addon.strip()}" if custom_addon and custom_addon.strip() else ""
    return (
        "Bạn là trợ lý AI tư vấn du lịch. Chỉ được phép dựa trên context được cung cấp, không bịa thông tin.\n"
        "\n"
        "NGUYÊN TẮC QUAN TRỌNG:\n"
        "1. ƯU TIÊN TRẢ LỜI TỪ DỮ LIỆU (CONTEXT)\n"
        "   - Nếu câu hỏi là kiến thức (so sánh, định nghĩa, 'có điểm chung gì', 'là gì', 'tại sao') "
        "→ CHỈ trả lời dựa trên context, KHÔNG gợi ý tour.\n"
        "2. CHỈ GỢI Ý TOUR KHI:\n"
        "   - Người dùng muốn đi đâu (ví dụ: 'đi đâu', 'gợi ý', 'tour nào')\n"
        "   - Hoặc hỏi về lịch trình / chi phí chuyến đi.\n"
        "3. KHÔNG BAO GIỜ:\n"
        "   - Tự ý chuyển sang gợi ý tour nếu câu hỏi không liên quan.\n"
        "   - Trả lời lan man ngoài context.\n"
        "   - Bịa thông tin.\n"
        "4. XỬ LÝ TRƯỜNG HỢP KHÔNG CÓ DỮ LIỆU:\n"
        "   - Nếu context không đủ → nói rõ: 'Hiện chưa có dữ liệu phù hợp'.\n"
        "\n"
        "PHÂN LOẠI CÂU HỎI:\n"
        "A. CÂU HỎI KIẾN THỨC (so sánh, định nghĩa, 'có điểm chung gì', 'là gì') "
        "→ Trả lời ngắn gọn, đúng context, không gợi ý tour.\n"
        "B. CÂU HỎI DU LỊCH ('đi đâu', 'gợi ý tour', lịch trình, chi phí) "
        "→ Có thể gợi ý tour, ưu tiên 1–3 lựa chọn sát nhất.\n"
        "\n"
        "QUAN TRỌNG: Nếu context không chứa tour thỏa mãn yêu cầu, tuyệt đối không gợi ý tour không liên quan. "
        "Phải nói thẳng: 'Hiện chưa có tour phù hợp với yêu cầu này'.\n"
        "Nếu intent là 'giá rẻ nhất' thì sắp xếp tăng dần theo giá. "
        "Nếu intent là 'cao cấp' thì sắp xếp giảm dần theo giá.\n"
        "KHÔNG thêm text như 'gợi ý cho bạn' nếu không cần thiết. "
        "Trả lời bằng tiếng Việt, ngắn gọn, thực dụng.\n"
        f"{personalization}{addon_block}"
    )


def build_out_of_scope_prompts(
    query: str,
    segment: Optional[Dict[str, Any]],
    mode: str,
    custom_system_prompt: str = "",
    popular_tours_context: str = "",
) -> Tuple[str, str]:
    personalization = segment_instruction(segment)
    admin_prompt = (custom_system_prompt or "").strip()

    if mode == "open_ai":
        base_prompt = admin_prompt or (
            "Bạn là trợ lý AI thân thiện của nền tảng đặt tour du lịch. "
            "Hãy trả lời câu hỏi của người dùng một cách tự nhiên, rõ ràng, súc tích bằng tiếng Việt."
        )
        system_prompt = (
            f"{base_prompt}\n\n"
            "Lưu ý:\n"
            "- Câu hỏi này nằm ngoài danh mục tour hiện có trong hệ thống.\n"
            "- Tuyệt đối KHÔNG bịa đặt tên tour hoặc giá vé không có trong dữ liệu được cung cấp.\n"
            f"- Cá nhân hóa nhẹ nhàng: {personalization}"
        )
    else:
        # general_travel (mặc định)
        base_prompt = admin_prompt or (
            "Bạn là chuyên gia tư vấn du lịch thân thiện và am hiểu thực tế."
        )
        system_prompt = (
            f"{base_prompt}\n\n"
            "NHIỆM VỤ KHI CÂU HỎI NGOÀI DANH MỤC TOUR:\n"
            "1. Dùng kiến thức du lịch chung để giải đáp ngắn gọn, hữu ích và thực tế cho câu hỏi của khách (visa, kinh nghiệm, thời tiết, văn hóa, điểm đến ngoài danh mục...).\n"
            "2. Nếu khách hỏi về một điểm đến/tour cụ thể chưa có trong hệ thống, hãy nói rõ là hiện tại danh mục tour của hệ thống chưa có tour khớp trực tiếp.\n"
            "3. Tuyệt đối KHÔNG bịa đặt tên tour, lịch khởi hành hoặc giá tour của hệ thống nếu không có trong danh sách gợi ý bên dưới.\n"
            "4. Nếu có danh sách tour nổi bật bên dưới, có thể gợi ý nhẹ nhàng 1–3 lựa chọn thay thế phù hợp.\n"
            "5. Trả lời bằng tiếng Việt, tự nhiên, súc tích.\n"
            f"{personalization}"
        )

    popular_block = (
        f"\n\nMột số tour nổi bật hiện có trong hệ thống (chỉ dùng để tham khảo/gợi ý thêm nếu phù hợp):\n{popular_tours_context}"
        if popular_tours_context.strip()
        else "\n\n(Hiện không đính kèm tour gợi ý bổ sung.)"
    )
    user_prompt = (
        f"Người dùng hỏi: {query}"
        f"{popular_block}\n\n"
        "Hãy trả lời trực tiếp câu hỏi trên bằng tiếng Việt."
    )
    return system_prompt, user_prompt


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
    # Detect if this is a knowledge question (no tour suggestion needed)
    knowledge_keywords = ["co gi chung", "diem chung", "la gi", "tai sao", "so sanh", "dinh nghia", "giai thich"]
    query_norm = normalize_text(query)
    is_knowledge_question = any(kw in query_norm for kw in knowledge_keywords)

    answer_instruction = (
        "- Đây là câu hỏi kiến thức: CHỈ trả lời dựa trên context, KHÔNG gợi ý tour.\n"
        if is_knowledge_question else
        "- Nếu có tour phù hợp: giới thiệu ngắn gọn (tên, địa điểm, giá nếu có).\n"
        "- Nếu là câu hỏi chung về điểm đến: trả lời trực tiếp, không ép gợi ý tour.\n"
    )

    return (
        f"Người dùng hỏi: {query}\n\n"
        f"Dữ liệu tham khảo:\n{context}\n\n"
        "Yêu cầu:\n"
        f"{similar_hint}"
        f"{hard_filter_hint}"
        f"{price_sort_hint}"
        f"{answer_instruction}"
        "- Chỉ dùng thông tin có trong context, không bịa thêm.\n"
        "- Nếu không có dữ liệu phù hợp → nói rõ: \"Hiện chưa có dữ liệu phù hợp\".\n"
        "- Không liệt kê quá 3 tour.\n"
        "- KHÔNG thêm text như 'gợi ý cho bạn' nếu không cần thiết."
    )