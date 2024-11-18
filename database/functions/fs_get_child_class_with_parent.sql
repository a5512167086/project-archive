CREATE OR REPLACE FUNCTION fs_get_child_class_with_parent(_class_id INT)
    RETURNS TABLE(
        parent_class_id INT,
        parent_class_name TEXT,
        child_class_id INT,
        child_class_name TEXT,
        child_class_description TEXT,
        entity_name TEXT,
        entity_description TEXT,
        class_type INT,
        name_path TEXT,
        id_path TEXT,
        level INT,
        is_deleted BOOLEAN,
        is_hidden BOOLEAN,
        has_children BOOLEAN,
        object_count BOOLEAN,
        rank INT
    )
    AS $$
DECLARE
    parent_id INT := fn_get_class_parent_id(_class_id);
BEGIN
    IF parent_id IS NULL THEN
        RETURN QUERY
        SELECT
            NULL AS parent_class_id,
            NULL AS parent_class_name,
            child.class_id AS child_class_id,
            child.class_name AS child_class_name,
            child.class_description AS child_class_description,
            child.entity_name AS entity_name,
            child.entity_description AS entity_description,
            child.class_type AS class_type,
            child.name_path AS name_path,
            child.id_path AS id_path,
            child.level AS level,
            child.is_deleted AS is_deleted,
            child.is_hidden AS is_hidden,
            child.has_children AS has_children,
            child.object_count AS object_count,
            NULL AS rank
        FROM
            class AS child
        WHERE
            child.class_id = _class_id;
    ELSE
        RETURN QUERY
        SELECT
            parent.class_id AS parent_class_id,
            parent.class_name AS parent_class_name,
            child.class_id AS child_class_id,
            child.class_name AS child_class_name,
            child.class_description AS child_class_description,
            child.entity_name AS entity_name,
            child.entity_description AS entity_description,
            child.class_type AS class_type,
            child.name_path AS name_path,
            child.id_path AS id_path,
            child.level AS level,
            child.is_deleted AS is_deleted,
            child.is_hidden AS is_hidden,
            child.has_children AS has_children,
            child.object_count AS object_count,
            inheritance.rank AS rank
        FROM
            class AS parent
            JOIN inheritance ON parent.class_id = inheritance.parent_class_id
            JOIN class AS child ON inheritance.child_class_id = child.class_id
        WHERE
            parent.class_id = parent_id
            AND child.class_id = _class_id;
    END IF;
    RETURN QUERY WITH RECURSIVE tmp AS (
        -- 首先選取直接子類別
        SELECT
            parent.class_id AS parent_class_id,
            parent.class_name AS parent_class_name,
            child.class_id AS child_class_id,
            child.class_name AS child_class_name,
            child.class_description AS child_class_description,
            child.entity_name AS entity_name,
            child.entity_description AS entity_description,
            child.class_type AS class_type,
            child.name_path AS name_path,
            child.id_path AS id_path,
            child.level AS level,
            child.is_deleted AS is_deleted,
            child.is_hidden AS is_hidden,
            child.has_children AS has_children,
            child.object_count AS object_count,
            inheritance.rank AS rank
        FROM
            class AS parent
            JOIN inheritance ON parent.class_id = inheritance.parent_class_id
            JOIN class AS child ON inheritance.child_class_id = child.class_id
        WHERE
            parent.class_id = _class_id
        UNION ALL
        -- 遞迴選取子類別的子類別
        SELECT
            tmp.child_class_id AS parent_class_id,
            tmp.child_class_name AS parent_class_name,
            next_class.class_id AS child_class_id,
            next_class.class_name AS child_class_name,
            next_class.class_description AS child_class_description,
            next_class.entity_name AS entity_name,
            next_class.entity_description AS entity_description,
            next_class.class_type AS class_type,
            next_class.name_path AS name_path,
            next_class.id_path AS id_path,
            next_class.level AS level,
            next_class.is_deleted AS is_deleted,
            next_class.is_hidden AS is_hidden,
            next_class.has_children AS has_children,
            next_class.object_count AS object_count,
            inheritance.rank AS rank
        FROM
            tmp
            JOIN inheritance ON tmp.child_class_id = inheritance.parent_class_id
            JOIN class AS next_class ON inheritance.child_class_id = next_class.class_id
)
    SELECT
        *
    FROM
        tmp;
END;
$$
LANGUAGE plpgsql;

