-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Máy chủ: 127.0.0.1
-- Thời gian đã tạo: Th8 29, 2025 lúc 05:58 PM
-- Phiên bản máy phục vụ: 10.4.32-MariaDB
-- Phiên bản PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Cơ sở dữ liệu: `tourbookingdb`
--

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `bank_txn`
--

CREATE TABLE `bank_txn` (
  `BankTxnID` int(11) NOT NULL,
  `Provider` varchar(50) NOT NULL,
  `ProviderRef` varchar(100) NOT NULL,
  `Amount` decimal(18,2) NOT NULL,
  `Description` varchar(255) DEFAULT NULL,
  `PaidAt` datetime NOT NULL,
  `RawPayload` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`RawPayload`)),
  `CreatedAt` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `bank_txn`
--

INSERT INTO `bank_txn` (`BankTxnID`, `Provider`, `ProviderRef`, `Amount`, `Description`, `PaidAt`, `RawPayload`, `CreatedAt`) VALUES
(1, 'manual', 'dev-001', 20000000.00, 'Chuyen tien ORDER20250829-F7922F', '2025-08-29 14:21:17', '{}', '2025-08-29 07:21:17');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `booking`
--

CREATE TABLE `booking` (
  `BookingID` int(11) NOT NULL,
  `UserID` int(11) DEFAULT NULL,
  `TourID` int(11) DEFAULT NULL,
  `BookingDate` date DEFAULT NULL,
  `NumberOfPeople` int(11) DEFAULT NULL,
  `TotalAmount` decimal(10,2) DEFAULT NULL,
  `Status` enum('Pending','Confirmed','Cancelled') DEFAULT 'Pending',
  `DiscountID` int(11) DEFAULT NULL,
  `OrderCode` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `booking`
--

INSERT INTO `booking` (`BookingID`, `UserID`, `TourID`, `BookingDate`, `NumberOfPeople`, `TotalAmount`, `Status`, `DiscountID`, `OrderCode`) VALUES
(9, 11, 30, '2025-08-29', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20250829-XE0MMF'),
(10, 12, 30, '2025-08-29', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20250829-OAAPUK'),
(11, 12, 30, '2025-08-29', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20250829-HAFRPY'),
(12, 12, 29, '2025-08-29', 6, 99999999.99, 'Confirmed', NULL, 'ORDER20250829-RAFGSP');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `category`
--

CREATE TABLE `category` (
  `CategoryID` int(11) NOT NULL,
  `CategoryName` varchar(100) NOT NULL,
  `Description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `category`
--

INSERT INTO `category` (`CategoryID`, `CategoryName`, `Description`) VALUES
(7, 'Du lịch trong nước', 'Cultural Tours'),
(10, 'Du lịch ngoài nước', 'History Tours');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `comment`
--

CREATE TABLE `comment` (
  `CommentID` int(11) NOT NULL,
  `UserID` int(11) DEFAULT NULL,
  `TourID` int(11) DEFAULT NULL,
  `Content` text DEFAULT NULL,
  `Rating` int(11) DEFAULT NULL CHECK (`Rating` >= 1 and `Rating` <= 5),
  `CreatedAt` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `comment`
--

INSERT INTO `comment` (`CommentID`, `UserID`, `TourID`, `Content`, `Rating`, `CreatedAt`) VALUES
(5, 8, 34, 'Quá đẹp !!!', 5, '2025-08-29 18:38:06'),
(6, 11, 30, 'hi', 5, '2025-08-29 21:37:25'),
(8, 12, 30, 'hi cho tui xin cảm nhận về chuyển đi', 5, '2025-08-29 21:48:41'),
(9, 12, 29, 'cho tui xin cảm nhận về tour', 5, '2025-08-29 22:51:33');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `discount`
--

CREATE TABLE `discount` (
  `DiscountID` int(11) NOT NULL,
  `Code` varchar(50) DEFAULT NULL,
  `Description` text DEFAULT NULL,
  `DiscountAmount` decimal(10,2) DEFAULT NULL,
  `IsPercent` tinyint(1) DEFAULT NULL,
  `StartDate` date DEFAULT NULL,
  `EndDate` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `discount`
--

INSERT INTO `discount` (`DiscountID`, `Code`, `Description`, `DiscountAmount`, `IsPercent`, `StartDate`, `EndDate`) VALUES
(3, 'MO1', '', 100.00, 1, '2025-08-01', '2025-08-31'),
(4, 'MO2', '', 200.00, 0, '2025-08-27', '2025-09-06');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `kv_store`
--

CREATE TABLE `kv_store` (
  `k` varchar(64) NOT NULL,
  `v` varchar(255) NOT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `payment`
--

CREATE TABLE `payment` (
  `PaymentID` int(11) NOT NULL,
  `BookingID` int(11) DEFAULT NULL,
  `Provider` varchar(50) NOT NULL DEFAULT 'manualqr',
  `OrderCode` varchar(50) NOT NULL,
  `PaymentDate` date DEFAULT NULL,
  `Amount` decimal(10,2) DEFAULT NULL,
  `Status` enum('Pending','Paid','Failed','Cancelled') NOT NULL DEFAULT 'Pending',
  `PaymentStatus` varchar(50) DEFAULT NULL,
  `PaymentMethod` enum('Credit Card','Bank Transfer') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `payment`
--

INSERT INTO `payment` (`PaymentID`, `BookingID`, `Provider`, `OrderCode`, `PaymentDate`, `Amount`, `Status`, `PaymentStatus`, `PaymentMethod`) VALUES
(1, 9, 'manualqr', 'ORDER20250829-XE0MMF', NULL, 3500000.00, 'Paid', NULL, NULL),
(2, 10, 'manualqr', 'ORDER20250829-OAAPUK', NULL, 3500000.00, 'Paid', NULL, NULL),
(3, 11, 'manualqr', 'ORDER20250829-HAFRPY', NULL, 3500000.00, 'Pending', NULL, NULL),
(4, 12, 'manualqr', 'ORDER20250829-RAFGSP', NULL, 99999999.99, 'Pending', NULL, NULL);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `photo`
--

CREATE TABLE `photo` (
  `PhotoID` int(11) NOT NULL,
  `TourID` int(11) DEFAULT NULL,
  `Caption` text DEFAULT NULL,
  `ImageURL` varchar(255) DEFAULT NULL,
  `UploadDate` date DEFAULT NULL,
  `IsPrimary` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `photo`
--

INSERT INTO `photo` (`PhotoID`, `TourID`, `Caption`, `ImageURL`, `UploadDate`, `IsPrimary`) VALUES
(18, 18, 'hehe', 'https://upload.wikimedia.org/wikipedia/commons/f/f6/Bangkok_skytrain_sunset.jpg', '2025-08-29', 1),
(19, 18, 'Tour Bangkok – Pattaya', 'https://upload.wikimedia.org/wikipedia/commons/1/1c/Pattaya_from_Big_Buddha.jpg', '2025-08-29', 0),
(20, 18, 'Tour Bangkok – Pattaya', 'https://upload.wikimedia.org/wikipedia/commons/a/a0/Pattaya_coastline.jpg', '2025-08-29', 0),
(21, 18, 'Tour Bangkok – Pattaya', 'https://upload.wikimedia.org/wikipedia/commons/e/ec/Pattaya_beach_from_view_point.jpg', '2025-08-29', 0),
(22, 19, 'a1', 'https://upload.wikimedia.org/wikipedia/commons/0/03/Singapore_%28SG%29%2C_View_from_Marina_Bay_Sands%2C_Singapore_Flyer_--_2019_--_4720.jpg', '2025-08-29', 1),
(23, 19, 'a2', 'https://upload.wikimedia.org/wikipedia/commons/0/04/Kuala-Lumpur_Malaysia_Planetarium_Negara-02.jpg', '2025-08-29', 0),
(24, 19, 'Tour Singapore – Kuala Lumpur', 'https://upload.wikimedia.org/wikipedia/commons/5/5c/Singapore_%28SG%29%2C_Marina_Bay_--_2019_--_4735-9.jpg', '2025-08-29', 0),
(25, 19, 'Tour Singapore – Kuala Lumpur', 'https://upload.wikimedia.org/wikipedia/commons/8/87/Kuala_Lumpur_Malaysia_Federal-Territory-Mosque-03.jpg', '2025-08-29', 0),
(26, 20, 'a3', 'https://upload.wikimedia.org/wikipedia/commons/3/36/Lake_Kawaguchiko_Sakura_Mount_Fuji_4.JPG', '2025-08-29', 1),
(27, 20, 'Tokyo – Núi Phú Sĩ', 'https://upload.wikimedia.org/wikipedia/commons/3/35/Minato_City%2C_Tokyo%2C_Japan.jpg', '2025-08-29', 0),
(28, 20, 'Tokyo – Núi Phú Sĩ', 'https://upload.wikimedia.org/wikipedia/commons/d/d2/070203_MM21%26FUJI.jpg', '2025-08-29', 0),
(29, 20, 'Tokyo – Núi Phú Sĩ', 'https://upload.wikimedia.org/wikipedia/commons/c/c5/Tokyo_Shibuya_Scramble_Crossing_2018-10-09.jpg', '2025-08-29', 0),
(30, 21, 'Seoul – Nami – Everland', 'https://upload.wikimedia.org/wikipedia/commons/3/3f/Everland_Magic_tree.jpg', '2025-08-29', 1),
(31, 21, 'Seoul – Nami – Everland', 'https://upload.wikimedia.org/wikipedia/commons/5/53/13-08-08-hongkong-sky100-05.jpg', '2025-08-29', 0),
(32, 21, 'Seoul – Nami – Everland', 'https://upload.wikimedia.org/wikipedia/commons/b/b7/Korea-Yongin-Everland-04.jpg', '2025-08-29', 0),
(33, 21, 'Seoul – Nami – Everland', 'https://upload.wikimedia.org/wikipedia/commons/0/0b/View_of_Nami_Island.JPG', '2025-08-29', 0),
(34, 22, 'A2', 'https://upload.wikimedia.org/wikipedia/commons/c/cc/Kaohsiung_Taiwan_Kaohsiung-Confucius-Temple-01.jpg', '2025-08-29', 1),
(36, 22, 'Hong Kong – Ma Cao', 'https://upload.wikimedia.org/wikipedia/commons/a/aa/Kaohsiung_Music_Center_and_Lingyaliao_Railroad_Bridge_lit_with_Ukrainian_flag_colors_during_2022_Taiwan_Lantern_Festival_%28cropped%29.jpg', '2025-08-29', 0),
(37, 22, 'Hong Kong – Ma Cao', 'https://upload.wikimedia.org/wikipedia/commons/7/7c/Kaohsiung_Skyline_2020.jpg', '2025-08-29', 0),
(38, 22, 'Hong Kong – Ma Cao', 'https://upload.wikimedia.org/wikipedia/commons/3/36/Kaohsiung_Taiwan_Floating-dock-Jong-Shyn-01.jpg', '2025-08-29', 0),
(39, 23, 'Đài Bắc – Cao Hùng', 'https://upload.wikimedia.org/wikipedia/commons/5/53/13-08-08-hongkong-sky100-05.jpg', '2025-08-29', 1),
(40, 23, 'Đài Bắc – Cao Hùng', 'https://upload.wikimedia.org/wikipedia/commons/3/36/Kaohsiung_Taiwan_Floating-dock-Jong-Shyn-01.jpg', '2025-08-29', 0),
(41, 23, 'Đài Bắc – Cao Hùng', 'https://upload.wikimedia.org/wikipedia/commons/c/c9/Macao_Casino.jpg', '2025-08-29', 0),
(42, 23, 'Đài Bắc – Cao Hùng', 'https://upload.wikimedia.org/wikipedia/commons/c/cc/Kaohsiung_Taiwan_Kaohsiung-Confucius-Temple-01.jpg', '2025-08-29', 0),
(58, 29, 'hihi', 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Chateau_Versailles_Galerie_des_Glaces.jpg', '2025-08-29', 1),
(59, 29, 'Paris – Versailles', 'https://upload.wikimedia.org/wikipedia/commons/e/e6/Paris_Night.jpg', '2025-08-30', 0),
(60, 29, 'Paris – Versailles', 'https://upload.wikimedia.org/wikipedia/commons/7/76/Palace_of_Versailles_June_2010.jpg', '2025-08-30', 0),
(61, 30, 'hehe', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Ha_Long_Bay_on_a_sunny_day.jpg/1024px-Ha_Long_Bay_on_a_sunny_day.jpg?20130317160000', '2025-08-29', 1),
(62, 30, 'Tour Hạ Long', 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Ha_Long_bay_The_Kissing_Rocks.jpg/1024px-Ha_Long_bay_The_Kissing_Rocks.jpg?20070930062110', '2025-08-29', 0),
(63, 30, 'Tour Hạ Long', 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Junk_Halong_Bay_Vietnam.jpg/1024px-Junk_Halong_Bay_Vietnam.jpg?20070404184139', '2025-08-29', 0),
(64, 31, 'huhu', 'https://upload.wikimedia.org/wikipedia/commons/f/f8/Thacbac3.jpg', '2025-08-29', 1),
(65, 30, 'Tour Hạ Long', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Downtown_Sa_Pa%2C_Vietnam.jpg/960px-Downtown_Sa_Pa%2C_Vietnam.jpg?20061206071242', '2025-08-29', 0),
(66, 30, 'Tour Hạ Long', 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Th%E1%BB%8B_tr%E1%BA%A5n_Sa_Pa.jpg', '2025-08-29', 0),
(67, 32, 'hihihi', 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/V%C3%A0o_%C4%91%E1%BB%99ng_Phong_Nha.jpg/800px-V%C3%A0o_%C4%91%E1%BB%99ng_Phong_Nha.jpg?20130130203259', '2025-08-29', 1),
(68, 32, 'Tour Phong Nha – Kẻ Bàng', 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Phong_Nha-Ke_Bang_cave3.jpg/1024px-Phong_Nha-Ke_Bang_cave3.jpg?20170826060800', '2025-08-29', 0),
(69, 32, 'Tour Phong Nha – Kẻ Bàng', 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Phong_Nha_cave_entrance.jpg/1024px-Phong_Nha_cave_entrance.jpg?20170826074802', '2025-08-29', 0),
(70, 33, 'hoho', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Hoi_An_%2842681823051%29.jpg/1024px-Hoi_An_%2842681823051%29.jpg?20210825091940', '2025-08-29', 1),
(71, 33, 'Tour Hội An', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Hoi_An_%28I%29.jpg/1024px-Hoi_An_%28I%29.jpg?20200511155154', '2025-08-29', 0),
(72, 33, 'Tour Hội An', 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/H%E1%BB%99i_An%2C_Ancient_Town%2C_2020-01_CN-06.jpg/1024px-H%E1%BB%99i_An%2C_Ancient_Town%2C_2020-01_CN-06.jpg?20200413172513', '2025-08-29', 0),
(73, 33, 'Tour Hội An', 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Hoi_An%2C_Vietnam_%2825710326363%29.jpg/1024px-Hoi_An%2C_Vietnam_%2825710326363%29.jpg?20210805101551', '2025-08-29', 0),
(74, 34, 'hphphp', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Golden_Bridge%2C_Da_Nang_%28I%29.jpg/1024px-Golden_Bridge%2C_Da_Nang_%28I%29.jpg?20200512152124', '2025-08-29', 1),
(75, 34, 'Tour Đà Nẵng', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Da_Nang_Dragon_Bridge_2020_IMG_4019.jpg/1024px-Da_Nang_Dragon_Bridge_2020_IMG_4019.jpg?20201116183400', '2025-08-29', 0),
(76, 34, 'Tour Đà Nẵng', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Lady_Buddha_in_Da_Nang%2C_Vietnam.jpg/800px-Lady_Buddha_in_Da_Nang%2C_Vietnam.jpg?20200226054138', '2025-08-29', 0),
(77, 35, 'mmomo', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/H%E1%BA%A1_Th%C3%A0nh%2C_H%C3%A0_Giang%2C_Vietnam_-_1.jpg/1024px-H%E1%BA%A1_Th%C3%A0nh%2C_H%C3%A0_Giang%2C_Vietnam_-_1.jpg?20230523172939', '2025-08-29', 1),
(78, 35, 'Tour Hà Giang', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/L%C3%B9ng_V%C3%A0i%2C_H%C3%A0_Giang%2C_Vietnam_-_4.jpg/1024px-L%C3%B9ng_V%C3%A0i%2C_H%C3%A0_Giang%2C_Vietnam_-_4.jpg?20230523211908', '2025-08-29', 0),
(79, 35, 'Tour Hà Giang', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Ha_Giang_Loop.jpg/800px-Ha_Giang_Loop.jpg?20201216035542', '2025-08-29', 0),
(80, 36, 'nini', 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/B%C3%A3i_bi%E1%BB%83n_%C4%90%E1%BA%A5t_D%E1%BB%91c_C%C3%B4n_%C4%90%E1%BA%A3o_-_panoramio.jpg/1024px-B%C3%A3i_bi%E1%BB%83n_%C4%90%E1%BA%A5t_D%E1%BB%91c_C%C3%B4n_%C4%90%E1%BA%A3o_-_panoramio.jpg?2017', '2025-08-29', 1),
(81, 36, 'Tour Côn Đảo', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/C%C3%B4n_%C4%90%E1%BA%A3o_National_Park.jpg/1024px-C%C3%B4n_%C4%90%E1%BA%A3o_National_Park.jpg?20150310084203', '2025-08-29', 0),
(82, 36, 'Tour Côn Đảo', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Nh%C3%A0_t%C3%B9_C%C3%B4n_%C4%90%E1%BA%A3o.JPG/1024px-Nh%C3%A0_t%C3%B9_C%C3%B4n_%C4%90%E1%BA%A3o.JPG?20150224201534', '2025-08-29', 0),
(83, 37, 'dsadasdsa', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/CanThoFloatingMarket.jpg/1024px-CanThoFloatingMarket.jpg?20070201200653', '2025-08-29', 1),
(84, 37, 'Tour Miền Tây', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Floating_Market_-_Can_Tho_-_Vietnam.JPG/800px-Floating_Market_-_Can_Tho_-_Vietnam.JPG?20090716043855', '2025-08-29', 0),
(85, 37, 'Tour Miền Tây', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Bridge-can-tho-vietnam.jpg/1024px-Bridge-can-tho-vietnam.jpg?20090408232953', '2025-08-29', 0),
(86, 38, 'bibi', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Hanoi-montage-2020-2.jpg/800px-Hanoi-montage-2020-2.jpg?20200426040702', '2025-08-29', 1),
(87, 38, 'Tour Hà Nội', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Main_gate_of_the_Temple_of_Literature_in_Hanoi.jpg/800px-Main_gate_of_the_Temple_of_Literature_in_Hanoi.jpg?20200321175629', '2025-08-29', 0),
(88, 38, 'Tour Hà Nội', 'https://upload.wikimedia.org/wikipedia/commons/a/a3/Main_hall%2C_V%C4%83n_Mi%E1%BA%BFu%2C_Hanoi%2C_Vietnam_%282006%29.jpg', '2025-08-29', 0),
(89, 39, 'koko', 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Vietnam%2C_Mui_Ne_sand_dunes.jpg/1024px-Vietnam%2C_Mui_Ne_sand_dunes.jpg?20191102133206', '2025-08-29', 1),
(90, 39, 'Tour Mũi Né', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Mui_Ne.jpg/1024px-Mui_Ne.jpg?20071124092858', '2025-08-29', 0),
(91, 39, 'Tour Mũi Né', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Mui_Ne_Fairy_Stream.jpg/1024px-Mui_Ne_Fairy_Stream.jpg?20110421030756', '2025-08-29', 0),
(92, 40, 'lolo', 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Trang_An%2C_Ninh_Binh.jpg/960px-Trang_An%2C_Ninh_Binh.jpg?20241012165724', '2025-08-29', 1),
(93, 40, 'Tour Ninh Bình', 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Tam_Coc_Ninh_Binh_%2880286%29.jpg/1024px-Tam_Coc_Ninh_Binh_%2880286%29.jpg?20250330102045', '2025-08-29', 0),
(94, 40, 'Tour Ninh Bình', 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Ninh_Binh_Hoa_Lu_%2839891%29.jpg/1024px-Ninh_Binh_Hoa_Lu_%2839891%29.jpg?20250402231255', '2025-08-29', 0),
(95, 41, 'aoiaoaoa', 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Sunset_on_Phu_Quoc_island.jpg/1024px-Sunset_on_Phu_Quoc_island.jpg?20220224072954', '2025-08-29', 1),
(96, 41, 'Tour Phú Quốc', 'https://upload.wikimedia.org/wikipedia/commons/f/f8/Phu_Quoc_Southern_Islands.jpg?20071115072141', '2025-08-29', 0),
(97, 41, 'Tour Phú Quốc', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Beautiful_beach_on_Phu_Quoc_island_Vietnam_%2839543775721%29.jpg/1024px-Beautiful_beach_on_Phu_Quoc_island_Vietnam_%2839543775721%29.jpg?20180112232830', '2025-08-29', 0),
(98, 41, 'Tour Phú Quốc', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Phu_quoc_suoi_tranh.jpg/1024px-Phu_quoc_suoi_tranh.jpg?20090119150603', '2025-08-29', 0),
(99, 42, 'khohoh', 'https://upload.wikimedia.org/wikipedia/commons/c/cd/Sydneyoperahouse_at_night.jpg', '2025-08-29', 1),
(100, 42, 'Sydney – Blue Mountains', 'https://upload.wikimedia.org/wikipedia/commons/c/cc/Blue_Mountains%2C_Sydney%2C_Australia.png', '2025-08-29', 0),
(101, 42, 'Sydney – Blue Mountains', 'https://upload.wikimedia.org/wikipedia/commons/7/72/Jamison_Valley%2C_Blue_Mountains%2C_Australia_-_Nov_2008.jpg', '2025-08-29', 0),
(102, 43, 'Dubai – Abu Dhabi', 'https://upload.wikimedia.org/wikipedia/commons/0/0b/Old_Cultural_Dubai_Area.jpg', '2025-08-29', 1),
(103, 43, 'Dubai – Abu Dhabi', 'https://upload.wikimedia.org/wikipedia/commons/1/15/13-08-06-abu-dhabi-by-RalfR-088.jpg', '2025-08-29', 0),
(104, 43, 'Dubai – Abu Dhabi', 'https://upload.wikimedia.org/wikipedia/commons/0/06/Meeru_Island_Resort_and_Spa%2C_Maldives_%28Unsplash%29.jpg', '2025-08-29', 0),
(105, 44, 'Gia đình haha', 'https://www.sgtiepthi.vn/wp-content/uploads/2020/10/A%CC%89nh-1-Du-li%CC%A3ch-Da%CC%A3i-Vie%CC%A3%CC%82t-e1602339539191.jpg', '2025-08-29', 1),
(106, 44, 'Gia đình haha', 'https://www.sgtiepthi.vn/wp-content/uploads/2020/10/A%CC%89nh-1-Du-li%CC%A3ch-Da%CC%A3i-Vie%CC%A3%CC%82t-e1602339539191.jpg', '2025-08-29', 0);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `role`
--

CREATE TABLE `role` (
  `RoleID` int(11) NOT NULL,
  `RoleName` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `role`
--

INSERT INTO `role` (`RoleID`, `RoleName`) VALUES
(1, 'Admin'),
(3, 'User');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `support_message`
--

CREATE TABLE `support_message` (
  `id` int(11) NOT NULL,
  `thread_id` int(11) NOT NULL,
  `sender_id` int(11) DEFAULT NULL,
  `is_admin` tinyint(1) NOT NULL DEFAULT 0,
  `content` text NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `support_message`
--

INSERT INTO `support_message` (`id`, `thread_id`, `sender_id`, `is_admin`, `content`, `created_at`) VALUES
(1, 3, 5, 0, 'hi', '2025-08-26 15:27:28'),
(2, 3, 5, 0, 'hello', '2025-08-26 15:32:37'),
(3, 4, 8, 0, 'Xin chào', '2025-08-26 15:36:50'),
(4, 4, 8, 0, 'Xin chào admin', '2025-08-26 16:29:45'),
(5, 4, 6, 1, 'chào bạn', '2025-08-26 16:30:08'),
(6, 4, 8, 0, 'Bạn tên gì', '2025-08-26 16:30:47'),
(7, 4, 6, 1, 'Admin2', '2025-08-26 16:31:03'),
(8, 4, 8, 0, 'Tour nào rẻ nhất', '2025-08-26 16:31:16'),
(9, 4, 6, 1, 'Đà Lạt bạn nhé', '2025-08-26 16:31:30'),
(10, 4, 6, 1, 'Bạn muốn hỏi gì nữa không', '2025-08-26 16:38:58'),
(11, 4, 8, 0, 'không cảm ơn bạn', '2025-08-26 16:39:18'),
(12, 4, 8, 0, 'hello hello', '2025-08-26 16:48:47'),
(13, 4, 6, 1, 'Bạn cần giúp gì', '2025-08-26 16:49:08'),
(14, 4, 8, 0, 'Tour nào rẻ nhất', '2025-08-26 16:49:21'),
(15, 4, 6, 1, 'Hà Giang', '2025-08-26 16:49:48'),
(16, 4, 8, 0, 'ohhhhh', '2025-08-26 16:49:55'),
(17, 4, 8, 0, 'hi', '2025-08-26 16:51:02'),
(18, 4, 8, 0, 'hi', '2025-08-26 16:51:05'),
(19, 4, 8, 0, 'hu', '2025-08-26 16:51:06'),
(20, 4, 8, 0, 'hu', '2025-08-26 16:51:06'),
(21, 4, 8, 0, 'hu', '2025-08-26 16:51:07'),
(22, 4, 8, 0, 'hu', '2025-08-26 16:51:08'),
(23, 4, 8, 0, 'hu', '2025-08-26 16:51:08'),
(24, 4, 8, 0, 'hello', '2025-08-26 16:51:49'),
(25, 4, 6, 1, 'hi', '2025-08-26 16:52:00'),
(26, 4, 6, 1, 'Xin chào', '2025-08-26 16:52:09'),
(27, 3, 5, 0, 'Xin chào', '2025-08-26 16:54:54'),
(28, 3, 5, 0, 'Hello', '2025-08-26 16:55:11'),
(29, 3, 6, 1, 'Bạn cần giúp gì', '2025-08-26 16:55:19'),
(30, 4, 6, 1, 'Xin chào', '2025-08-26 17:07:19'),
(31, 4, 8, 0, 'hello', '2025-08-26 17:07:25'),
(32, 4, 6, 1, 'hello', '2025-08-26 17:07:57'),
(33, 4, 8, 0, 'có việc gì', '2025-08-26 17:13:42'),
(34, 4, 6, 1, 'Aloo', '2025-08-26 17:13:52'),
(35, 4, 6, 1, 'hi', '2025-08-26 17:16:47'),
(36, 4, 6, 1, 'hi1', '2025-08-26 17:17:34'),
(37, 4, 8, 0, 'hllo', '2025-08-26 17:17:39'),
(38, 4, 8, 0, 'alo', '2025-08-26 17:28:35'),
(39, 4, 6, 1, 'hả', '2025-08-26 17:28:40'),
(40, 4, 8, 0, 'hú', '2025-08-26 17:28:44'),
(41, 4, 8, 0, 'hi', '2025-08-26 17:29:37'),
(42, 4, 8, 0, 'Hello', '2025-08-26 17:34:03'),
(43, 4, 6, 1, 'Xin chào', '2025-08-26 17:34:12'),
(44, 4, 6, 1, 'hi', '2025-08-26 17:35:38'),
(45, 4, 6, 1, 'hi', '2025-08-26 17:40:30'),
(46, 4, 6, 1, 'Hello', '2025-08-26 17:42:34'),
(47, 4, 6, 1, 'Hello', '2025-08-26 17:42:57'),
(48, 4, 6, 1, 'Xin chào', '2025-08-26 17:43:10'),
(49, 4, 6, 1, 'chào chào', '2025-08-26 17:43:17'),
(50, 4, 6, 1, 'xin chào', '2025-08-26 17:43:59'),
(51, 4, 6, 1, 'hi', '2025-08-26 17:56:20'),
(52, 4, 6, 1, 'xin chào', '2025-08-26 17:56:31'),
(53, 4, 6, 1, 'xin chào', '2025-08-26 17:58:57'),
(54, 4, 6, 1, 'lại nữa', '2025-08-26 17:59:34'),
(55, 4, 6, 1, 'chào nhé', '2025-08-26 18:03:28'),
(56, 4, 8, 0, 'chào', '2025-08-26 18:03:40'),
(57, 4, 6, 1, 'Hello', '2025-08-26 18:03:52'),
(58, 4, 6, 1, 'Chào', '2025-08-26 18:04:18'),
(59, 4, 8, 0, 'Chào', '2025-08-26 18:04:22'),
(60, 4, 6, 1, 'chào', '2025-08-26 18:15:33'),
(61, 4, 8, 0, 'chào', '2025-08-26 18:15:38'),
(62, 4, 6, 1, 'How are you ?', '2025-08-26 18:17:33'),
(63, 4, 8, 0, 'Xin chào', '2025-08-26 18:25:19'),
(64, 4, 6, 1, 'Chào nhé', '2025-08-26 18:25:27'),
(65, 4, 6, 1, 'Bạn cần giúp gì', '2025-08-26 18:25:53'),
(66, 4, 8, 0, 'Giúp chọn tour', '2025-08-26 18:26:04'),
(67, 4, 8, 0, 'ALo', '2025-08-26 18:28:26'),
(68, 4, 6, 1, 'Alo', '2025-08-26 18:28:30'),
(69, 4, 8, 0, 'Lo', '2025-08-26 18:28:33'),
(70, 4, 6, 1, 'Xin chào', '2025-08-26 18:58:06'),
(71, 4, 6, 1, 'Chào nhé', '2025-08-26 19:00:36'),
(72, 4, 8, 0, 'chào', '2025-08-26 19:00:57'),
(73, 4, 6, 1, 'Chào chào', '2025-08-26 19:01:02'),
(74, 4, 8, 0, 'Xin chào', '2025-08-26 19:01:07'),
(75, 4, 8, 0, 'Thanh Lich', '2025-08-26 19:03:04'),
(76, 4, 6, 1, 'Thanh Thien', '2025-08-26 19:14:55'),
(77, 4, 8, 0, 'Thien Thanh', '2025-08-26 19:15:02'),
(78, 4, 8, 0, 'xin chào', '2025-08-26 19:18:07'),
(79, 4, 6, 1, 'Chào', '2025-08-26 19:18:11'),
(80, 4, 8, 0, 'Hí hí', '2025-08-26 19:18:15'),
(81, 3, 5, 0, 'Thanh Thien', '2025-08-26 19:19:40'),
(82, 3, 6, 1, 'Thien Thanh', '2025-08-26 19:19:55'),
(83, 3, 5, 0, 'Thanh Thien', '2025-08-26 19:21:49'),
(84, 3, 6, 1, 'Thanh Lich', '2025-08-26 19:34:55'),
(85, 3, 5, 0, 'Chào', '2025-08-26 19:35:17'),
(86, 3, 6, 1, 'hgi', '2025-08-26 19:35:21'),
(87, 3, 5, 0, 'Alo', '2025-08-26 19:35:25'),
(88, 3, 6, 1, 'hả', '2025-08-26 19:35:59'),
(89, 3, 5, 0, 'Xin chào', '2025-08-26 19:36:03'),
(90, 3, 6, 1, 'xin chào', '2025-08-26 19:36:37'),
(91, 3, 5, 0, 'chào', '2025-08-26 19:36:42'),
(92, 1, 7, 0, 'Hi', '2025-08-27 10:01:40'),
(93, 1, 6, 1, 'Hello', '2025-08-27 10:02:19'),
(94, 1, 7, 0, 'Xin chao', '2025-08-27 10:02:28'),
(95, 1, 6, 1, 'heelo', '2025-08-27 10:02:45'),
(96, 1, 7, 0, 'hi', '2025-08-27 10:02:55'),
(97, 6, 6, 1, 'hi', '2025-08-27 10:03:20'),
(98, 6, 6, 1, 'Hello', '2025-08-27 10:03:26'),
(99, 6, 6, 1, 'Hi', '2025-08-27 10:09:40'),
(100, 6, 6, 1, 'Hi', '2025-08-27 10:09:46'),
(101, 1, 7, 0, 'Xin chào', '2025-08-27 10:10:21'),
(102, 1, 6, 1, 'Tôi có thể giúp gì cho bạn', '2025-08-27 10:10:33'),
(103, 1, 7, 0, 'Tìm tour rẻ nhất', '2025-08-27 10:10:47'),
(104, 1, 7, 0, 'Chào', '2025-08-27 10:11:17'),
(105, 1, 6, 1, 'hello', '2025-08-27 10:12:28'),
(106, 1, 7, 0, 'chào', '2025-08-27 10:15:19'),
(107, 1, 6, 1, 'Chào', '2025-08-27 10:17:03'),
(108, 1, 7, 0, 'Chào', '2025-08-27 10:17:09'),
(109, 1, 7, 0, 'Xin chào', '2025-08-27 10:26:14'),
(110, 1, 6, 1, 'Hello', '2025-08-27 10:26:24'),
(111, 1, 7, 0, 'hi', '2025-08-27 10:27:10'),
(112, 1, 6, 1, 'Hi', '2025-08-27 10:27:13'),
(113, 4, 8, 0, 'Hi1', '2025-08-27 10:32:35'),
(114, 4, 6, 1, 'Xin chào', '2025-08-27 10:32:45'),
(115, 4, 8, 0, 'Xin chào', '2025-08-27 10:32:53'),
(116, 4, 6, 1, 'Xin chào', '2025-08-27 10:33:27'),
(117, 4, 6, 1, 'Halo', '2025-08-27 10:38:13'),
(118, 4, 8, 0, 'Chào', '2025-08-27 10:38:18'),
(119, 4, 8, 0, 'Xin chào', '2025-08-27 10:40:14'),
(120, 4, 6, 1, 'Chào', '2025-08-27 10:40:30'),
(121, 4, 6, 1, 'Chào', '2025-08-27 10:40:58'),
(122, 4, 6, 1, 'Chào', '2025-08-27 10:41:01'),
(123, 4, 6, 1, 'Chào', '2025-08-27 10:41:03'),
(124, 4, 6, 1, 'Chào', '2025-08-27 10:41:05'),
(125, 4, 6, 1, 'chào', '2025-08-27 10:41:17'),
(126, 4, 6, 1, 'Hello', '2025-08-27 10:41:49'),
(127, 4, 8, 0, 'Chào', '2025-08-27 10:42:00'),
(128, 4, 6, 1, 'chào', '2025-08-27 10:43:35'),
(129, 4, 8, 0, 'chào', '2025-08-27 10:43:52'),
(130, 4, 6, 1, 'chào nhé', '2025-08-27 10:43:58'),
(131, 4, 6, 1, 'Xin chào', '2025-08-27 10:44:43'),
(132, 4, 8, 0, 'Chào', '2025-08-27 10:45:15'),
(133, 4, 6, 1, 'chào nhé', '2025-08-27 10:59:46'),
(134, 4, 6, 1, 'Chài', '2025-08-27 11:00:31'),
(135, 4, 8, 0, 'hi', '2025-08-27 11:00:34'),
(136, 4, 6, 1, 'Hello', '2025-08-27 11:10:49'),
(137, 4, 8, 0, 'Xin chào', '2025-08-27 11:11:54'),
(138, 4, 8, 0, 'Chào nhé', '2025-08-27 11:12:11'),
(139, 4, 6, 1, 'xin chào', '2025-08-27 11:24:28'),
(140, 4, 8, 0, 'Xin chào', '2025-08-27 11:24:35'),
(141, 4, 6, 1, 'Hi', '2025-08-27 11:25:44'),
(142, 4, 8, 0, 'hi', '2025-08-27 11:25:51'),
(143, 4, 8, 0, '1', '2025-08-27 11:45:37'),
(144, 4, 6, 1, '2', '2025-08-27 11:45:55'),
(145, 4, 8, 0, '3', '2025-08-27 11:46:01'),
(146, 4, 6, 1, '4', '2025-08-27 11:46:38'),
(147, 4, 8, 0, '5', '2025-08-27 11:46:43'),
(148, 4, 6, 1, '6', '2025-08-27 11:46:50'),
(149, 4, 6, 1, '7', '2025-08-27 12:02:54'),
(150, 4, 8, 0, '8', '2025-08-27 12:02:58'),
(151, 4, 6, 1, '9', '2025-08-27 12:09:23'),
(152, 4, 8, 0, '10', '2025-08-27 12:09:27'),
(153, 4, 6, 1, '11', '2025-08-27 12:13:07'),
(154, 4, 8, 0, '12', '2025-08-27 12:13:35'),
(155, 4, 8, 0, '123', '2025-08-27 12:13:55'),
(156, 4, 8, 0, '14', '2025-08-27 12:14:13'),
(157, 4, 6, 1, '15', '2025-08-27 12:14:15'),
(158, 4, 8, 0, '16', '2025-08-27 12:15:01'),
(159, 4, 6, 1, '17', '2025-08-27 12:15:04'),
(160, 4, 8, 0, '18', '2025-08-27 12:23:03'),
(161, 4, 6, 1, '19', '2025-08-27 12:23:12'),
(162, 4, 8, 0, '20', '2025-08-27 12:23:18'),
(163, 4, 6, 1, '21', '2025-08-27 12:23:25'),
(164, 4, 8, 0, '22', '2025-08-27 12:24:32'),
(165, 4, 6, 1, '23', '2025-08-27 12:24:51'),
(166, 4, 8, 0, '24', '2025-08-27 12:25:13'),
(167, 4, 6, 1, '25', '2025-08-27 12:25:16'),
(168, 4, 6, 1, '26', '2025-08-27 12:25:22'),
(169, 4, 6, 1, '27', '2025-08-27 12:25:24'),
(170, 4, 8, 0, '29', '2025-08-27 12:25:27'),
(171, 4, 6, 1, '30', '2025-08-27 12:29:46'),
(172, 4, 8, 0, '31', '2025-08-27 12:30:24'),
(173, 4, 6, 1, '32', '2025-08-27 12:30:31'),
(174, 4, 8, 0, '33', '2025-08-27 12:30:43'),
(175, 4, 6, 1, '34', '2025-08-27 12:33:24'),
(176, 4, 8, 0, '35', '2025-08-27 12:33:28'),
(177, 4, 6, 1, '36', '2025-08-27 12:34:13'),
(178, 4, 8, 0, '37', '2025-08-27 12:35:36'),
(179, 4, 6, 1, '38', '2025-08-27 12:35:54'),
(180, 4, 8, 0, '39', '2025-08-27 12:35:58'),
(181, 4, 6, 1, '40', '2025-08-27 12:37:37'),
(182, 4, 8, 0, '41', '2025-08-27 12:37:47'),
(183, 4, 6, 1, '42', '2025-08-27 12:37:51'),
(184, 4, 8, 0, '43', '2025-08-27 12:40:57'),
(185, 4, 6, 1, '44', '2025-08-27 12:41:36'),
(186, 4, 8, 0, '45', '2025-08-27 12:41:50'),
(187, 4, 6, 1, '46', '2025-08-27 12:42:00'),
(188, 4, 8, 0, '47', '2025-08-27 12:42:16'),
(189, 4, 6, 1, '48', '2025-08-27 12:42:19'),
(190, 4, 8, 0, '49', '2025-08-27 12:42:23'),
(191, 4, 6, 1, '49', '2025-08-27 12:42:43'),
(192, 4, 8, 0, '50', '2025-08-27 12:42:46'),
(193, 4, 8, 0, '54', '2025-08-27 12:42:59'),
(194, 4, 6, 1, '55', '2025-08-27 12:43:02'),
(195, 4, 8, 0, '56', '2025-08-27 12:43:06'),
(196, 4, 6, 1, '57', '2025-08-27 12:43:09'),
(197, 4, 8, 0, '58', '2025-08-27 12:44:47'),
(198, 4, 6, 1, '59', '2025-08-27 12:44:52'),
(199, 4, 8, 0, '60', '2025-08-27 12:45:01'),
(200, 4, 6, 1, '61', '2025-08-27 12:45:12'),
(201, 4, 8, 0, '62', '2025-08-27 12:45:26'),
(202, 4, 6, 1, '62', '2025-08-27 12:45:49'),
(203, 4, 8, 0, '63', '2025-08-27 12:50:55'),
(204, 4, 6, 1, '64', '2025-08-27 12:51:05'),
(205, 4, 8, 0, '65', '2025-08-27 12:51:12'),
(206, 4, 6, 1, '66', '2025-08-27 12:51:45'),
(207, 4, 8, 0, '67', '2025-08-27 12:51:49'),
(208, 4, 8, 0, 'hi', '2025-08-27 12:56:02'),
(209, 4, 6, 1, '37', '2025-08-27 12:56:07'),
(210, 4, 8, 0, '38', '2025-08-27 12:56:10'),
(211, 4, 6, 1, '39', '2025-08-27 12:57:13'),
(212, 4, 8, 0, '40', '2025-08-27 12:57:18'),
(213, 4, 6, 1, '41', '2025-08-27 12:57:23'),
(214, 4, 6, 1, '42', '2025-08-27 12:57:27'),
(215, 4, 6, 1, '42', '2025-08-27 12:57:28'),
(216, 4, 6, 1, '44', '2025-08-27 12:57:29'),
(217, 4, 6, 1, '45', '2025-08-27 12:57:32'),
(218, 4, 6, 1, '46', '2025-08-27 12:58:03'),
(219, 4, 6, 1, '47', '2025-08-27 12:58:06'),
(220, 4, 6, 1, '49', '2025-08-27 13:00:37'),
(221, 4, 8, 0, '50', '2025-08-27 13:00:42'),
(222, 4, 6, 1, '51', '2025-08-27 13:01:10'),
(223, 4, 8, 0, '52', '2025-08-27 13:01:35'),
(224, 4, 6, 1, '53', '2025-08-27 13:01:38'),
(225, 4, 8, 0, '54', '2025-08-27 13:03:05'),
(226, 4, 6, 1, '55', '2025-08-27 13:09:13'),
(227, 4, 6, 1, '56', '2025-08-27 13:09:18'),
(228, 4, 8, 0, '57', '2025-08-27 13:09:22'),
(229, 4, 6, 1, '59', '2025-08-27 13:09:43'),
(230, 4, 6, 1, '60', '2025-08-27 13:09:46'),
(231, 4, 8, 0, '61', '2025-08-27 13:09:49'),
(232, 4, 8, 0, '62', '2025-08-27 13:11:13'),
(233, 4, 6, 1, '63', '2025-08-27 13:12:27'),
(234, 4, 8, 0, '64', '2025-08-27 13:13:41'),
(235, 4, 6, 1, '65', '2025-08-27 13:18:45'),
(236, 4, 8, 0, '66', '2025-08-27 13:18:48'),
(237, 4, 6, 1, '67', '2025-08-27 13:23:13'),
(238, 4, 8, 0, '68', '2025-08-27 13:25:14'),
(239, 4, 6, 1, '70', '2025-08-27 13:25:19'),
(240, 4, 6, 1, '71', '2025-08-27 13:25:22'),
(241, 4, 6, 1, '72', '2025-08-27 13:25:23'),
(242, 4, 6, 1, '73', '2025-08-27 13:25:25'),
(243, 4, 8, 0, '74', '2025-08-27 13:25:30'),
(244, 4, 8, 0, '68', '2025-08-27 13:29:23'),
(245, 4, 6, 1, '69', '2025-08-27 13:29:29'),
(246, 4, 6, 1, '68', '2025-08-27 13:31:07'),
(247, 4, 6, 1, '69', '2025-08-27 13:31:10'),
(248, 4, 6, 1, '69', '2025-08-27 13:33:28'),
(249, 4, 6, 1, '69', '2025-08-27 13:33:31'),
(250, 4, 8, 0, 'hi', '2025-08-27 13:38:20'),
(251, 4, 6, 1, 'Hi', '2025-08-27 13:38:27'),
(252, 4, 8, 0, 'Hi', '2025-08-27 13:39:25'),
(253, 4, 8, 0, '68', '2025-08-27 13:40:04'),
(254, 4, 6, 1, '69', '2025-08-27 13:40:15'),
(255, 4, 6, 1, '70', '2025-08-27 13:40:17'),
(256, 4, 6, 1, '71', '2025-08-27 13:40:20'),
(257, 4, 8, 0, '82', '2025-08-27 13:40:23'),
(258, 4, 8, 0, '68', '2025-08-27 13:41:49'),
(259, 4, 8, 0, '68', '2025-08-27 13:43:59'),
(260, 4, 6, 1, '69', '2025-08-27 13:44:03'),
(261, 4, 6, 1, '68', '2025-08-27 13:54:08'),
(262, 4, 6, 1, '69', '2025-08-27 13:54:11'),
(263, 4, 8, 0, '70', '2025-08-27 13:54:14'),
(264, 4, 8, 0, '71', '2025-08-27 13:54:16'),
(265, 4, 6, 1, '72', '2025-08-27 13:54:23'),
(266, 4, 6, 1, '73', '2025-08-27 13:54:25'),
(267, 7, 10, 0, 'Xin chào', '2025-08-27 18:12:23'),
(268, 7, 10, 0, 'Xin chào', '2025-08-27 18:19:28'),
(269, 7, NULL, 1, 'Chào User 1, bạn cần giúp gì không? Chúng tôi sẽ phản hồi sớm nhất có thể. Xin cảm ơn!', '2025-08-27 18:19:28'),
(270, 7, 10, 0, 'Xin chào', '2025-08-27 18:22:46'),
(271, 7, 6, 1, 'Bạn cần giúp gì', '2025-08-27 18:23:15'),
(272, 7, 10, 0, 'Tour nào rẻ', '2025-08-27 18:23:23'),
(273, 7, 10, 0, 'Xin chào', '2025-08-27 18:29:18'),
(274, 7, NULL, 1, 'Chào User 1 👋🥰, bạn cần giúp gì không? Chúng tôi sẽ phản hồi sớm nhất có thể. Xin cảm ơn!', '2025-08-27 18:29:18'),
(275, 7, 10, 0, 'Tour nào rẻ nhất', '2025-08-27 18:29:48'),
(276, 7, NULL, 1, 'Chào User 1 👋🥰, bạn cần giúp gì không? Chúng tôi sẽ phản hồi sớm nhất có thể. Xin cảm ơn!', '2025-08-27 18:29:48'),
(277, 7, 6, 1, 'Tour Hội an bạn nhé', '2025-08-27 18:30:05'),
(278, 7, 10, 0, 'cảm ơn bạn', '2025-08-27 18:30:10'),
(279, 7, NULL, 1, 'Chào User 1 👋🥰, bạn cần giúp gì không? Chúng tôi sẽ phản hồi sớm nhất có thể. Xin cảm ơn!', '2025-08-27 18:30:10'),
(280, 7, 10, 0, 'Xin chào', '2025-08-27 18:35:33'),
(281, 7, 6, 1, 'Chào bạn', '2025-08-27 18:35:40'),
(282, 8, 11, 0, 'Xin chào', '2025-08-27 18:36:43'),
(283, 8, NULL, 1, 'Chào User 2 👋🥰, bạn cần giúp gì không? Chúng tôi sẽ phản hồi sớm nhất có thể. Xin cảm ơn!', '2025-08-27 18:36:43'),
(284, 8, 11, 0, 'Xin chào', '2025-08-27 18:36:56'),
(285, 8, 11, 0, 'Xin chào', '2025-08-27 18:37:15'),
(286, 8, 6, 1, 'Chào bạn', '2025-08-27 18:37:31'),
(287, 8, 11, 0, 'Tôi cần sự giúp đỡ', '2025-08-27 18:37:58'),
(288, 8, 6, 1, 'bạn cần giúp gì', '2025-08-27 18:38:09'),
(289, 6, 6, 1, 'ngày 1', '2025-08-29 10:08:39'),
(290, 9, 12, 0, 'tui muốn biết tui đã thanh toán xong chưa', '2025-08-29 21:49:34'),
(291, 9, NULL, 1, 'Chào Hồ  Thiện 👋🥰, bạn cần giúp gì không? Chúng tôi sẽ phản hồi sớm nhất có thể. Xin cảm ơn!', '2025-08-29 21:49:34'),
(292, 9, 1, 1, 'bạn yên tâm tour của bạn đã đặt thành công', '2025-08-29 21:50:49'),
(293, 9, 12, 0, 'hi hi', '2025-08-29 22:52:02'),
(294, 9, 12, 0, 'tui muốn biết tui đã đặt tour thafnnh công hay chhuaw', '2025-08-29 22:52:35'),
(295, 9, 1, 1, 'vâng bạn đã đặt tour tc', '2025-08-29 22:53:14');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `support_thread`
--

CREATE TABLE `support_thread` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `status` enum('open','closed') DEFAULT 'open',
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `support_thread`
--

INSERT INTO `support_thread` (`id`, `user_id`, `status`, `created_at`) VALUES
(1, 7, 'open', '2025-08-26 14:52:36'),
(3, 5, 'open', '2025-08-26 15:20:52'),
(4, 8, 'open', '2025-08-26 15:36:43'),
(6, 6, 'open', '2025-08-26 16:05:24'),
(7, 10, 'open', '2025-08-27 18:02:54'),
(8, 11, 'open', '2025-08-27 18:36:31'),
(9, 12, 'open', '2025-08-29 21:48:02');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `tour`
--

CREATE TABLE `tour` (
  `TourID` int(11) NOT NULL,
  `Title` varchar(100) NOT NULL,
  `Location` varchar(100) DEFAULT NULL,
  `Description` text DEFAULT NULL,
  `Capacity` int(11) DEFAULT NULL,
  `Price` decimal(10,2) DEFAULT NULL,
  `StartDate` date DEFAULT NULL,
  `EndDate` date DEFAULT NULL,
  `Status` enum('Available','Full','Cancelled') DEFAULT 'Available',
  `CategoryID` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `tour`
--

INSERT INTO `tour` (`TourID`, `Title`, `Location`, `Description`, `Capacity`, `Price`, `StartDate`, `EndDate`, `Status`, `CategoryID`) VALUES
(18, 'Tour Bangkok – Pattaya', 'Thái Lan', 'Khám phá thành phố biển Pattaya và thủ đô Bangkok sôi động.', 35, 12000000.00, '2025-10-04', '2025-08-06', 'Available', 10),
(19, 'Tour Singapore – Kuala Lumpur', 'Singapore – Malaysia', 'Tham quan Singapore hiện đại và Kuala Lumpur cổ kính.', 50, 15000000.00, '2025-10-07', '2025-10-09', 'Available', 10),
(20, 'Tokyo – Núi Phú Sĩ', 'Nhật Bản', 'Khám phá thủ đô Tokyo và ngắm cảnh Núi Phú Sĩ hùng vĩ.', 45, 32000000.00, '2025-10-10', '2025-10-12', 'Available', 10),
(21, 'Seoul – Nami – Everland', 'Hàn Quốc', 'Trải nghiệm Hàn Quốc qua Seoul, đảo Nami và công viên Everland.', 45, 25000000.00, '2025-10-13', '2025-10-15', 'Available', 10),
(22, 'Hong Kong – Ma Cao', 'Hong Kong – Macau', 'Tham quan Hong Kong hiện đại và sòng bạc Ma Cao nổi tiếng', 30, 20000000.00, '2025-10-16', '2025-10-18', 'Available', 10),
(23, 'Đài Bắc – Cao Hùng', 'Đài Loan', 'Khám phá Đài Bắc nhộn nhịp và thành phố Cao Hùng.', 30, 18000000.00, '2025-10-19', '2025-10-21', 'Available', 10),
(29, 'Paris – Versailles', 'Pháp', 'Dạo quanh Paris hoa lệ và cung điện Versailles lộng lẫy.', 25, 45000000.00, '2025-08-07', '2025-08-31', 'Available', 10),
(30, 'Tour Hạ Long', 'Quảng Ninh', 'Khám phá kỳ quan Vịnh Hạ Long.', 30, 3500000.00, '2025-08-01', '2025-08-27', 'Available', 7),
(31, 'Tour Sa Pa – Phan Xi Păng', 'Lào Cai', 'Leo núi Fansipan, thưởng sương Sa Pa.', 25, 4200000.00, '2025-08-16', '2025-08-19', 'Available', 7),
(32, 'Tour Phong Nha – Kẻ Bàng', 'Quảng Bình', 'Khám phá hang động kỳ vĩ Phong Nha.', 35, 3800000.00, '2025-08-29', '2025-09-01', 'Available', 7),
(33, 'Tour Hội An', 'Quảng Nam', 'Phố cổ Hội An về đêm lung linh.', 40, 2500000.00, '2025-08-08', '2025-08-14', 'Available', 7),
(34, 'Tour Đà Nẵng', 'Đà Nẵng', 'Khám phá biển Mỹ Khê và Bà Nà Hills.', 50, 4000000.00, '2025-08-08', '2025-08-10', 'Available', 7),
(35, 'Tour Hà Giang', 'Hà Giang', 'Cao nguyên đá Đồng Văn và Mã Pí Lèng.', 27, 3600000.00, '2025-08-29', '2025-09-05', 'Available', 7),
(36, 'Tour Côn Đảo', 'Bà Rịa – Vũng Tàu', 'Khám phá Côn Đảo huyền thoại.', 20, 5200000.00, '2025-08-15', '2025-09-06', 'Available', 7),
(37, 'Tour Miền Tây', 'Cần Thơ', 'Khám phá chợ nổi Cái Răng.', 36, 2900000.00, '2025-08-23', '2025-08-24', 'Available', 7),
(38, 'Tour Hà Nội', 'Hà Nội', 'Văn Miếu – Hồ Hoàn Kiếm – Lăng Bác.', 50, 3000000.00, '2025-08-30', '2025-08-31', 'Available', 7),
(39, 'Tour Mũi Né', 'Bình Thuận', 'Đồi cát bay và biển Mũi Né.', 38, 3300000.00, '2025-08-01', '2025-08-10', 'Available', 7),
(40, 'Tour Ninh Bình', 'Ninh Bình', 'Tràng An và Tam Cốc – Bích Động.', 32, 3100000.00, '2025-08-09', '2025-08-17', 'Available', 7),
(41, 'Tour Phú Quốc', 'Kiên Giang', 'Thiên đường biển đảo Phú Quốc.', 45, 5500000.00, '2025-08-02', '2025-08-12', 'Available', 7),
(42, 'Sydney – Blue Mountains', 'Úc', 'Tham quan Sydney và dãy núi Blue Mountains hùng vĩ.', 25, 40000000.00, '2025-08-02', '2025-08-12', 'Available', 10),
(43, 'Dubai – Abu Dhabi', 'UAE', 'Khám phá Dubai hiện đại và Abu Dhabi xa hoa.', 35, 38000000.00, '2025-08-28', '2025-08-31', 'Available', 10),
(44, 'Gia đình haha', 'Vĩnh Long', 'Du lịch sông nước', 100, 5000000.00, '2025-08-31', '2025-09-04', 'Available', 7);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `user`
--

CREATE TABLE `user` (
  `UserID` int(11) NOT NULL,
  `FirstName` varchar(50) DEFAULT NULL,
  `LastName` varchar(50) DEFAULT NULL,
  `FullName` varchar(100) DEFAULT NULL,
  `Password` varchar(100) NOT NULL,
  `Phone` varchar(20) DEFAULT NULL,
  `Email` varchar(100) DEFAULT NULL,
  `RoleID` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `user`
--

INSERT INTO `user` (`UserID`, `FirstName`, `LastName`, `FullName`, `Password`, `Phone`, `Email`, `RoleID`) VALUES
(1, 'Amin', '1', 'Admin1', '$2y$10$S6YFPPkwoSOPtBhfsBRSxulD.e2TeSBZw6s2uvB6nCFI6IqkYyT9u', '0122243434', 'admin1@gmail.com', 1),
(6, 'Admin', '2', 'Admin2', '$2y$10$3Ygpg279hGbflO1mLCUXi.6dXwz0M9ZejKZ1.ZtjoZt9QyqCZRn/y', '0122243434', 'admin3@gmail.com', 1),
(7, 'Thanh', 'Thien', 'Thanh Thien', '$2b$12$TL1tZjaaguIujfukSge3FeCYUK7D9GiiSVNwemjC377yWQgKjmS8m', '0222222222', 'thanhthien@gmail.com', 3),
(8, 'thanh', 'lich', 'Thanh Lich', '$2b$12$U6byv0BTym7K/0PchgD7o.Ua6A3DJp2xoBVeo563xQfm9QdHboome', '0111111111', 'thanhlich@gmail.com', 3),
(10, 'User', '1', 'User 1', '$2b$12$LKzFnEXoCkkijEcUe57HbO8JHDiDTcrIvuI4Ugb6LQBBbfzRsqi2S', '0222212121', 'user1@gmail.com', 3),
(11, 'User', '2', 'User2', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0222121212', 'user2@gmail.com', 3),
(12, 'Hồ ', 'Thiện', 'Hồ  Thiện', '$2b$12$73KIL1M57ISRadbpvdUDfeuBAy/rGExxki4RCvU3t4aGQI2mn4ary', '0375227764', 'thien@gmail.com', 3);

--
-- Chỉ mục cho các bảng đã đổ
--

--
-- Chỉ mục cho bảng `bank_txn`
--
ALTER TABLE `bank_txn`
  ADD PRIMARY KEY (`BankTxnID`),
  ADD UNIQUE KEY `ProviderRef` (`ProviderRef`);

--
-- Chỉ mục cho bảng `booking`
--
ALTER TABLE `booking`
  ADD PRIMARY KEY (`BookingID`),
  ADD UNIQUE KEY `OrderCode` (`OrderCode`),
  ADD KEY `UserID` (`UserID`),
  ADD KEY `TourID` (`TourID`),
  ADD KEY `DiscountID` (`DiscountID`);

--
-- Chỉ mục cho bảng `category`
--
ALTER TABLE `category`
  ADD PRIMARY KEY (`CategoryID`);

--
-- Chỉ mục cho bảng `comment`
--
ALTER TABLE `comment`
  ADD PRIMARY KEY (`CommentID`),
  ADD KEY `UserID` (`UserID`),
  ADD KEY `TourID` (`TourID`);

--
-- Chỉ mục cho bảng `discount`
--
ALTER TABLE `discount`
  ADD PRIMARY KEY (`DiscountID`),
  ADD UNIQUE KEY `Code` (`Code`);

--
-- Chỉ mục cho bảng `kv_store`
--
ALTER TABLE `kv_store`
  ADD PRIMARY KEY (`k`);

--
-- Chỉ mục cho bảng `payment`
--
ALTER TABLE `payment`
  ADD PRIMARY KEY (`PaymentID`),
  ADD KEY `BookingID` (`BookingID`);

--
-- Chỉ mục cho bảng `photo`
--
ALTER TABLE `photo`
  ADD PRIMARY KEY (`PhotoID`),
  ADD KEY `TourID` (`TourID`);

--
-- Chỉ mục cho bảng `role`
--
ALTER TABLE `role`
  ADD PRIMARY KEY (`RoleID`);

--
-- Chỉ mục cho bảng `support_message`
--
ALTER TABLE `support_message`
  ADD PRIMARY KEY (`id`),
  ADD KEY `thread_id` (`thread_id`);

--
-- Chỉ mục cho bảng `support_thread`
--
ALTER TABLE `support_thread`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uniq_user` (`user_id`);

--
-- Chỉ mục cho bảng `tour`
--
ALTER TABLE `tour`
  ADD PRIMARY KEY (`TourID`),
  ADD KEY `CategoryID` (`CategoryID`);

--
-- Chỉ mục cho bảng `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`UserID`),
  ADD UNIQUE KEY `Email` (`Email`),
  ADD KEY `RoleID` (`RoleID`);

--
-- AUTO_INCREMENT cho các bảng đã đổ
--

--
-- AUTO_INCREMENT cho bảng `bank_txn`
--
ALTER TABLE `bank_txn`
  MODIFY `BankTxnID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT cho bảng `booking`
--
ALTER TABLE `booking`
  MODIFY `BookingID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT cho bảng `category`
--
ALTER TABLE `category`
  MODIFY `CategoryID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT cho bảng `comment`
--
ALTER TABLE `comment`
  MODIFY `CommentID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT cho bảng `discount`
--
ALTER TABLE `discount`
  MODIFY `DiscountID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT cho bảng `payment`
--
ALTER TABLE `payment`
  MODIFY `PaymentID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT cho bảng `photo`
--
ALTER TABLE `photo`
  MODIFY `PhotoID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=107;

--
-- AUTO_INCREMENT cho bảng `role`
--
ALTER TABLE `role`
  MODIFY `RoleID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT cho bảng `support_message`
--
ALTER TABLE `support_message`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=296;

--
-- AUTO_INCREMENT cho bảng `support_thread`
--
ALTER TABLE `support_thread`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT cho bảng `tour`
--
ALTER TABLE `tour`
  MODIFY `TourID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=45;

--
-- AUTO_INCREMENT cho bảng `user`
--
ALTER TABLE `user`
  MODIFY `UserID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- Các ràng buộc cho các bảng đã đổ
--

--
-- Các ràng buộc cho bảng `booking`
--
ALTER TABLE `booking`
  ADD CONSTRAINT `booking_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`),
  ADD CONSTRAINT `booking_ibfk_2` FOREIGN KEY (`TourID`) REFERENCES `tour` (`TourID`),
  ADD CONSTRAINT `booking_ibfk_3` FOREIGN KEY (`DiscountID`) REFERENCES `discount` (`DiscountID`);

--
-- Các ràng buộc cho bảng `comment`
--
ALTER TABLE `comment`
  ADD CONSTRAINT `comment_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`),
  ADD CONSTRAINT `comment_ibfk_2` FOREIGN KEY (`TourID`) REFERENCES `tour` (`TourID`);

--
-- Các ràng buộc cho bảng `payment`
--
ALTER TABLE `payment`
  ADD CONSTRAINT `payment_ibfk_1` FOREIGN KEY (`BookingID`) REFERENCES `booking` (`BookingID`);

--
-- Các ràng buộc cho bảng `photo`
--
ALTER TABLE `photo`
  ADD CONSTRAINT `photo_ibfk_1` FOREIGN KEY (`TourID`) REFERENCES `tour` (`TourID`);

--
-- Các ràng buộc cho bảng `support_message`
--
ALTER TABLE `support_message`
  ADD CONSTRAINT `support_message_ibfk_1` FOREIGN KEY (`thread_id`) REFERENCES `support_thread` (`id`);

--
-- Các ràng buộc cho bảng `tour`
--
ALTER TABLE `tour`
  ADD CONSTRAINT `tour_ibfk_1` FOREIGN KEY (`CategoryID`) REFERENCES `category` (`CategoryID`);

--
-- Các ràng buộc cho bảng `user`
--
ALTER TABLE `user`
  ADD CONSTRAINT `user_ibfk_1` FOREIGN KEY (`RoleID`) REFERENCES `role` (`RoleID`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
