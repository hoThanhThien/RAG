-- Seed data for admin dashboard (tour revenue + clustering friendly data)
-- Categories used by business rule:
--   7  = Domestic (Trong nuoc)
--   10 = International (Ngoai nuoc)

SET @baseTour := (SELECT IFNULL(MAX(TourID), 0) FROM tour);

INSERT INTO tour (TourID, Title, Location, Description, Capacity, Price, StartDate, EndDate, Status, CategoryID) VALUES
(@baseTour + 1, 'Huế - Đà Nẵng Premium 3N2D', 'Đà Nẵng', 'Tour miền Trung cao cấp, trải nghiệm nghỉ dưỡng và ẩm thực.', 30, 4200000, '2026-05-10', '2026-05-12', 'Available', 7),
(@baseTour + 2, 'Phú Quốc Sunset Resort 4N3D', 'Phú Quốc', 'Nghỉ dưỡng biển cao cấp tại Phú Quốc.', 24, 6900000, '2026-05-18', '2026-05-21', 'Available', 7),
(@baseTour + 3, 'Sapa Trekking Fansipan 3N2D', 'Lào Cai', 'Khám phá núi rừng Tây Bắc và văn hóa bản địa.', 28, 3600000, '2026-06-03', '2026-06-05', 'Available', 7),
(@baseTour + 4, 'Mekong Cần Thơ - Châu Đốc 2N1D', 'Cần Thơ', 'Trải nghiệm chợ nổi và ẩm thực miền Tây.', 35, 2500000, '2026-06-12', '2026-06-13', 'Available', 7),
(@baseTour + 5, 'Seoul - Nami Signature 5N4D', 'Hàn Quốc', 'Tour Hàn Quốc mùa hoa, lịch trình signature.', 20, 16500000, '2026-07-02', '2026-07-06', 'Available', 10),
(@baseTour + 6, 'Tokyo - Fuji Premium 5N4D', 'Nhật Bản', 'Khám phá Tokyo và núi Phú Sĩ theo tiêu chuẩn premium.', 18, 19800000, '2026-07-10', '2026-07-14', 'Available', 10),
(@baseTour + 7, 'Paris - Switzerland Scenic 7N6D', 'Pháp', 'Hành trình châu Âu lãng mạn và cảnh quan đặc sắc.', 16, 36500000, '2026-08-04', '2026-08-10', 'Available', 10),
(@baseTour + 8, 'Sydney - Melbourne Discovery 6N5D', 'Úc', 'Tour Úc kết hợp hai thành phố nổi bật.', 18, 33800000, '2026-08-20', '2026-08-25', 'Available', 10);

SET @baseBooking := (SELECT IFNULL(MAX(BookingID), 0) FROM booking);

INSERT INTO booking (BookingID, UserID, TourID, BookingDate, NumberOfPeople, TotalAmount, Status, DiscountID, OrderCode, UpdatedAt) VALUES
(@baseBooking + 1, 14, @baseTour + 1, '2026-04-20', 2, 8400000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 1), NOW()),
(@baseBooking + 2, 15, @baseTour + 1, '2026-04-21', 3, 12600000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 2), NOW()),
(@baseBooking + 3, 16, @baseTour + 1, '2026-04-22', 1, 4200000, 'Pending', NULL, CONCAT('BKD_DEMO_', @baseBooking + 3), NOW()),

(@baseBooking + 4, 17, @baseTour + 2, '2026-04-20', 2, 13800000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 4), NOW()),
(@baseBooking + 5, 18, @baseTour + 2, '2026-04-21', 2, 13800000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 5), NOW()),
(@baseBooking + 6, 19, @baseTour + 2, '2026-04-23', 1, 6900000, 'Pending', NULL, CONCAT('BKD_DEMO_', @baseBooking + 6), NOW()),

(@baseBooking + 7, 20, @baseTour + 3, '2026-04-20', 3, 10800000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 7), NOW()),
(@baseBooking + 8, 21, @baseTour + 3, '2026-04-22', 2, 7200000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 8), NOW()),
(@baseBooking + 9, 22, @baseTour + 4, '2026-04-22', 4, 10000000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 9), NOW()),
(@baseBooking + 10, 23, @baseTour + 4, '2026-04-23', 2, 5000000, 'Pending', NULL, CONCAT('BKD_DEMO_', @baseBooking + 10), NOW()),

(@baseBooking + 11, 24, @baseTour + 5, '2026-04-19', 2, 33000000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 11), NOW()),
(@baseBooking + 12, 25, @baseTour + 5, '2026-04-21', 1, 16500000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 12), NOW()),

(@baseBooking + 13, 26, @baseTour + 6, '2026-04-20', 2, 39600000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 13), NOW()),
(@baseBooking + 14, 27, @baseTour + 6, '2026-04-21', 1, 19800000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 14), NOW()),

