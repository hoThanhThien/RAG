-- Xóa UNIQUE constraint trên user_id để cho phép user tạo nhiều threads
-- Chạy script này trong MySQL Workbench hoặc phpMyAdmin

USE tourbookingdb;

-- Xóa constraint
ALTER TABLE support_thread DROP INDEX uniq_user;

-- Kiểm tra lại
SHOW CREATE TABLE support_thread;
