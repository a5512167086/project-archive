CREATE TABLE IF NOT EXISTS permissions(
    class_id INT NOT NULL,
    role_type BOOLEAN NOT NULL,
    role_id INT NOT NULL,
    permission_bits SMALLINT DEFAULT 1 NOT NULL,
    CONSTRAINT uq_permissions UNIQUE (class_id, role_type, role_id)
);

-- 添加欄位描述
COMMENT ON COLUMN permissions.role_type IS '0表示是群組，1表示是使用者';

COMMENT ON COLUMN permissions.role_id IS '由RoleType決定值為Groups.GID或Member.MID';

