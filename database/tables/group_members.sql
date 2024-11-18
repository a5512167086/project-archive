CREATE TABLE IF NOT EXISTS group_members(
    group_id INT NOT NULL,
    member_id UUID NOT NULL,
    role SMALLINT DEFAULT 2 NOT NULL,
    type BOOLEAN,
    status BOOLEAN,
    CONSTRAINT pk_group_members PRIMARY KEY (group_id, member_id),
    CHECK (ROLE >= 0 AND ROLE <= 2)
);

-- 添加欄位描述
COMMENT ON COLUMN group_members.type IS '該關係的類型，null (直接加入)、0 (邀請) 、1 (申請)';

COMMENT ON COLUMN group_members.status IS '該關係的狀態，0為申請中、1為正常、null為過期使用者';

COMMENT ON COLUMN group_members.role IS '使用者在群組中的角色，目前有0是Owner，1是Manager，2是成員';

