-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Máy chủ: nhom09_mysql
-- Thời gian đã tạo: Th4 21, 2026 lúc 11:53 AM
-- Phiên bản máy phục vụ: 8.0.44
-- Phiên bản PHP: 8.3.30

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
-- Cấu trúc bảng cho bảng `booking`
--

CREATE TABLE `booking` (
  `BookingID` int NOT NULL,
  `UserID` int DEFAULT NULL,
  `TourID` int DEFAULT NULL,
  `BookingDate` date DEFAULT NULL,
  `NumberOfPeople` int DEFAULT NULL,
  `TotalAmount` decimal(10,2) DEFAULT NULL,
  `Status` enum('Pending','Confirmed','Cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'Pending',
  `DiscountID` int DEFAULT NULL,
  `OrderCode` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `UpdatedAt` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `booking`
--

INSERT INTO `booking` (`BookingID`, `UserID`, `TourID`, `BookingDate`, `NumberOfPeople`, `TotalAmount`, `Status`, `DiscountID`, `OrderCode`, `UpdatedAt`) VALUES
(9, 11, 30, '2025-08-29', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20250829-XE0MMF', '2026-04-18 16:35:46'),
(10, 12, 30, '2025-08-29', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20250829-OAAPUK', '2026-04-18 16:35:46'),
(11, 12, 30, '2025-08-29', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20250829-HAFRPY', '2026-04-18 16:35:46'),
(13, 11, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-79BF3X', '2026-04-19 09:57:36'),
(14, 11, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-5AY0YZ', '2026-04-19 06:53:52'),
(15, 11, 43, '2026-04-19', 1, 38000000.00, 'Confirmed', NULL, 'ORDER20260419-I17DG3', '2026-04-19 07:31:18'),
(16, 11, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-P9D9X4', '2026-04-19 09:27:46'),
(17, 11, 18, '2026-04-19', 1, 12000000.00, 'Pending', NULL, 'ORDER20260419-GYM0IB', NULL),
(18, 11, 18, '2026-04-19', 1, 12000000.00, 'Confirmed', NULL, 'ORDER20260419-HFD9FI', '2026-04-19 09:43:19'),
(19, 11, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-HL7TGY', '2026-04-19 09:49:26'),
(20, 11, 20, '2026-04-19', 1, 32000000.00, 'Confirmed', NULL, 'ORDER20260419-1PL3P6', '2026-04-19 09:50:35'),
(21, 11, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-VUQR6M', '2026-04-19 09:58:56'),
(22, 11, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-8KUA8A', '2026-04-19 09:58:19'),
(23, 23, 30, '2026-04-19', 1, 3500000.00, 'Pending', NULL, 'ORDER20260419-45P6QV', NULL),
(24, 23, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-80UJE2', '2026-04-19 10:10:48'),
(25, 14, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-A10014', NULL),
(26, 15, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-A10015', NULL),
(27, 16, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-A10016', NULL),
(28, 17, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-A10017', NULL),
(29, 18, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-A10018', NULL),
(30, 19, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-A10019', NULL),
(31, 20, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-A10020', NULL),
(32, 21, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-A10021', NULL),
(33, 22, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-A10022', NULL),
(34, 23, 30, '2026-04-19', 1, 3500000.00, 'Confirmed', NULL, 'ORDER20260419-A10023', NULL),
(35, 24, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-B20024', NULL),
(36, 25, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-B20025', NULL),
(37, 26, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-B20026', NULL),
(38, 27, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-B20027', NULL),
(39, 28, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-B20028', NULL),
(40, 29, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-B20029', NULL),
(41, 30, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-B20030', NULL),
(42, 31, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-B20031', NULL),
(43, 32, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-B20032', NULL),
(44, 33, 31, '2026-04-19', 1, 4200000.00, 'Confirmed', NULL, 'ORDER20260419-B20033', NULL),
(45, 34, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30034', NULL),
(46, 35, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30035', NULL),
(47, 36, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30036', NULL),
(48, 37, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30037', NULL),
(49, 38, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30038', NULL),
(50, 39, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30039', NULL),
(51, 40, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30040', NULL),
(52, 41, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30041', NULL),
(53, 42, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30042', NULL),
(54, 43, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30043', NULL),
(55, 44, 40, '2026-04-19', 1, 3100000.00, 'Confirmed', NULL, 'ORDER20260419-C30044', NULL),
(56, 45, 44, '2026-04-19', 1, 5000000.00, 'Confirmed', NULL, 'ORDER20260419-D40045', NULL),
(57, 46, 44, '2026-04-19', 1, 5000000.00, 'Confirmed', NULL, 'ORDER20260419-D40046', NULL),
(58, 47, 44, '2026-04-19', 1, 5000000.00, 'Confirmed', NULL, 'ORDER20260419-D40047', NULL),
(59, 48, 44, '2026-04-19', 1, 5000000.00, 'Confirmed', NULL, 'ORDER20260419-D40048', NULL),
(60, 49, 44, '2026-04-19', 1, 5000000.00, 'Confirmed', NULL, 'ORDER20260419-D40049', NULL),
(61, 50, 44, '2026-04-19', 1, 5000000.00, 'Confirmed', NULL, 'ORDER20260419-D40050', NULL),
(62, 51, 44, '2026-04-19', 1, 5000000.00, 'Confirmed', NULL, 'ORDER20260419-D40051', NULL),
(63, 52, 44, '2026-04-19', 1, 5000000.00, 'Confirmed', NULL, 'ORDER20260419-D40052', NULL),
(64, 53, 44, '2026-04-19', 1, 5000000.00, 'Confirmed', NULL, 'ORDER20260419-D40053', NULL),
(65, 54, 44, '2026-04-19', 1, 5000000.00, 'Confirmed', NULL, 'ORDER20260419-D40054', NULL),
(66, 55, 29, '2026-04-19', 1, 45000000.00, 'Confirmed', NULL, 'ORDER20260419-E50055', NULL),
(67, 56, 42, '2026-04-19', 1, 40000000.00, 'Confirmed', NULL, 'ORDER20260419-E50056', NULL),
(68, 57, 43, '2026-04-19', 1, 38000000.00, 'Confirmed', NULL, 'ORDER20260419-E50057', NULL),
(69, 58, 20, '2026-04-19', 1, 32000000.00, 'Confirmed', NULL, 'ORDER20260419-E50058', NULL),
(70, 59, 21, '2026-04-19', 1, 25000000.00, 'Confirmed', NULL, 'ORDER20260419-E50059', NULL),
(71, 60, 22, '2026-04-19', 1, 20000000.00, 'Confirmed', NULL, 'ORDER20260419-E50060', NULL),
(72, 61, 22, '2026-04-19', 1, 20000000.00, 'Confirmed', NULL, 'ORDER20260419-E50061', NULL),
(73, 62, 18, '2026-04-19', 1, 12000000.00, 'Confirmed', NULL, 'ORDER20260419-E50062', NULL),
(74, 63, 18, '2026-04-19', 1, 12000000.00, 'Confirmed', NULL, 'ORDER20260419-E50063', NULL),
(75, 23, 31, '2026-04-19', 1, 0.00, 'Pending', 3, 'ORDER20260419-GW088O', NULL),
(76, 23, 31, '2026-04-19', 1, 4200000.00, 'Pending', 3, 'ORDER20260419-5NC2DU', '2026-04-19 13:12:27'),
(77, 23, 31, '2026-04-21', 1, 4200000.00, 'Pending', NULL, 'ORDER20260421-T4T0PF', NULL);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `category`
--

CREATE TABLE `category` (
  `CategoryID` int NOT NULL,
  `CategoryName` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `Description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
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
  `CommentID` int NOT NULL,
  `UserID` int DEFAULT NULL,
  `TourID` int DEFAULT NULL,
  `BookingID` int DEFAULT NULL,
  `Content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `Rating` int DEFAULT NULL,
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Đang đổ dữ liệu cho bảng `comment`
--

INSERT INTO `comment` (`CommentID`, `UserID`, `TourID`, `BookingID`, `Content`, `Rating`, `CreatedAt`) VALUES
(6, 11, 30, NULL, 'hi', 5, '2025-08-29 21:37:25'),
(8, 12, 30, NULL, 'hi cho tui xin cảm nhận về chuyển đi', 5, '2025-08-29 21:48:41'),
(9, 12, 29, NULL, 'cho tui xin cảm nhận về tour', 5, '2025-08-29 22:51:33'),
(10, 11, 31, NULL, 'xuất sắc', 1, '2026-04-19 09:28:26'),
(11, 11, 20, NULL, '123', 5, '2026-04-19 09:50:14'),
(12, 23, 31, NULL, 'dd', 5, '2026-04-19 12:12:16'),
(13, 23, 31, NULL, 'tttt', 5, '2026-04-19 12:12:48'),
(14, 23, 31, NULL, 'ttt', 5, '2026-04-19 13:03:09'),
(15, 23, 43, NULL, 'ggg', NULL, '2026-04-21 08:04:10');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `customer_segment`
--

CREATE TABLE `customer_segment` (
  `UserID` int NOT NULL,
  `ClusterID` int NOT NULL,
  `SegmentName` varchar(100) NOT NULL,
  `TotalSpending` decimal(15,2) DEFAULT '0.00',
  `OrderCount` int DEFAULT '0',
  `DaysSinceLastPurchase` int DEFAULT '9999',
  `DiscountUsageRate` decimal(6,4) DEFAULT '0.0000',
  `FavoriteCategory` varchar(255) DEFAULT NULL,
  `UpdatedAt` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Đang đổ dữ liệu cho bảng `customer_segment`
--

INSERT INTO `customer_segment` (`UserID`, `ClusterID`, `SegmentName`, `TotalSpending`, `OrderCount`, `DaysSinceLastPurchase`, `DiscountUsageRate`, `FavoriteCategory`, `UpdatedAt`) VALUES
(1, 2, 'Khách ít tương tác', 0.00, 0, 9999, 0.0000, 'General', '2026-04-19 16:09:20'),
(6, 2, 'Khách ít tương tác', 0.00, 0, 9999, 0.0000, 'General', '2026-04-19 16:09:20'),
(7, 2, 'Khách ít tương tác', 0.00, 0, 9999, 0.0000, 'General', '2026-04-19 16:09:20'),
(11, 1, 'Khách mua nhiều', 107800000.00, 10, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(12, 0, 'Khách ít tương tác', 7000000.00, 2, 233, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(13, 2, 'Khách ít tương tác', 0.00, 0, 9999, 0.0000, 'General', '2026-04-19 16:09:20'),
(14, 0, 'Khách ít tương tác', 3500000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(15, 0, 'Khách ít tương tác', 3500000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(16, 0, 'Khách ít tương tác', 3500000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(17, 0, 'Khách ít tương tác', 3500000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(18, 0, 'Khách ít tương tác', 3500000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(19, 0, 'Khách ít tương tác', 3500000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(20, 0, 'Khách ít tương tác', 3500000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(21, 0, 'Khách ít tương tác', 3500000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(22, 0, 'Khách ít tương tác', 3500000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(23, 0, 'Khách ít tương tác', 7700000.00, 2, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(24, 0, 'Khách ít tương tác', 4200000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(25, 0, 'Khách ít tương tác', 4200000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(26, 0, 'Khách ít tương tác', 4200000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(27, 0, 'Khách ít tương tác', 4200000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(28, 0, 'Khách ít tương tác', 4200000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(29, 0, 'Khách ít tương tác', 4200000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(30, 0, 'Khách ít tương tác', 4200000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(31, 0, 'Khách ít tương tác', 4200000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(32, 0, 'Khách ít tương tác', 4200000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(33, 0, 'Khách ít tương tác', 4200000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(34, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(35, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(36, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(37, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(38, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(39, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(40, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(41, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(42, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(43, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(44, 0, 'Khách ít tương tác', 3100000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(45, 0, 'Khách ít tương tác', 5000000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(46, 0, 'Khách ít tương tác', 5000000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(47, 0, 'Khách ít tương tác', 5000000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(48, 0, 'Khách ít tương tác', 5000000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(49, 0, 'Khách ít tương tác', 5000000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(50, 0, 'Khách ít tương tác', 5000000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(51, 0, 'Khách ít tương tác', 5000000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(52, 0, 'Khách ít tương tác', 5000000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(53, 0, 'Khách ít tương tác', 5000000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(54, 0, 'Khách ít tương tác', 5000000.00, 1, 0, 0.0000, 'Du lịch trong nước', '2026-04-19 16:09:20'),
(55, 3, 'Khách mua nhiều', 45000000.00, 1, 0, 0.0000, 'Du lịch ngoài nước', '2026-04-19 16:09:20'),
(56, 3, 'Khách mua nhiều', 40000000.00, 1, 0, 0.0000, 'Du lịch ngoài nước', '2026-04-19 16:09:20'),
(57, 3, 'Khách mua nhiều', 38000000.00, 1, 0, 0.0000, 'Du lịch ngoài nước', '2026-04-19 16:09:20'),
(58, 3, 'Khách mua nhiều', 32000000.00, 1, 0, 0.0000, 'Du lịch ngoài nước', '2026-04-19 16:09:20'),
(59, 3, 'Khách mua nhiều', 25000000.00, 1, 0, 0.0000, 'Du lịch ngoài nước', '2026-04-19 16:09:20'),
(60, 3, 'Khách mua nhiều', 20000000.00, 1, 0, 0.0000, 'Du lịch ngoài nước', '2026-04-19 16:09:20'),
(61, 3, 'Khách mua nhiều', 20000000.00, 1, 0, 0.0000, 'Du lịch ngoài nước', '2026-04-19 16:09:20'),
(62, 0, 'Khách ít tương tác', 12000000.00, 1, 0, 0.0000, 'Du lịch ngoài nước', '2026-04-19 16:09:20'),
(63, 0, 'Khách ít tương tác', 12000000.00, 1, 0, 0.0000, 'Du lịch ngoài nước', '2026-04-19 16:09:20');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `discount`
--

CREATE TABLE `discount` (
  `DiscountID` int NOT NULL,
  `Code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `Description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `DiscountAmount` decimal(10,2) DEFAULT NULL,
  `IsPercent` tinyint(1) DEFAULT NULL,
  `StartDate` date DEFAULT NULL,
  `EndDate` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `discount`
--

INSERT INTO `discount` (`DiscountID`, `Code`, `Description`, `DiscountAmount`, `IsPercent`, `StartDate`, `EndDate`) VALUES
(3, 'MO1', '', 100.00, 1, '2025-08-01', '2026-08-31'),
(4, 'MO2', '', 200.00, 1, '2025-08-27', '2026-09-06');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `payment`
--

CREATE TABLE `payment` (
  `PaymentID` int NOT NULL,
  `BookingID` int DEFAULT NULL,
  `Provider` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'manualqr',
  `OrderCode` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `PaymentDate` date DEFAULT NULL,
  `PaidAt` datetime DEFAULT NULL,
  `PaypalOrderID` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `PaypalTransactionID` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `UpdatedAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `Amount` decimal(10,2) DEFAULT NULL,
  `Status` enum('Pending','Paid','Failed','Cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'Pending',
  `PaymentStatus` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `PaymentMethod` enum('Credit Card','Bank Transfer') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `payment`
--

INSERT INTO `payment` (`PaymentID`, `BookingID`, `Provider`, `OrderCode`, `PaymentDate`, `PaidAt`, `PaypalOrderID`, `PaypalTransactionID`, `UpdatedAt`, `Amount`, `Status`, `PaymentStatus`, `PaymentMethod`) VALUES
(5, 13, 'paypal', 'ORDER20260419-79BF3X', NULL, '2026-04-19 09:57:36', '8DL17124JW554604K', '1SH29397MY893453L', '2026-04-19 09:57:36', 4200000.00, 'Paid', NULL, NULL),
(6, 14, 'paypal', 'ORDER20260419-5AY0YZ', NULL, '2026-04-19 06:53:53', '6FP68063B56888201', '0YC584561C018441D', '2026-04-19 06:53:52', 4200000.00, 'Paid', NULL, NULL),
(7, 15, 'paypal', 'ORDER20260419-I17DG3', NULL, '2026-04-19 07:31:19', '9N636416MD237172Y', '19581069CW627223H', '2026-04-19 07:31:18', 38000000.00, 'Paid', NULL, NULL),
(8, 16, 'paypal', 'ORDER20260419-P9D9X4', NULL, '2026-04-19 09:27:46', '98M99439HH9222544', '3FH9974234841622Y', '2026-04-19 09:27:46', 3100000.00, 'Paid', NULL, NULL),
(9, 17, 'manualqr', 'ORDER20260419-GYM0IB', NULL, NULL, NULL, NULL, '2026-04-19 09:40:53', 12000000.00, 'Pending', NULL, NULL),
(10, 18, 'paypal', 'ORDER20260419-HFD9FI', NULL, '2026-04-19 09:43:20', '4XN94719LX102352X', '2MP80967SU525863J', '2026-04-19 09:43:19', 12000000.00, 'Paid', NULL, NULL),
(11, 19, 'paypal', 'ORDER20260419-HL7TGY', NULL, '2026-04-19 09:49:26', '7VL99527KJ913724T', '4VP78088BW507931L', '2026-04-19 09:49:26', 4200000.00, 'Paid', NULL, NULL),
(12, 20, 'paypal', 'ORDER20260419-1PL3P6', NULL, '2026-04-19 09:50:35', '54348187J7475653E', '3M129002K38973525', '2026-04-19 09:50:35', 32000000.00, 'Paid', NULL, NULL),
(13, 21, 'paypal', 'ORDER20260419-VUQR6M', NULL, '2026-04-19 09:58:57', '2B032498PR614760K', '3MB507897Y9736728', '2026-04-19 09:58:56', 3500000.00, 'Paid', NULL, NULL),
(14, 22, 'paypal', 'ORDER20260419-8KUA8A', NULL, '2026-04-19 09:58:20', '6S862913RD2791727', '9N485807UA0625444', '2026-04-19 09:58:19', 3100000.00, 'Paid', NULL, NULL),
(15, 23, 'manualqr', 'ORDER20260419-45P6QV', NULL, NULL, '2ML686238H051734F', NULL, '2026-04-19 10:09:05', 3500000.00, 'Pending', NULL, NULL),
(16, 24, 'paypal', 'ORDER20260419-80UJE2', NULL, '2026-04-19 10:10:48', '2BH34567M1313334D', '8YA897860E227664R', '2026-04-19 10:10:48', 4200000.00, 'Paid', NULL, NULL),
(17, 23, 'paypal', 'ORDER20260419-A10014', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-A10014', 'TRANS-A10014', '2026-04-19 10:20:55', 3500000.00, 'Paid', NULL, NULL),
(18, 24, 'paypal', 'ORDER20260419-A10015', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-A10015', 'TRANS-A10015', '2026-04-19 10:20:55', 3500000.00, 'Paid', NULL, NULL),
(19, 25, 'paypal', 'ORDER20260419-A10016', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-A10016', 'TRANS-A10016', '2026-04-19 10:20:55', 3500000.00, 'Paid', NULL, NULL),
(20, 26, 'paypal', 'ORDER20260419-A10017', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-A10017', 'TRANS-A10017', '2026-04-19 10:20:55', 3500000.00, 'Paid', NULL, NULL),
(21, 27, 'paypal', 'ORDER20260419-A10018', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-A10018', 'TRANS-A10018', '2026-04-19 10:20:55', 3500000.00, 'Paid', NULL, NULL),
(22, 28, 'paypal', 'ORDER20260419-A10019', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-A10019', 'TRANS-A10019', '2026-04-19 10:20:55', 3500000.00, 'Paid', NULL, NULL),
(23, 29, 'paypal', 'ORDER20260419-A10020', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-A10020', 'TRANS-A10020', '2026-04-19 10:20:55', 3500000.00, 'Paid', NULL, NULL),
(24, 30, 'paypal', 'ORDER20260419-A10021', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-A10021', 'TRANS-A10021', '2026-04-19 10:20:55', 3500000.00, 'Paid', NULL, NULL),
(25, 31, 'paypal', 'ORDER20260419-A10022', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-A10022', 'TRANS-A10022', '2026-04-19 10:20:55', 3500000.00, 'Paid', NULL, NULL),
(26, 32, 'paypal', 'ORDER20260419-A10023', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-A10023', 'TRANS-A10023', '2026-04-19 10:20:55', 3500000.00, 'Paid', NULL, NULL),
(27, 33, 'paypal', 'ORDER20260419-B20024', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-B20024', 'TRANS-B20024', '2026-04-19 10:20:55', 4200000.00, 'Paid', NULL, NULL),
(28, 34, 'paypal', 'ORDER20260419-B20025', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-B20025', 'TRANS-B20025', '2026-04-19 10:20:55', 4200000.00, 'Paid', NULL, NULL),
(29, 35, 'paypal', 'ORDER20260419-B20026', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-B20026', 'TRANS-B20026', '2026-04-19 10:20:55', 4200000.00, 'Paid', NULL, NULL),
(30, 36, 'paypal', 'ORDER20260419-B20027', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-B20027', 'TRANS-B20027', '2026-04-19 10:20:55', 4200000.00, 'Paid', NULL, NULL),
(31, 37, 'paypal', 'ORDER20260419-B20028', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-B20028', 'TRANS-B20028', '2026-04-19 10:20:55', 4200000.00, 'Paid', NULL, NULL),
(32, 38, 'paypal', 'ORDER20260419-B20029', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-B20029', 'TRANS-B20029', '2026-04-19 10:20:55', 4200000.00, 'Paid', NULL, NULL),
(33, 39, 'paypal', 'ORDER20260419-B20030', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-B20030', 'TRANS-B20030', '2026-04-19 10:20:55', 4200000.00, 'Paid', NULL, NULL),
(34, 40, 'paypal', 'ORDER20260419-B20031', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-B20031', 'TRANS-B20031', '2026-04-19 10:20:55', 4200000.00, 'Paid', NULL, NULL),
(35, 41, 'paypal', 'ORDER20260419-B20032', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-B20032', 'TRANS-B20032', '2026-04-19 10:20:55', 4200000.00, 'Paid', NULL, NULL),
(36, 42, 'paypal', 'ORDER20260419-B20033', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-B20033', 'TRANS-B20033', '2026-04-19 10:20:55', 4200000.00, 'Paid', NULL, NULL),
(37, 43, 'paypal', 'ORDER20260419-C30034', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30034', 'TRANS-C30034', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(38, 44, 'paypal', 'ORDER20260419-C30035', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30035', 'TRANS-C30035', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(39, 45, 'paypal', 'ORDER20260419-C30036', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30036', 'TRANS-C30036', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(40, 46, 'paypal', 'ORDER20260419-C30037', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30037', 'TRANS-C30037', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(41, 47, 'paypal', 'ORDER20260419-C30038', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30038', 'TRANS-C30038', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(42, 48, 'paypal', 'ORDER20260419-C30039', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30039', 'TRANS-C30039', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(43, 49, 'paypal', 'ORDER20260419-C30040', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30040', 'TRANS-C30040', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(44, 50, 'paypal', 'ORDER20260419-C30041', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30041', 'TRANS-C30041', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(45, 51, 'paypal', 'ORDER20260419-C30042', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30042', 'TRANS-C30042', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(46, 52, 'paypal', 'ORDER20260419-C30043', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30043', 'TRANS-C30043', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(47, 53, 'paypal', 'ORDER20260419-C30044', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-C30044', 'TRANS-C30044', '2026-04-19 10:20:55', 3100000.00, 'Paid', NULL, NULL),
(48, 54, 'paypal', 'ORDER20260419-D40045', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-D40045', 'TRANS-D40045', '2026-04-19 10:20:55', 5000000.00, 'Paid', NULL, NULL),
(49, 55, 'paypal', 'ORDER20260419-D40046', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-D40046', 'TRANS-D40046', '2026-04-19 10:20:55', 5000000.00, 'Paid', NULL, NULL),
(50, 56, 'paypal', 'ORDER20260419-D40047', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-D40047', 'TRANS-D40047', '2026-04-19 10:20:55', 5000000.00, 'Paid', NULL, NULL),
(51, 57, 'paypal', 'ORDER20260419-D40048', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-D40048', 'TRANS-D40048', '2026-04-19 10:20:55', 5000000.00, 'Paid', NULL, NULL),
(52, 58, 'paypal', 'ORDER20260419-D40049', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-D40049', 'TRANS-D40049', '2026-04-19 10:20:55', 5000000.00, 'Paid', NULL, NULL),
(53, 59, 'paypal', 'ORDER20260419-D40050', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-D40050', 'TRANS-D40050', '2026-04-19 10:20:55', 5000000.00, 'Paid', NULL, NULL),
(54, 60, 'paypal', 'ORDER20260419-D40051', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-D40051', 'TRANS-D40051', '2026-04-19 10:20:55', 5000000.00, 'Paid', NULL, NULL),
(55, 61, 'paypal', 'ORDER20260419-D40052', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-D40052', 'TRANS-D40052', '2026-04-19 10:20:55', 5000000.00, 'Paid', NULL, NULL),
(56, 62, 'paypal', 'ORDER20260419-D40053', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-D40053', 'TRANS-D40053', '2026-04-19 10:20:55', 5000000.00, 'Paid', NULL, NULL),
(57, 63, 'paypal', 'ORDER20260419-D40054', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-D40054', 'TRANS-D40054', '2026-04-19 10:20:55', 5000000.00, 'Paid', NULL, NULL),
(58, 64, 'paypal', 'ORDER20260419-E50055', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-E50055', 'TRANS-E50055', '2026-04-19 10:20:55', 45000000.00, 'Paid', NULL, NULL),
(59, 65, 'paypal', 'ORDER20260419-E50056', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-E50056', 'TRANS-E50056', '2026-04-19 10:20:55', 40000000.00, 'Paid', NULL, NULL),
(60, 66, 'paypal', 'ORDER20260419-E50057', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-E50057', 'TRANS-E50057', '2026-04-19 10:20:55', 38000000.00, 'Paid', NULL, NULL),
(61, 67, 'paypal', 'ORDER20260419-E50058', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-E50058', 'TRANS-E50058', '2026-04-19 10:20:55', 32000000.00, 'Paid', NULL, NULL),
(62, 68, 'paypal', 'ORDER20260419-E50059', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-E50059', 'TRANS-E50059', '2026-04-19 10:20:55', 25000000.00, 'Paid', NULL, NULL),
(63, 69, 'paypal', 'ORDER20260419-E50060', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-E50060', 'TRANS-E50060', '2026-04-19 10:20:55', 20000000.00, 'Paid', NULL, NULL),
(64, 70, 'paypal', 'ORDER20260419-E50061', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-E50061', 'TRANS-E50061', '2026-04-19 10:20:55', 20000000.00, 'Paid', NULL, NULL),
(65, 71, 'paypal', 'ORDER20260419-E50062', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-E50062', 'TRANS-E50062', '2026-04-19 10:20:55', 12000000.00, 'Paid', NULL, NULL),
(66, 72, 'paypal', 'ORDER20260419-E50063', NULL, '2026-04-19 10:20:55', 'PAYPAL-ID-E50063', 'TRANS-E50063', '2026-04-19 10:20:55', 12000000.00, 'Paid', NULL, NULL),
(67, 75, 'manualqr', 'ORDER20260419-GW088O', NULL, NULL, NULL, NULL, '2026-04-19 10:40:36', 0.00, 'Pending', NULL, NULL),
(68, 76, 'manualqr', 'ORDER20260419-5NC2DU', NULL, NULL, NULL, NULL, '2026-04-19 10:40:51', -4200000.00, 'Pending', NULL, NULL),
(69, 77, 'manualqr', 'ORDER20260421-T4T0PF', NULL, NULL, NULL, NULL, '2026-04-21 10:39:26', 4200000.00, 'Pending', NULL, NULL);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `photo`
--

CREATE TABLE `photo` (
  `PhotoID` int NOT NULL,
  `TourID` int DEFAULT NULL,
  `Caption` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `ImageURL` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
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
(61, 30, 'hehe', 'https://upload.wikimedia.org/wikipedia/commons/2/2d/Halong_Bay_in_Vietnam.jpg', '2025-08-29', 1),
(62, 30, 'Tour Hạ Long', 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Ha_Long_bay_The_Kissing_Rocks.jpg/1024px-Ha_Long_bay_The_Kissing_Rocks.jpg?20070930062110', '2025-08-29', 0),
(64, 31, 'huhu', 'https://upload.wikimedia.org/wikipedia/commons/f/f8/Thacbac3.jpg', '2025-08-29', 1),
(92, 40, 'lolo', 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Trang_An%2C_Ninh_Binh.jpg/960px-Trang_An%2C_Ninh_Binh.jpg?20241012165724', '2025-08-29', 1),
(93, 40, 'Tour Ninh Bình', 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Tam_Coc_Ninh_Binh_%2880286%29.jpg/1024px-Tam_Coc_Ninh_Binh_%2880286%29.jpg?20250330102045', '2025-08-29', 0),
(94, 40, 'Tour Ninh Bình', 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Ninh_Binh_Hoa_Lu_%2839891%29.jpg/1024px-Ninh_Binh_Hoa_Lu_%2839891%29.jpg?20250402231255', '2025-08-29', 0),
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
  `RoleID` int NOT NULL,
  `RoleName` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL
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
  `id` int NOT NULL,
  `thread_id` int NOT NULL,
  `sender_id` int DEFAULT NULL,
  `is_admin` tinyint(1) NOT NULL DEFAULT '0',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
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
(295, 9, 1, 1, 'vâng bạn đã đặt tour tc', '2025-08-29 22:53:14'),
(299, 13, 13, 0, 'hihi', '2026-04-18 19:18:53'),
(300, 13, NULL, 1, 'Chào A I 👋🥰, bạn cần giúp gì không? Chúng tôi sẽ phản hồi sớm nhất có thể. Xin cảm ơn!', '2026-04-18 19:18:53'),
(301, 13, 1, 1, ',mm,,m', '2026-04-18 19:27:06'),
(302, 13, 1, 1, ',,,,', '2026-04-18 19:27:09'),
(303, 13, 1, 1, '4', '2026-04-18 19:44:59'),
(304, 13, 1, 1, 's', '2026-04-18 20:11:29'),
(305, 13, 1, 1, 'gfgf', '2026-04-18 21:06:56'),
(306, 13, 1, 1, 'dhgfkdg', '2026-04-18 21:06:59'),
(307, 13, 13, 0, 'g', '2026-04-18 22:10:21'),
(308, 13, 13, 0, 'gg', '2026-04-18 22:28:39'),
(309, 13, 13, 0, 'g', '2026-04-18 22:28:42'),
(310, 8, 11, 0, 'g', '2026-04-19 02:25:52'),
(311, 8, 1, 1, 'hi hi su su', '2026-04-19 05:50:43'),
(312, 8, 11, 0, 'ss', '2026-04-19 05:51:17'),
(313, 8, 11, 0, 's', '2026-04-19 05:51:32'),
(314, 8, 11, 0, 's', '2026-04-19 05:51:34'),
(315, 8, 11, 0, 'gâu gâu gâu', '2026-04-19 05:51:40'),
(316, 8, 1, 1, 'gấu gấu', '2026-04-19 05:52:11'),
(317, 8, 11, 0, '\'', '2026-04-19 09:48:57'),
(318, 8, 1, 1, 's', '2026-04-19 14:27:41'),
(319, 8, 11, 0, 'Gợi ý tour biển giá tốt', '2026-04-19 14:27:57'),
(320, 8, NULL, 1, '🤖 Trợ lý AI gợi ý cho bạn (VIP customers):\nGợi ý dành cho nhóm VIP customers:\n- Tour Ninh Bình tại Ninh Bình: giá 3,100,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Gia đình haha tại Vĩnh Long: giá 5,000,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\nTruy vấn gốc: Gợi ý tour biển giá tốt\nTour phù hợp:\n• Tour Ninh Bình - Ninh Bình - 3,100,000đ\n• Gia đình haha - Vĩnh Long - 5,000,000đ\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-19 14:27:57'),
(321, 8, 11, 0, 'Gợi ý tour biển giá tốt', '2026-04-19 14:28:04'),
(322, 8, NULL, 1, '🤖 Trợ lý AI gợi ý cho bạn (VIP customers):\nGợi ý dành cho nhóm VIP customers:\n- Tour Ninh Bình tại Ninh Bình: giá 3,100,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Gia đình haha tại Vĩnh Long: giá 5,000,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\nTruy vấn gốc: Gợi ý tour biển giá tốt\nTour phù hợp:\n• Tour Ninh Bình - Ninh Bình - 3,100,000đ\n• Gia đình haha - Vĩnh Long - 5,000,000đ\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-19 14:28:04'),
(323, 16, 11, 0, 'Tư vấn tour nghỉ dưỡng', '2026-04-19 14:28:13'),
(324, 16, NULL, 1, '🤖 Trợ lý AI gợi ý cho bạn (VIP customers):\nGợi ý dành cho nhóm VIP customers:\n- Tour Ninh Bình tại Ninh Bình: giá 3,100,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Gia đình haha tại Vĩnh Long: giá 5,000,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\nTruy vấn gốc: Tư vấn tour nghỉ dưỡng\nTour phù hợp:\n• Tour Ninh Bình - Ninh Bình - 3,100,000đ\n• Gia đình haha - Vĩnh Long - 5,000,000đ\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-19 14:28:13'),
(325, 16, 11, 0, 'Tư vấn tour nghỉ dưỡng', '2026-04-19 14:28:18'),
(326, 16, NULL, 1, '🤖 Trợ lý AI gợi ý cho bạn (VIP customers):\nGợi ý dành cho nhóm VIP customers:\n- Tour Ninh Bình tại Ninh Bình: giá 3,100,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Gia đình haha tại Vĩnh Long: giá 5,000,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\nTruy vấn gốc: Tư vấn tour nghỉ dưỡng\nTour phù hợp:\n• Tour Ninh Bình - Ninh Bình - 3,100,000đ\n• Gia đình haha - Vĩnh Long - 5,000,000đ\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-19 14:28:18'),
(327, 16, 11, 0, 'Gợi ý tour biển giá tốt', '2026-04-19 14:28:21'),
(328, 16, NULL, 1, '🤖 Trợ lý AI gợi ý cho bạn (VIP customers):\nGợi ý dành cho nhóm VIP customers:\n- Tour Ninh Bình tại Ninh Bình: giá 3,100,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Gia đình haha tại Vĩnh Long: giá 5,000,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\nTruy vấn gốc: Gợi ý tour biển giá tốt\nTour phù hợp:\n• Tour Ninh Bình - Ninh Bình - 3,100,000đ\n• Gia đình haha - Vĩnh Long - 5,000,000đ\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-19 14:28:21'),
(329, 16, 11, 0, 'trời nóng quá nên đi đâu', '2026-04-19 14:28:57'),
(330, 16, NULL, 1, '🤖 Trợ lý AI gợi ý cho bạn (VIP customers):\nGợi ý dành cho nhóm VIP customers:\n- Gia đình haha tại Vĩnh Long: giá 5,000,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\n- Tour Ninh Bình tại Ninh Bình: giá 3,100,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\nTruy vấn gốc: trời nóng quá nên đi đâu\nTour phù hợp:\n• Gia đình haha - Vĩnh Long - 5,000,000đ\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\n• Tour Ninh Bình - Ninh Bình - 3,100,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-19 14:28:57'),
(331, 8, 11, 0, 'tui rẻ nhất', '2026-04-19 14:30:54'),
(332, 8, 11, 0, 'trời nắng đi đâu', '2026-04-19 14:31:11'),
(333, 8, NULL, 1, '🤖 Trợ lý AI gợi ý cho bạn (VIP customers):\nGợi ý dành cho nhóm VIP customers:\n- Gia đình haha tại Vĩnh Long: giá 5,000,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\n- Tour Ninh Bình tại Ninh Bình: giá 3,100,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\nTruy vấn gốc: trời nắng đi đâu\nTour phù hợp:\n• Gia đình haha - Vĩnh Long - 5,000,000đ\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\n• Tour Ninh Bình - Ninh Bình - 3,100,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-19 14:31:11'),
(334, 8, 11, 0, 'tui muốn đi núi', '2026-04-19 14:31:20'),
(335, 8, 11, 0, 'goi y tour gia dinh test live', '2026-04-19 14:53:17'),
(336, 8, NULL, 1, '🤖 Trợ lý AI gợi ý cho bạn (VIP customers):\nGợi ý dành cho nhóm VIP customers:\n- Gia đình haha tại Vĩnh Long: giá 5,000,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Ninh Bình tại Ninh Bình: giá 3,100,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\nTruy vấn gốc: goi y tour gia dinh test live\nTour phù hợp:\n• Gia đình haha - Vĩnh Long - 5,000,000đ\n• Tour Ninh Bình - Ninh Bình - 3,100,000đ\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-19 14:53:17'),
(337, 8, 11, 0, 'Gợi ý tour biển giá tốt', '2026-04-19 14:58:38'),
(338, 8, NULL, 1, '🤖 Trợ lý AI gợi ý cho bạn (VIP customers):\nGợi ý dành cho nhóm VIP customers:\n- Tour Ninh Bình tại Ninh Bình: giá 3,100,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Gia đình haha tại Vĩnh Long: giá 5,000,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\nTruy vấn gốc: Gợi ý tour biển giá tốt\nTour phù hợp:\n• Tour Ninh Bình - Ninh Bình - 3,100,000đ\n• Gia đình haha - Vĩnh Long - 5,000,000đ\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-19 14:58:38'),
(341, 8, 11, 0, 'Gợi ý tour biển giá tốt', '2026-04-19 14:59:33'),
(342, 8, NULL, 1, '🤖 Trợ lý AI gợi ý cho bạn (VIP customers):\nGợi ý dành cho nhóm VIP customers:\n- Tour Ninh Bình tại Ninh Bình: giá 3,100,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Gia đình haha tại Vĩnh Long: giá 5,000,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 0.0.\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\nTruy vấn gốc: Gợi ý tour biển giá tốt\nTour phù hợp:\n• Tour Ninh Bình - Ninh Bình - 3,100,000đ\n• Gia đình haha - Vĩnh Long - 5,000,000đ\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-19 14:59:33'),
(394, 22, 23, 0, 'nống quá', '2026-04-21 07:56:38'),
(395, 22, NULL, 1, 'Chào Ngô Thị Bích 👋 Mình là trợ lý AI hỗ trợ du lịch. Bạn có thể hỏi ngay như: gợi ý tour gia đình, tour biển, tour giá rẻ hoặc tour nghỉ dưỡng.', '2026-04-21 07:56:38'),
(396, 22, 23, 0, 'nóng quá', '2026-04-21 07:56:48'),
(397, 21, 23, 0, 'u', '2026-04-21 07:56:57'),
(398, 21, NULL, 1, 'Chào Ngô Thị Bích 👋 Mình là trợ lý AI hỗ trợ du lịch. Bạn có thể hỏi ngay như: gợi ý tour gia đình, tour biển, tour giá rẻ hoặc tour nghỉ dưỡng.', '2026-04-21 07:56:57'),
(399, 21, 23, 0, 'nóng quá', '2026-04-21 07:57:02'),
(400, 21, 23, 0, 'nogns quá', '2026-04-21 07:57:17'),
(401, 21, 23, 0, 'nóng quá', '2026-04-21 07:57:24'),
(402, 23, 23, 0, 'nóng quá đi đâu', '2026-04-21 07:57:37'),
(403, 23, NULL, 1, '🤖 Gợi ý cho bạn:\nNếu trời đang nóng, bạn có thể ưu tiên các tour biển hoặc điểm đến mát mẻ sau:\n- Tour Hạ Long tại Quảng Ninh: giá 3,500,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 5.0.\n- Tour Sa Pa – Phan Xi Păng tại Lào Cai: giá 4,200,000 VND, hạng mục Du lịch trong nước, điểm đánh giá 4.0.\n- Sydney – Blue Mountains tại Úc: giá 40,000,000 VND, hạng mục Du lịch ngoài nước, điểm đánh giá 0.0.\nTruy vấn gốc: nóng quá đi đâu\nTour phù hợp:\n• Tour Hạ Long - Quảng Ninh - 3,500,000đ\n• Tour Sa Pa – Phan Xi Păng - Lào Cai - 4,200,000đ\n• Sydney – Blue Mountains - Úc - 40,000,000đ\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-21 07:57:37'),
(404, 23, 23, 0, 'nóng quá', '2026-04-21 07:57:50'),
(405, 21, 23, 0, 'nóng qyuas', '2026-04-21 09:54:32'),
(406, 23, 23, 0, 'nóng quá', '2026-04-21 09:54:43'),
(407, 24, 23, 0, 'hu', '2026-04-21 09:54:54'),
(408, 24, NULL, 1, 'Chào Ngô Thị Bích 👋 Mình là trợ lý AI hỗ trợ du lịch. Bạn có thể hỏi ngay như: gợi ý tour gia đình, tour biển, tour giá rẻ hoặc tour nghỉ dưỡng.', '2026-04-21 09:54:54'),
(409, 24, 23, 0, 'nóng quá đi\\', '2026-04-21 09:55:02'),
(410, 24, 23, 0, 'nóng quá', '2026-04-21 09:55:09'),
(411, 21, 23, 0, 'nóng quá', '2026-04-21 09:55:36'),
(412, 21, 23, 0, 'nóng quá', '2026-04-21 10:51:00'),
(413, 21, NULL, 1, '🤖 Gợi ý cho bạn:\nNếu đang nóng, bạn có thể cân nhắc các tour mát mẻ sau (Khách ít tương tác):\n- Tour Sa Pa – Phan Xi Păng ở Lào Cai, giá khoảng 4,200,000 VND, danh mục Du lịch trong nước; lý do: phù hợp để tránh nóng.\n- Tour Hạ Long ở Quảng Ninh, giá khoảng 3,500,000 VND, danh mục Du lịch trong nước; lý do: phù hợp để tránh nóng.\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-21 10:51:00'),
(414, 21, 23, 0, 'tui nuốn đi nước ngoài', '2026-04-21 10:51:26'),
(415, 21, NULL, 1, '🤖 Gợi ý cho bạn:\nGợi ý tour nước ngoài cho bạn (Khách ít tương tác):\n- Tour Bangkok – Pattaya ở Thái Lan, giá khoảng 12,000,000 VND, danh mục Du lịch ngoài nước.\n- Paris – Versailles ở Pháp, giá khoảng 45,000,000 VND, danh mục Du lịch ngoài nước.\n- Seoul – Nami – Everland ở Hàn Quốc, giá khoảng 25,000,000 VND, danh mục Du lịch ngoài nước.\nNếu bạn muốn, nhân viên vẫn có thể hỗ trợ thêm ngay trong cuộc trò chuyện này.', '2026-04-21 10:51:26');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `support_thread`
--

CREATE TABLE `support_thread` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `status` enum('open','closed') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'open',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
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
(9, 12, 'open', '2025-08-29 21:48:02'),
(12, 13, 'open', '2026-04-18 19:18:45'),
(13, 13, 'open', '2026-04-18 19:18:48'),
(14, 1, 'open', '2026-04-19 06:58:49'),
(16, 11, 'open', '2026-04-19 14:28:08'),
(21, 23, 'open', '2026-04-21 07:49:45'),
(22, 23, 'open', '2026-04-21 07:49:48'),
(23, 23, 'open', '2026-04-21 07:57:27'),
(24, 23, 'open', '2026-04-21 09:54:46');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `tour`
--

CREATE TABLE `tour` (
  `TourID` int NOT NULL,
  `Title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `Location` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `Description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `Capacity` int DEFAULT NULL,
  `Price` decimal(10,2) DEFAULT NULL,
  `StartDate` date DEFAULT NULL,
  `EndDate` date DEFAULT NULL,
  `Status` enum('Available','Full','Cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'Available',
  `CategoryID` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `tour`
--

INSERT INTO `tour` (`TourID`, `Title`, `Location`, `Description`, `Capacity`, `Price`, `StartDate`, `EndDate`, `Status`, `CategoryID`) VALUES
(18, 'Tour Bangkok – Pattaya', 'Thái Lan', 'Khám phá thành phố biển Pattaya và thủ đô Bangkok sôi động.', 35, 12000000.00, '2026-06-10', '2026-06-14', 'Available', 10),
(19, 'Tour Singapore – Kuala Lumpur', 'Singapore – Malaysia', 'Tham quan Singapore hiện đại và Kuala Lumpur cổ kính.', 50, 15000000.00, '2026-06-15', '2026-06-19', 'Available', 10),
(20, 'Tokyo – Núi Phú Sĩ', 'Nhật Bản', 'Khám phá thủ đô Tokyo và ngắm cảnh Núi Phú Sĩ hùng vĩ.', 45, 32000000.00, '2026-07-05', '2026-07-10', 'Available', 10),
(21, 'Seoul – Nami – Everland', 'Hàn Quốc', 'Trải nghiệm Hàn Quốc qua Seoul, đảo Nami và công viên Everland.', 45, 25000000.00, '2026-07-12', '2026-07-16', 'Available', 10),
(22, 'Hong Kong – Ma Cao', 'Hong Kong – Macau', 'Tham quan Hong Kong hiện đại và sòng bạc Ma Cao nổi tiếng', 30, 20000000.00, '2026-08-01', '2026-08-04', 'Available', 10),
(23, 'Đài Bắc – Cao Hùng', 'Đài Loan', 'Khám phá Đài Bắc nhộn nhịp và thành phố Cao Hùng.', 30, 18000000.00, '2026-08-10', '2026-08-14', 'Available', 10),
(29, 'Paris – Versailles', 'Pháp', 'Dạo quanh Paris hoa lệ và cung điện Versailles lộng lẫy.', 25, 45000000.00, '2026-09-01', '2026-09-08', 'Available', 10),
(30, 'Tour Hạ Long', 'Quảng Ninh', 'Khám phá kỳ quan Vịnh Hạ Long.', 30, 3500000.00, '2026-05-15', '2026-05-17', 'Available', 7),
(31, 'Tour Sa Pa – Phan Xi Păng', 'Lào Cai', 'Leo núi Fansipan, thưởng sương Sa Pa.', 25, 4200000.00, '2026-05-20', '2026-05-23', 'Available', 7),
(40, 'Tour Ninh Bình', 'Ninh Bình', 'Tràng An và Tam Cốc – Bích Động.', 32, 3100000.00, '2026-06-01', '2026-06-03', 'Available', 7),
(42, 'Sydney – Blue Mountains', 'Úc', 'Tham quan Sydney và dãy núi Blue Mountains hùng vĩ.', 25, 40000000.00, '2026-10-10', '2026-10-17', 'Available', 10),
(43, 'Dubai – Abu Dhabi', 'UAE', 'Khám phá Dubai hiện đại và Abu Dhabi xa hoa.', 35, 38000000.00, '2026-11-05', '2026-11-10', 'Available', 10),
(44, 'Gia đình haha', 'Vĩnh Long', 'Du lịch sông nước', 100, 5000000.00, '2026-05-25', '2026-05-26', 'Available', 7);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `user`
--

CREATE TABLE `user` (
  `UserID` int NOT NULL,
  `FirstName` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `LastName` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `FullName` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `Password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `Phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `Email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `RoleID` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `user`
--

INSERT INTO `user` (`UserID`, `FirstName`, `LastName`, `FullName`, `Password`, `Phone`, `Email`, `RoleID`) VALUES
(1, 'Amin', '1', 'Admin1', '$2y$10$S6YFPPkwoSOPtBhfsBRSxulD.e2TeSBZw6s2uvB6nCFI6IqkYyT9u', '0122243434', 'admin1@gmail.com', 1),
(6, 'Admin', '2', 'Admin2', '$2y$10$3Ygpg279hGbflO1mLCUXi.6dXwz0M9ZejKZ1.ZtjoZt9QyqCZRn/y', '0122243434', 'admin3@gmail.com', 1),
(7, 'Thanh', 'Thien', 'Thanh Thien', '$2b$12$TL1tZjaaguIujfukSge3FeCYUK7D9GiiSVNwemjC377yWQgKjmS8m', '0222222222', 'thanhthien@gmail.com', 3),
(11, 'User', '2', 'User2', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0222121212', 'user2@gmail.com', 3),
(12, 'Hồ ', 'Thiện', 'Hồ  Thiện', '$2b$12$73KIL1M57ISRadbpvdUDfeuBAy/rGExxki4RCvU3t4aGQI2mn4ary', '0375227764', 'thien@gmail.com', 3),
(13, 'A', 'I', 'A I', '$2b$12$VSvWphaPxrCBThx3AliH1.jMd5uy5uLeeqeqxPFyuLnd0us80n/5a', '0123455667', 'ai@gmail.com', 3),
(14, 'Đăng', 'Nguyễn Hải', 'Nguyễn Hải Đăng', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000001', 'nguyenhaidang@gmail.com', 3),
(15, 'Ngọc', 'Trần Bảo', 'Trần Bảo Ngọc', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000002', 'tranbaongoc@gmail.com', 3),
(16, 'Kiệt', 'Lê Tuấn', 'Lê Tuấn Kiệt', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000003', 'letuankiet@gmail.com', 3),
(17, 'Thảo', 'Phạm Thu', 'Phạm Thu Thảo', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000004', 'phamthuthao@gmail.com', 3),
(18, 'Minh', 'Vũ Hoàng', 'Vũ Hoàng Minh', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000005', 'vuhoangminh@gmail.com', 3),
(19, 'Dung', 'Đặng Thùy', 'Đặng Thùy Dung', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000006', 'dangthuydung@gmail.com', 3),
(20, 'Phát', 'Bùi Xuân', 'Bùi Xuân Phát', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000007', 'buixuanphat@gmail.com', 3),
(21, 'Phương', 'Đỗ Mai', 'Đỗ Mai Phương', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000008', 'domaiphuong@gmail.com', 3),
(22, 'Bảo', 'Hồ Quốc', 'Hồ Quốc Bảo', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000009', 'hoquocbao@gmail.com', 3),
(23, 'Bích', 'Ngô Thị', 'Ngô Thị Bích', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000010', 'ngothibich@gmail.com', 3),
(24, 'Trí', 'Dương Đức', 'Dương Đức Trí', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000011', 'duongductri@gmail.com', 3),
(25, 'Kỳ', 'Lý Nhã', 'Lý Nhã Kỳ', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000012', 'lynhaky@gmail.com', 3),
(26, 'Sơn', 'Hoàng Thanh', 'Hoàng Thanh Sơn', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000013', 'hoangthanhson@gmail.com', 3),
(27, 'Anh', 'Phan Quỳnh', 'Phan Quỳnh Anh', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000014', 'phanquynhanh@gmail.com', 3),
(28, 'Huy', 'Trương Quang', 'Trương Quang Huy', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000015', 'truongquanghuy@gmail.com', 3),
(29, 'Dũng', 'Vũ Tấn', 'Vũ Tấn Dũng', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000016', 'vutandung@gmail.com', 3),
(30, 'Phương', 'Nguyễn Minh', 'Nguyễn Minh Phương', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000017', 'nguyenminhphuong@gmail.com', 3),
(31, 'My', 'Lê Hà', 'Lê Hà My', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000018', 'lehamy@gmail.com', 3),
(32, 'Anh', 'Trần Đức', 'Trần Đức Anh', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000019', 'tranducanh@gmail.com', 3),
(33, 'Hưng', 'Phạm Gia', 'Phạm Gia Hưng', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000020', 'phamgiahung@gmail.com', 3),
(34, 'Ngọc', 'Võ Thị', 'Võ Thị Ngọc', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000021', 'vothingoc@gmail.com', 3),
(35, 'Yến', 'Đinh Hoàng', 'Đinh Hoàng Yến', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000022', 'dinhhoangyen@gmail.com', 3),
(36, 'Sơn', 'Mai Thế', 'Mai Thế Sơn', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000023', 'maitheson@gmail.com', 3),
(37, 'Thắng', 'Chu Việt', 'Chu Việt Thắng', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000024', 'chuvietthang@gmail.com', 3),
(38, 'Nhật', 'Đào Minh', 'Đào Minh Nhật', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000025', 'daominhnhat@gmail.com', 3),
(39, 'Linh', 'Trần Phương', 'Trần Phương Linh', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000026', 'tranphuonglinh@gmail.com', 3),
(40, 'Kiên', 'Nguyễn Trung', 'Nguyễn Trung Kiên', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000027', 'nguyentrungkien@gmail.com', 3),
(41, 'Thanh', 'Bùi Thị', 'Bùi Thị Thanh', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000028', 'buithithanh@gmail.com', 3),
(42, 'Trúc', 'Đoàn Thanh', 'Đoàn Thanh Trúc', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000029', 'doanthanhtruc@gmail.com', 3),
(43, 'Phong', 'Trịnh Tuấn', 'Trịnh Tuấn Phong', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000030', 'trinhtuanphong@gmail.com', 3),
(44, 'Hân', 'Lâm Gia', 'Lâm Gia Hân', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000031', 'lamgiahan@gmail.com', 3),
(45, 'Tâm', 'Hồ Minh', 'Hồ Minh Tâm', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000032', 'hominhtam@gmail.com', 3),
(46, 'Liên', 'Phan Cẩm', 'Phan Cẩm Liên', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000033', 'phancamlien@gmail.com', 3),
(47, 'Đạt', 'Vương Quốc', 'Vương Quốc Đạt', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000034', 'vuongquocdat@gmail.com', 3),
(48, 'Hà', 'Quách Thu', 'Quách Thu Hà', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000035', 'quachthuha@gmail.com', 3),
(49, 'Trâm', 'Nguyễn Bảo', 'Nguyễn Bảo Trâm', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000036', 'nguyenbaotram@gmail.com', 3),
(50, 'Khôi', 'Đỗ Minh', 'Đỗ Minh Khôi', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000037', 'dominhkhoi@gmail.com', 3),
(51, 'Cẩm', 'Trần Thị', 'Trần Thị Cẩm', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000038', 'tranthicam@gmail.com', 3),
(52, 'Đại', 'Đặng Quang', 'Đặng Quang Đại', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000039', 'dangquangdai@gmail.com', 3),
(53, 'Thịnh', 'Lê Phúc', 'Lê Phúc Thịnh', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000040', 'lephucthinh@gmail.com', 3),
(54, 'Michael', 'Johnson', 'Michael Johnson', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000041', 'michaeljohnson@gmail.com', 3),
(55, 'Sarah', 'Williams', 'Sarah Williams', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000042', 'sarahwilliams@gmail.com', 3),
(56, 'David', 'Brown', 'David Brown', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000043', 'davidbrown@gmail.com', 3),
(57, 'Emily', 'Davis', 'Emily Davis', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000044', 'emilydavis@gmail.com', 3),
(58, 'James', 'Wilson', 'James Wilson', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000045', 'jameswilson@gmail.com', 3),
(59, 'Jessica', 'Taylor', 'Jessica Taylor', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000046', 'jessicataylor@gmail.com', 3),
(60, 'Christopher', 'Anderson', 'Christopher Anderson', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000047', 'chrisanderson@gmail.com', 3),
(61, 'Ashley', 'Thomas', 'Ashley Thomas', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000048', 'ashleythomas@gmail.com', 3),
(62, 'Matthew', 'Martinez', 'Matthew Martinez', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000049', 'mattmartinez@gmail.com', 3),
(63, 'Olivia', 'White', 'Olivia White', '$2b$12$chaCVa.5aUSFfuhABKw.oelG6R49N4pgK5zLmLyrwS9iwXk3g/tD.', '0981000050', 'oliviawhite@gmail.com', 3);

--
-- Chỉ mục cho các bảng đã đổ
--

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
-- Chỉ mục cho bảng `customer_segment`
--
ALTER TABLE `customer_segment`
  ADD PRIMARY KEY (`UserID`);

--
-- Chỉ mục cho bảng `discount`
--
ALTER TABLE `discount`
  ADD PRIMARY KEY (`DiscountID`),
  ADD UNIQUE KEY `Code` (`Code`);

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
  ADD PRIMARY KEY (`id`);

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
-- AUTO_INCREMENT cho bảng `booking`
--
ALTER TABLE `booking`
  MODIFY `BookingID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=78;

--
-- AUTO_INCREMENT cho bảng `category`
--
ALTER TABLE `category`
  MODIFY `CategoryID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT cho bảng `comment`
--
ALTER TABLE `comment`
  MODIFY `CommentID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT cho bảng `discount`
--
ALTER TABLE `discount`
  MODIFY `DiscountID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT cho bảng `payment`
--
ALTER TABLE `payment`
  MODIFY `PaymentID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=70;

--
-- AUTO_INCREMENT cho bảng `photo`
--
ALTER TABLE `photo`
  MODIFY `PhotoID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=107;

--
-- AUTO_INCREMENT cho bảng `role`
--
ALTER TABLE `role`
  MODIFY `RoleID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT cho bảng `support_message`
--
ALTER TABLE `support_message`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=416;

--
-- AUTO_INCREMENT cho bảng `support_thread`
--
ALTER TABLE `support_thread`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT cho bảng `tour`
--
ALTER TABLE `tour`
  MODIFY `TourID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=45;

--
-- AUTO_INCREMENT cho bảng `user`
--
ALTER TABLE `user`
  MODIFY `UserID` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=64;

--
-- Ràng buộc đối với các bảng kết xuất
--

--
-- Ràng buộc cho bảng `booking`
--
ALTER TABLE `booking`
  ADD CONSTRAINT `booking_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`),
  ADD CONSTRAINT `booking_ibfk_2` FOREIGN KEY (`TourID`) REFERENCES `tour` (`TourID`),
  ADD CONSTRAINT `booking_ibfk_3` FOREIGN KEY (`DiscountID`) REFERENCES `discount` (`DiscountID`);

--
-- Ràng buộc cho bảng `comment`
--
ALTER TABLE `comment`
  ADD CONSTRAINT `comment_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `user` (`UserID`),
  ADD CONSTRAINT `comment_ibfk_2` FOREIGN KEY (`TourID`) REFERENCES `tour` (`TourID`);

--
-- Ràng buộc cho bảng `payment`
--
ALTER TABLE `payment`
  ADD CONSTRAINT `payment_ibfk_1` FOREIGN KEY (`BookingID`) REFERENCES `booking` (`BookingID`);

--
-- Ràng buộc cho bảng `photo`
--
ALTER TABLE `photo`
  ADD CONSTRAINT `photo_ibfk_1` FOREIGN KEY (`TourID`) REFERENCES `tour` (`TourID`);

--
-- Ràng buộc cho bảng `support_message`
--
ALTER TABLE `support_message`
  ADD CONSTRAINT `support_message_ibfk_1` FOREIGN KEY (`thread_id`) REFERENCES `support_thread` (`id`);

--
-- Ràng buộc cho bảng `tour`
--
ALTER TABLE `tour`
  ADD CONSTRAINT `tour_ibfk_1` FOREIGN KEY (`CategoryID`) REFERENCES `category` (`CategoryID`);

--
-- Ràng buộc cho bảng `user`
--
ALTER TABLE `user`
  ADD CONSTRAINT `user_ibfk_1` FOREIGN KEY (`RoleID`) REFERENCES `role` (`RoleID`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
