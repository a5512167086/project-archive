CREATE TABLE IF NOT EXISTS permissions (
    class_id INT NOT NULL,
    role_type BOOLEAN NOT NULL,
    group_id INT,
    user_id UUID,
    permission_bits SMALLINT DEFAULT 1 NOT NULL,
    UNIQUE (class_id, role_type, group_id),
    UNIQUE (class_id, role_type, user_id),
    CHECK (
        (
            role_type = FALSE
            AND group_id IS NOT NULL
            AND user_id IS NULL
        )
        OR (
            role_type = TRUE
            AND user_id IS NOT NULL
            AND group_id IS NULL
        )
    )
);

-- 欄位說明
COMMENT ON COLUMN permissions.role_type IS 'FALSE 表示群組，TRUE 表示使用者';

COMMENT ON COLUMN permissions.group_id IS '當 role_type = FALSE 時對應 groups.group_id';

COMMENT ON COLUMN permissions.user_id IS '當 role_type = TRUE 時對應 users.user_id';