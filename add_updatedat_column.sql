-- Add UpdatedAt column to booking table
ALTER TABLE `booking` 
ADD COLUMN `UpdatedAt` TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP 
AFTER `OrderCode`;

-- Update existing records
UPDATE `booking` SET `UpdatedAt` = NOW() WHERE `UpdatedAt` IS NULL;
