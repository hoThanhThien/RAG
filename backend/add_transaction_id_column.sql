-- Add TransactionID column to payment table for storing MoMo/PayPal transaction IDs
ALTER TABLE `payment` 
ADD COLUMN `TransactionID` varchar(100) DEFAULT NULL AFTER `OrderCode`,
ADD INDEX `idx_transaction_id` (`TransactionID`);
