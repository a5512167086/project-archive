CREATE TABLE IF NOT EXISTS member_groups(
    member_id UUID NOT NULL,
    group_id INT NOT NULL,
    role SMALLINT DEFAULT 2,
    type BOOLEAN DEFAULT NULL,
    status BOOLEAN DEFAULT TRUE,
    CONSTRAINT pk_member_group_relationship PRIMARY KEY (member_id, group_id)
);

-- 添加欄位描述
COMMENT ON COLUMN member_groups.status IS '該關係的狀態，0為申請中、1為正常、null為過期使用者';

COMMENT ON COLUMN member_groups.type IS '該關係的類型，null (直接加入)、0 (邀請) 、1 (申請)';

COMMENT ON COLUMN member_groups.role IS '使用者在群組中的角色，目前有0是Owner，1是Manager，2是成員';

