#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Optional, Tuple

import pymysql


def _parse_database_url(url: str) -> Optional[Tuple[str, int, str, str, str]]:
	# Expected format: mysql+pymysql://user:pass@host:port/db
	try:
		raw = url.replace("mysql+pymysql://", "", 1)
		user_pass, host_db = raw.split("@", 1)
		user, password = user_pass.split(":", 1)
		host_port, dbname = host_db.split("/", 1)
		host, port = host_port.split(":", 1)
		return host, int(port), user, password, dbname
	except Exception:
		return None


def _connect_db() -> pymysql.connections.Connection:
	parsed = _parse_database_url(os.getenv("DATABASE_URL", ""))

	if parsed:
		host, port, user, password, dbname = parsed
	else:
		host, port, user, password, dbname = (
			"mysql",
			3306,
			"tour_user",
			"tour_pass123",
			"tourbookingdb",
		)

	# Try the configured host first, then common fallbacks.
	host_candidates = [host]
	for fallback in ["mysql", "127.0.0.1", "localhost"]:
		if fallback not in host_candidates:
			host_candidates.append(fallback)

	last_error = None
	for candidate in host_candidates:
		try:
			return pymysql.connect(
				host=candidate,
				port=port,
				user=user,
				password=password,
				database=dbname,
				charset="utf8mb4",
				autocommit=False,
			)
		except Exception as exc:
			last_error = exc

	# Final local-port fallback in case compose publishes 3306 and .env had wrong port.
	try:
		return pymysql.connect(
			host="127.0.0.1",
			port=3306,
			user=user,
			password=password,
			database=dbname,
			charset="utf8mb4",
			autocommit=False,
		)
	except Exception as exc:
		raise RuntimeError(f"Cannot connect MySQL using hosts={host_candidates}: {exc}") from last_error


def main() -> None:
	conn = _connect_db()

	descriptions = {
		30: "Khám phá Vịnh Hạ Long – kỳ quan thiên nhiên thế giới với hơn 1900 đảo đá vôi nhô lên từ mặt biển xanh ngọc. Trải nghiệm ngủ đêm trên du thuyền sang trọng, chèo kayak khám phá hang Sửng Sốt và hang Luồn bí ẩn. Tham quan làng chài Cửa Vạn nổi trên mặt nước, tắm biển tại bãi Ti Tốp, ngắm hoàng hôn tuyệt đẹp. Thưởng thức hải sản tươi sống đặc trưng vùng biển Quảng Ninh. Tour du lịch trong nước được yêu thích nhất Việt Nam.",
		80: "Hành trình khám phá miền Trung Việt Nam cao cấp 3 ngày 2 đêm. Huế – cố đô triều Nguyễn với Đại Nội, lăng tẩm các vua, sông Hương thơ mộng, chùa Thiên Mụ cổ kính và ẩm thực Huế tinh tế. Đà Nẵng – thành phố đáng sống với Cầu Rồng phun lửa, Bà Nà Hills huyền ảo, Cầu Vàng nổi tiếng toàn cầu, bãi biển Mỹ Khê đẹp nhất châu Á. Nghỉ dưỡng tại resort 5 sao ven biển, thưởng thức hải sản tươi và ẩm thực đặc trưng địa phương.",
		81: "Nghỉ dưỡng biển cao cấp tại Phú Quốc – hòn đảo ngọc của Việt Nam thuộc tỉnh Kiên Giang. Resort 4 sao ven biển với hồ bơi vô cực nhìn ra Vịnh Thái Lan, bãi biển Ông Lang và Bãi Sao trong xanh tuyệt đẹp. Tham quan Vinpearl Safari – vườn thú bán hoang dã đầu tiên tại Việt Nam, VinWonders Phú Quốc, nhà tù Phú Quốc lịch sử. Thưởng thức hải sản tươi sống: cua Huỳnh Đế, nhum biển, ghẹ. Ngắm hoàng hôn tuyệt mỹ tại Bãi Dài – một trong những bãi hoàng hôn đẹp nhất thế giới.",
		82: "Trekking khám phá Sa Pa và chinh phục đỉnh Fansipan 3143m – đỉnh núi cao nhất Đông Dương bằng cáp treo hoặc đi bộ. Băng qua rừng nguyên sinh với hệ sinh thái đa dạng, ngắm thác nước bạc xanh và suối chảy róc rách. Khám phá bản Cát Cát, bản Sin Chải với văn hóa người H'Mông Hoa truyền thống. Ngắm ruộng bậc thang kỳ vĩ mùa lúa chín vàng. Trải nghiệm đêm chợ Sa Pa sôi động, mua đặc sản thổ cẩm và ẩm thực núi rừng Tây Bắc. Tour lý tưởng cho người yêu thiên nhiên và phiêu lưu khám phá.",
	}

	try:
		with conn.cursor() as cur:
			# Enforce UTF-8 at schema/table level to avoid future mojibake.
			cur.execute("ALTER DATABASE tourbookingdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
			cur.execute("ALTER TABLE tour CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")

			for tour_id, desc in descriptions.items():
				cur.execute("UPDATE tour SET Description = %s WHERE TourID = %s", (desc, tour_id))
				print(f"Updated TourID={tour_id}, chars={len(desc)}")

		conn.commit()
		print("Done: charset + descriptions updated successfully.")
	finally:
		conn.close()


if __name__ == "__main__":
	main()