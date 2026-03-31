-- Kiểm tra user nào là admin
SELECT UserID, Username, Email, FullName, RoleID FROM user;

-- Kiểm tra role
SELECT * FROM role;

-- Cập nhật user thành admin (thay UserID = 1 bằng ID user của bạn)
UPDATE user SET RoleID = (SELECT RoleID FROM role WHERE RoleName = 'admin' LIMIT 1) WHERE UserID = 1;