(@baseBooking + 15, 14, @baseTour + 7, '2026-04-20', 1, 36500000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 15), NOW()),
(@baseBooking + 16, 15, @baseTour + 7, '2026-04-22', 1, 36500000, 'Pending', NULL, CONCAT('BKD_DEMO_', @baseBooking + 16), NOW()),

(@baseBooking + 17, 16, @baseTour + 8, '2026-04-20', 1, 33800000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 17), NOW()),
(@baseBooking + 18, 17, @baseTour + 8, '2026-04-22', 2, 67600000, 'Confirmed', NULL, CONCAT('BKD_DEMO_', @baseBooking + 18), NOW());

SET @basePayment := (SELECT IFNULL(MAX(PaymentID), 0) FROM payment);

INSERT INTO payment (PaymentID, BookingID, Provider, OrderCode, PaymentDate, PaidAt, PaypalOrderID, PaypalTransactionID, UpdatedAt, Amount, Status, PaymentStatus, PaymentMethod) VALUES
(@basePayment + 1, @baseBooking + 1, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 1), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 1), CONCAT('PP_TX_', @basePayment + 1), NOW(), 8400000, 'Paid', NULL, NULL),
(@basePayment + 2, @baseBooking + 2, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 2), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 2), CONCAT('PP_TX_', @basePayment + 2), NOW(), 12600000, 'Paid', NULL, NULL),
(@basePayment + 3, @baseBooking + 3, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 3), NOW(), NULL, CONCAT('PP_OD_', @basePayment + 3), NULL, NOW(), 4200000, 'Pending', NULL, NULL),

(@basePayment + 4, @baseBooking + 4, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 4), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 4), CONCAT('PP_TX_', @basePayment + 4), NOW(), 13800000, 'Paid', NULL, NULL),
(@basePayment + 5, @baseBooking + 5, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 5), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 5), CONCAT('PP_TX_', @basePayment + 5), NOW(), 13800000, 'Paid', NULL, NULL),
(@basePayment + 6, @baseBooking + 6, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 6), NOW(), NULL, CONCAT('PP_OD_', @basePayment + 6), NULL, NOW(), 6900000, 'Pending', NULL, NULL),

(@basePayment + 7, @baseBooking + 7, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 7), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 7), CONCAT('PP_TX_', @basePayment + 7), NOW(), 10800000, 'Paid', NULL, NULL),
(@basePayment + 8, @baseBooking + 8, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 8), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 8), CONCAT('PP_TX_', @basePayment + 8), NOW(), 7200000, 'Paid', NULL, NULL),
(@basePayment + 9, @baseBooking + 9, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 9), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 9), CONCAT('PP_TX_', @basePayment + 9), NOW(), 10000000, 'Paid', NULL, NULL),
(@basePayment + 10, @baseBooking + 10, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 10), NOW(), NULL, CONCAT('PP_OD_', @basePayment + 10), NULL, NOW(), 5000000, 'Pending', NULL, NULL),

(@basePayment + 11, @baseBooking + 11, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 11), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 11), CONCAT('PP_TX_', @basePayment + 11), NOW(), 33000000, 'Paid', NULL, NULL),
(@basePayment + 12, @baseBooking + 12, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 12), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 12), CONCAT('PP_TX_', @basePayment + 12), NOW(), 16500000, 'Paid', NULL, NULL),

(@basePayment + 13, @baseBooking + 13, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 13), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 13), CONCAT('PP_TX_', @basePayment + 13), NOW(), 39600000, 'Paid', NULL, NULL),
(@basePayment + 14, @baseBooking + 14, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 14), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 14), CONCAT('PP_TX_', @basePayment + 14), NOW(), 19800000, 'Paid', NULL, NULL),

(@basePayment + 15, @baseBooking + 15, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 15), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 15), CONCAT('PP_TX_', @basePayment + 15), NOW(), 36500000, 'Paid', NULL, NULL),
(@basePayment + 16, @baseBooking + 16, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 16), NOW(), NULL, CONCAT('PP_OD_', @basePayment + 16), NULL, NOW(), 36500000, 'Pending', NULL, NULL),

(@basePayment + 17, @baseBooking + 17, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 17), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 17), CONCAT('PP_TX_', @basePayment + 17), NOW(), 33800000, 'Paid', NULL, NULL),
(@basePayment + 18, @baseBooking + 18, 'paypal', CONCAT('ODR_DEMO_', @baseBooking + 18), NOW(), NOW(), CONCAT('PP_OD_', @basePayment + 18), CONCAT('PP_TX_', @basePayment + 18), NOW(), 67600000, 'Paid', NULL, NULL);
