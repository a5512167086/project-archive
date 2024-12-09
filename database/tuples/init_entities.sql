DO $$
BEGIN
    IF NOT EXISTS(
        SELECT
            1
        FROM
            entities
        WHERE
            chinese_name = '權限角色') THEN
    CALL sp_insert_entity('權限角色', 'Role', TRUE);
END IF;
END
$$;

