CREATE OR REPLACE FUNCTION fs_get_child_class(_class_id int)
    RETURNS TABLE(
        parent_class_id int,
        parent_chinese_name text,
        child_class_id int,
        child_chinese_name text,
        child_chinese_description text,
        entity_id int,
        name_path text,
        id_path text
    )
    AS $$
BEGIN
    RETURN QUERY WITH RECURSIVE tmp(
        parent_class_id,
        parent_chinese_name,
        child_class_id,
        child_chinese_name,
        child_chinese_description,
        entity_id,
        name_path,
        id_path
) AS(
        -- 初始查詢
        SELECT
            c1.class_id AS parent_class_id,
            c1.chinese_name::text AS parent_chinese_name,
            c2.class_id AS child_class_id,
            c2.chinese_name::text AS child_chinese_name,
            c2.chinese_description::text AS child_chinese_description,
            c2.entity_id AS entity_id,
            c2.name_path::text AS name_path,
            c2.id_path::text AS id_path
        FROM
            classes c1
            JOIN inheritances i ON c1.class_id = i.parent_class_id
            JOIN classes c2 ON i.child_class_id = c2.class_id
        WHERE
            c1.class_id = _class_id
        UNION ALL
        -- 遞歸部分
        SELECT
            t.child_class_id AS parent_class_id,
            t.child_chinese_name::text AS parent_chinese_name,
            c2.class_id AS child_class_id,
            c2.chinese_name::text AS child_chinese_name,
            c2.chinese_description::text AS child_chinese_description,
            c2.entity_id AS entity_id,
            c2.name_path::text AS name_path,
            c2.id_path::text AS id_path
        FROM
            tmp t
            JOIN inheritances i ON t.child_class_id = i.parent_class_id
            JOIN classes c2 ON i.child_class_id = c2.class_id
)
    SELECT
        tmp.*
    FROM
        tmp;
END;
$$
LANGUAGE plpgsql;

