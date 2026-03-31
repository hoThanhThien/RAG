-- Create bank_txn table for tracking bank transactions
CREATE TABLE IF NOT EXISTS `bank_txn` (
  `BankTxnID` int(11) NOT NULL AUTO_INCREMENT,
  `Provider` varchar(50) NOT NULL,
  `ProviderRef` varchar(100) NOT NULL,
  `Amount` decimal(18,2) NOT NULL,
  `Description` varchar(255) DEFAULT NULL,
  `PaidAt` datetime NOT NULL,
  `RawPayload` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`RawPayload`)),
  `CreatedAt` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`BankTxnID`),
  UNIQUE KEY `ProviderRef` (`ProviderRef`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
