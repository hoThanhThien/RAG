from __future__ import annotations

import re
import unicodedata


VIETNAM_LOCATIONS = (
    'Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ',
    'Quảng Ninh', 'Lâm Đồng', 'Khánh Hòa', 'Kiên Giang', 'Bình Thuận',
    'Thừa Thiên Huế', 'Quảng Nam', 'Bà Rịa - Vũng Tàu', 'Đồng Nai',
    'Bình Dương', 'Long An', 'Tiền Giang', 'Bến Tre', 'Trà Vinh',
    'Vĩnh Long', 'Đồng Tháp', 'An Giang', 'Sóc Trăng', 'Bạc Liêu',
    'Cà Mau', 'Ninh Bình', 'Thanh Hóa', 'Nghệ An', 'Hà Tĩnh',
    'Quảng Bình', 'Quảng Trị', 'Kon Tum', 'Gia Lai', 'Đắk Lắk',
    'Đắk Nông', 'Phú Yên', 'Bình Định', 'Ninh Thuận', 'Tây Ninh',
    'Bình Phước', 'Phú Thọ', 'Vĩnh Phúc', 'Bắc Ninh', 'Hải Dương',
    'Hưng Yên', 'Thái Bình', 'Nam Định', 'Hà Nam', 'Sơn La',
    'Lai Châu', 'Lào Cai', 'Yên Bái', 'Điện Biên', 'Hòa Bình',
    'Tuyên Quang', 'Lạng Sơn', 'Cao Bằng', 'Bắc Kạn', 'Thái Nguyên',
    'Quảng Ngãi', 'Hà Giang', 'Phú Quốc', 'Vũng Tàu', 'Huế',
)


def normalize_location_text(value: str | None) -> str:
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    text = text.lower().replace('đ', 'd')
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


NORMALIZED_VIETNAM_LOCATIONS = tuple(
    normalize_location_text(location)
    for location in VIETNAM_LOCATIONS
)


def is_vietnam_location(value: str | None) -> bool:
    normalized_value = normalize_location_text(value)
    if not normalized_value:
        return False

    if normalized_value in NORMALIZED_VIETNAM_LOCATIONS:
        return True

    return any(location in normalized_value for location in NORMALIZED_VIETNAM_LOCATIONS)