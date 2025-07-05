CREATE OR REPLACE FUNCTION fs_move_class(
        target_class_id INT,
        new_parent_class_id INT
    ) RETURNS TABLE (
        parent_class_id INT,
        parent_class_name TEXT,
        parent_name_path TEXT,
        parent_id_path TEXT,
        parent_hierarchy_level INT,
        current_class_id INT,
        current_class_name TEXT,
        full_name_path TEXT,
        full_id_path TEXT,
        current_hierarchy_level INT
    ) LANGUAGE plpgsql AS $$
DECLARE base_name_path TEXT;

base_id_path TEXT;

base_class_name TEXT;

base_hierarchy_level INT;

BEGIN -- 取得新的父類別的資訊
SELECT name_path,
    id_path,
    chinese_name::TEXT,
    hierarchy_level INTO base_name_path,
    base_id_path,
    base_class_name,
    base_hierarchy_level
FROM classes
WHERE class_id = new_parent_class_id;

IF base_class_name IS NULL THEN RETURN;

END IF;

-- ✅ 更新並回傳的主流程
RETURN QUERY WITH RECURSIVE class_hierarchy AS (
    -- 第一層：指定要移動的 class
    SELECT new_parent_class_id AS parent_class_id,
        base_class_name::TEXT AS parent_class_name,
        base_name_path::TEXT AS parent_name_path,
        base_id_path::TEXT AS parent_id_path,
        base_hierarchy_level AS parent_hierarchy_level,
        c.class_id AS current_class_id,
        c.chinese_name::TEXT AS current_class_name,
        (base_name_path || '/' || c.chinese_name)::TEXT AS full_name_path,
        (base_id_path || '/' || c.class_id::TEXT)::TEXT AS full_id_path,
        base_hierarchy_level + 1 AS current_hierarchy_level
    FROM classes c
    WHERE c.class_id = target_class_id
    UNION ALL
    SELECT ch.current_class_id AS parent_class_id,
        ch.current_class_name::TEXT AS parent_class_name,
        ch.full_name_path::TEXT AS parent_name_path,
        ch.full_id_path::TEXT AS parent_id_path,
        ch.current_hierarchy_level AS parent_hierarchy_level,
        c2.class_id AS current_class_id,
        c2.chinese_name::TEXT AS current_class_name,
        (ch.full_name_path || '/' || c2.chinese_name)::TEXT AS full_name_path,
        (ch.full_id_path || '/' || c2.class_id::TEXT)::TEXT AS full_id_path,
        ch.current_hierarchy_level + 1 AS current_hierarchy_level
    FROM class_hierarchy ch
        JOIN inheritances i ON ch.current_class_id = i.parent_class_id
        JOIN classes c2 ON i.child_class_id = c2.class_id
),
updated_classes AS (
    -- ✅ 實際更新資料表
    UPDATE classes c
    SET name_path = ch.full_name_path,
        id_path = ch.full_id_path,
        hierarchy_level = ch.current_hierarchy_level
    FROM class_hierarchy ch
    WHERE c.class_id = ch.current_class_id
    RETURNING ch.parent_class_id,
        ch.parent_class_name,
        ch.parent_name_path,
        ch.parent_id_path,
        ch.parent_hierarchy_level,
        c.class_id AS current_class_id,
        c.chinese_name::TEXT AS current_class_name,
        ch.full_name_path,
        ch.full_id_path,
        ch.current_hierarchy_level
),
updated_inheritances AS (
    -- ✅ 更新 target_class_id 的父類別關係
    UPDATE inheritances i
    SET parent_class_id = new_parent_class_id
    WHERE i.child_class_id = target_class_id
    RETURNING i.child_class_id,
        i.parent_class_id
)
SELECT *
FROM updated_classes;

END;

$$;