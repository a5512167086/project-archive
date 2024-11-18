CREATE OR REPLACE FUNCTION fs_get_parent_class_id(_class_id INT)
    RETURNS INT
    AS $$
DECLARE
    id_path TEXT;
    parent_class_id INT;
BEGIN
    -- 獲取指定 class_id 的 id_path
    SELECT
        id_path INTO id_path
    FROM
        class
    WHERE
        class_id = _class_id;
    -- 檢查 id_path 是否為空，如果為空則返回 NULL
    IF id_path IS NULL THEN
        RETURN NULL;
    END IF;
    -- 使用 regexp_split_to_array 來分割 id_path 並選取倒數第二個元素
    SELECT
        CAST((REGEXP_SPLIT_TO_ARRAY(id_path, '/'))[ARRAY_LENGTH(REGEXP_SPLIT_TO_ARRAY(id_path, '/'), 1) - 1] AS INT) INTO parent_class_id;
    -- 如果計算出的 parent_class_id 等於 _class_id，本身無父類別，返回 NULL
    IF parent_class_id = _class_id THEN
        RETURN NULL;
    END IF;
    RETURN parent_class_id;
END;
$$
LANGUAGE plpgsql;

