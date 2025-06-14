DO $$ BEGIN -- users
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_users_class_id'
) THEN
ALTER TABLE users
ADD CONSTRAINT fk_users_class_id FOREIGN KEY(class_id) REFERENCES classes(class_id);

END IF;

COMMENT ON TABLE users IS '使用者資料表，包含帳號、密碼、email、角色等資訊';

-- classes
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_classes_owner_id'
) THEN
ALTER TABLE classes
ADD CONSTRAINT fk_classes_owner_id FOREIGN KEY(owner_id) REFERENCES users(user_id);

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_classes_entity_id'
) THEN
ALTER TABLE classes
ADD CONSTRAINT fk_classes_entity_id FOREIGN KEY(entity_id) REFERENCES entities(entity_id);

END IF;

COMMENT ON TABLE classes IS '類別定義表，記錄各個分類與擁有者的資訊';

-- inheritances
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_inheritances_child_class_id'
) THEN
ALTER TABLE inheritances
ADD CONSTRAINT fk_inheritances_child_class_id FOREIGN KEY(child_class_id) REFERENCES classes(class_id);

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_inheritances_parent_class_id'
) THEN
ALTER TABLE inheritances
ADD CONSTRAINT fk_inheritances_parent_class_id FOREIGN KEY(parent_class_id) REFERENCES classes(class_id);

END IF;

COMMENT ON TABLE inheritances IS '類別繼承關係表';

-- objects
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_objects_owner_id'
) THEN
ALTER TABLE objects
ADD CONSTRAINT fk_objects_owner_id FOREIGN KEY(owner_id) REFERENCES users(user_id);

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_objects_entity_id'
) THEN
ALTER TABLE objects
ADD CONSTRAINT fk_objects_entity_id FOREIGN KEY(entity_id) REFERENCES entities(entity_id);

END IF;

COMMENT ON TABLE objects IS '具體物件表，儲存可被預約或分類的實體';

-- object_relations
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_object_relations_first_object_id'
) THEN
ALTER TABLE object_relations
ADD CONSTRAINT fk_object_relations_first_object_id FOREIGN KEY(first_object_id) REFERENCES objects(object_id);

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_object_relations_second_object_id'
) THEN
ALTER TABLE object_relations
ADD CONSTRAINT fk_object_relations_second_object_id FOREIGN KEY(second_object_id) REFERENCES objects(object_id);

END IF;

COMMENT ON TABLE object_relations IS '物件之間的關聯性資料表';

-- class_object_relations
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_class_object_relations_class_id'
) THEN
ALTER TABLE class_object_relations
ADD CONSTRAINT fk_class_object_relations_class_id FOREIGN KEY(class_id) REFERENCES classes(class_id);

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_class_object_relations_object_id'
) THEN
ALTER TABLE class_object_relations
ADD CONSTRAINT fk_class_object_relations_object_id FOREIGN KEY(object_id) REFERENCES objects(object_id);

END IF;

COMMENT ON TABLE class_object_relations IS '類別與物件對應表';

-- oauths
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_oauths_user_id'
) THEN
ALTER TABLE oauths
ADD CONSTRAINT fk_oauths_user_id FOREIGN KEY(user_id) REFERENCES users(user_id);

END IF;

COMMENT ON TABLE oauths IS 'OAuth 第三方登入資訊';

-- customers
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_customers_user_id'
) THEN
ALTER TABLE customers
ADD CONSTRAINT fk_customers_user_id FOREIGN KEY(user_id) REFERENCES users(user_id);

END IF;

COMMENT ON TABLE customers IS '顧客使用者擴展資料表';

-- group_members
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_group_members_group_id'
) THEN
ALTER TABLE group_members
ADD CONSTRAINT fk_group_members_group_id FOREIGN KEY(group_id) REFERENCES groups(group_id);

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_group_members_member_id'
) THEN
ALTER TABLE group_members
ADD CONSTRAINT fk_group_members_member_id FOREIGN KEY(member_id) REFERENCES users(user_id);

END IF;

COMMENT ON TABLE group_members IS '群組成員關聯表';

-- groups
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_groups_class_id'
) THEN
ALTER TABLE groups
ADD CONSTRAINT fk_groups_class_id FOREIGN KEY(class_id) REFERENCES classes(class_id);

END IF;

COMMENT ON TABLE groups IS '使用者群組資訊';

-- permissions
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_permissions_class_id'
) THEN
ALTER TABLE permissions
ADD CONSTRAINT fk_permissions_class_id FOREIGN KEY(class_id) REFERENCES classes(class_id);

END IF;

COMMENT ON TABLE permissions IS '權限與類別的對應關係表';

-- reservation_item_details
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_reservation_item_details_object_id'
) THEN
ALTER TABLE reservation_item_details
ADD CONSTRAINT fk_reservation_item_details_object_id FOREIGN KEY(object_id) REFERENCES objects(object_id) ON DELETE CASCADE;

END IF;

COMMENT ON TABLE reservation_item_details IS '預約服務細節表';

-- reservation_item_schedules
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_reservation_item_schedules_object_id'
) THEN
ALTER TABLE reservation_item_schedules
ADD CONSTRAINT fk_reservation_item_schedules_object_id FOREIGN KEY(object_id) REFERENCES objects(object_id) ON DELETE CASCADE;

END IF;

COMMENT ON TABLE reservation_item_schedules IS '預約可用時段表';

-- reservation_item_options
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_reservation_item_options_object_id'
) THEN
ALTER TABLE reservation_item_options
ADD CONSTRAINT fk_reservation_item_options_object_id FOREIGN KEY(object_id) REFERENCES objects(object_id) ON DELETE CASCADE;

END IF;

COMMENT ON TABLE reservation_item_options IS '預約項目選項表';

-- reservation_options
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_reservation_options_object_id'
) THEN
ALTER TABLE reservation_options
ADD CONSTRAINT fk_reservation_options_object_id FOREIGN KEY(object_id) REFERENCES objects(object_id) ON DELETE CASCADE;

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_reservation_options_option_id'
) THEN
ALTER TABLE reservation_options
ADD CONSTRAINT fk_reservation_options_option_id FOREIGN KEY(option_id) REFERENCES reservation_item_options(option_id) ON DELETE CASCADE;

END IF;

COMMENT ON TABLE reservation_options IS '預約選項表';

-- reservation_details
IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_reservation_details_object_id'
) THEN
ALTER TABLE reservation_details
ADD CONSTRAINT fk_reservation_details_object_id FOREIGN KEY(object_id) REFERENCES objects(object_id) ON DELETE CASCADE;

END IF;

IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_reservation_details_schedule_id'
) THEN
ALTER TABLE reservation_details
ADD CONSTRAINT fk_reservation_details_schedule_id FOREIGN KEY(reservation_item_schedule_id) REFERENCES reservation_item_schedules(reservation_item_schedule_id) ON DELETE CASCADE;

END IF;

COMMENT ON TABLE reservation_details IS '預約詳細資訊表';

END $$ LANGUAGE plpgsql;