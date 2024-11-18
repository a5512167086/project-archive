DO $$
BEGIN
    -- Add fk_customers_user_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_customers_user_id') THEN
    ALTER TABLE customers
        ADD CONSTRAINT fk_customers_user_id FOREIGN KEY(user_id) REFERENCES users(user_id);
END IF;
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_group_members_group_id') THEN
    ALTER TABLE group_members
        ADD CONSTRAINT fk_group_members_group_id FOREIGN KEY(group_id) REFERENCES groups(group_id);
END IF;
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_group_members_member_id') THEN
    ALTER TABLE group_members
        ADD CONSTRAINT fk_group_members_member_id FOREIGN KEY(member_id) REFERENCES users(user_id);
END IF;
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_groups_class_id') THEN
    ALTER TABLE GROUPS
        ADD CONSTRAINT fk_groups_class_id FOREIGN KEY(class_id) REFERENCES classes(class_id);
END IF;
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_member_group_relationship_group_id') THEN
    ALTER TABLE member_groups
        ADD CONSTRAINT fk_member_group_relationship_group_id FOREIGN KEY(group_id) REFERENCES groups(group_id);
END IF;
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_member_group_relationship_member_id') THEN
    ALTER TABLE member_groups
        ADD CONSTRAINT fk_member_group_relationship_member_id FOREIGN KEY(member_id) REFERENCES users(user_id);
END IF;
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_permission_class_id') THEN
    ALTER TABLE permission
        ADD CONSTRAINT fk_permission_class_id FOREIGN KEY(class_id) REFERENCES classes(class_id);
END IF;
END
$$;

