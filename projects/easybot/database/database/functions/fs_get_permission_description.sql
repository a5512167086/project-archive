CREATE OR REPLACE FUNCTION fs_get_permission_description(_permission INT)
    RETURNS TABLE(
        permission INT,
        permission_bit TEXT,
        permission_description TEXT
    )
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        _permission AS permission,
        STRING_AGG(
            CASE WHEN permission_bits & _permission > 0 THEN
                '1'
            ELSE
                '0'
            END, '') AS permission_bit,
        STRING_AGG(
            CASE WHEN permission_bits & _permission > 0 THEN
                permission_description
            ELSE
                NULL
            END, '|') AS permission_description
    FROM(
    VALUES(64, '訂閱'),
(32, '管理'),
(16, '修改'),
(8, '刪除'),
(4, '新增'),
(2, '讀取'),
(1, '看')) AS permissions(permission_bits, permission_description);
END;
$$
LANGUAGE plpgsql;

