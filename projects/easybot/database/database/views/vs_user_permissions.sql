CREATE OR REPLACE VIEW vs_user_permissions AS
SELECT p.class_id,
    p.user_id,
    u.username,
    u.email,
    u.status AS user_status,
    p.permission_bits
FROM permissions p
    JOIN users u ON p.user_id = u.user_id
WHERE p.role_type = TRUE;