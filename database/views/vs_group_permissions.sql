CREATE OR REPLACE VIEW vs_group_permissions AS
SELECT p.class_id,
    p.group_id,
    g.group_name,
    g.group_description,
    g.status AS group_status,
    p.permission_bits
FROM permissions p
    JOIN groups g ON p.group_id = g.group_id
WHERE p.role_type = FALSE;