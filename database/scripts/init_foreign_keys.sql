DO $$
BEGIN
    -- Add fk_users_class_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_users_class_id') THEN
    ALTER TABLE users
        ADD CONSTRAINT fk_users_class_id FOREIGN KEY(class_id) REFERENCES classes(class_id);
END IF;
    -- Add fk_classes_owner_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_classes_owner_id') THEN
    ALTER TABLE classes
        ADD CONSTRAINT fk_classes_owner_id FOREIGN KEY(owner_id) REFERENCES users(user_id);
END IF;
    -- Add fk_classes_entity_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_classes_entity_id') THEN
    ALTER TABLE classes
        ADD CONSTRAINT fk_classes_entity_id FOREIGN KEY(entity_id) REFERENCES entities(entity_id);
END IF;
    -- Add fk_inheritances_child_class_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_inheritances_child_class_id') THEN
    ALTER TABLE inheritances
        ADD CONSTRAINT fk_inheritances_child_class_id FOREIGN KEY(child_class_id) REFERENCES classes(class_id);
END IF;
    -- Add fk_inheritances_parent_class_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_inheritances_parent_class_id') THEN
    ALTER TABLE inheritances
        ADD CONSTRAINT fk_inheritances_parent_class_id FOREIGN KEY(parent_class_id) REFERENCES classes(class_id);
END IF;
    -- Add fk_objects_owner_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_objects_owner_id') THEN
    ALTER TABLE objects
        ADD CONSTRAINT fk_objects_owner_id FOREIGN KEY(owner_id) REFERENCES users(user_id);
END IF;
    -- Add fk_objects_entity_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_objects_entity_id') THEN
    ALTER TABLE objects
        ADD CONSTRAINT fk_objects_entity_id FOREIGN KEY(entity_id) REFERENCES entities(entity_id);
END IF;
    -- Add fk_object_relations_first_object_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_object_relations_first_object_id') THEN
    ALTER TABLE object_relations
        ADD CONSTRAINT fk_object_relations_first_object_id FOREIGN KEY(first_object_id) REFERENCES objects(object_id);
END IF;
    -- Add fk_object_relations_second_object_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_object_relations_second_object_id') THEN
    ALTER TABLE object_relations
        ADD CONSTRAINT fk_object_relations_second_object_id FOREIGN KEY(second_object_id) REFERENCES objects(object_id);
END IF;
    -- Add fk_class_object_relations_class_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_class_object_relations_class_id') THEN
    ALTER TABLE class_object_relations
        ADD CONSTRAINT fk_class_object_relations_class_id FOREIGN KEY(class_id) REFERENCES classes(class_id);
END IF;
    -- Add fk_class_object_relations_object_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_class_object_relations_object_id') THEN
    ALTER TABLE class_object_relations
        ADD CONSTRAINT fk_class_object_relations_object_id FOREIGN KEY(object_id) REFERENCES objects(object_id);
END IF;
    -- Add fk_oauths_user_id if it doesn't exist
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_constraint
        WHERE
            conname = 'fk_oauths_user_id') THEN
    ALTER TABLE oauths
        ADD CONSTRAINT fk_oauths_user_id FOREIGN KEY(user_id) REFERENCES users(user_id);
END IF;
END
$$;

