CREATE OR REPLACE FUNCTION fs_rename_class(_class_id INT, _new_class_name TEXT)
    RETURNS VOID
    AS $$
DECLARE
    current_name_path TEXT;
    current_class_name TEXT;
    new_name_path TEXT;
BEGIN
    -- 獲取當前類別的 NamePath 和 CName
    SELECT
        name_path,
        class_name INTO current_name_path,
        current_class_name
    FROM
        class
    WHERE
        class_id = _class_id;
    IF current_name_path IS NULL THEN
        RAISE EXCEPTION 'Error: Class ID % not found', _class_id;
    END IF;
    -- 去掉尾端的原 class_name，並加上新的 class_name 作為根節點
    new_name_path := REVERSE(SUBSTRING(REVERSE(current_name_path), LENGTH(current_class_name) + 1)) || _new_class_name;
    -- 檢查新名稱是否會導致命名衝突
    IF EXISTS (
        SELECT
            1
        FROM
            class c
            JOIN inheritance i ON c.class_id = i.child_class_id
        WHERE
            i.parent_class_id =(
                SELECT
                    parent_class_id
                FROM
                    inheritance
                WHERE
                    child_class_id = _class_id)
                AND c.class_name = _new_class_name
                AND c.class_id != _class_id) THEN
        RAISE EXCEPTION 'Error: Class name % already exists at the same level', _new_class_name;
END IF;
    -- 更新當前類別的名稱和路徑
    UPDATE
        class
    SET
        class_name = _new_class_name,
        name_path = new_name_path
    WHERE
        class_id = _class_id;
    -- 使用遞迴 CTE 更新子類別的 NamePath
    WITH RECURSIVE tmp AS (
        -- 初始層級：選取直接子類別
        SELECT
            parent_class.class_id AS parent_class_id,
            _new_class_name AS parent_class_name,
            new_name_path AS parent_name_path,
            child_class.class_id AS child_class_id,
            child_class.class_name AS child_class_name,
            new_name_path || '/' || child_class.class_name AS name_path
        FROM
            class AS parent_class
            JOIN inheritance ON parent_class.class_id = inheritance.parent_class_id
            JOIN class AS child_class ON inheritance.child_class_id = child_class.class_id
        WHERE
            parent_class.class_id = _class_id
        UNION ALL
        -- 遞迴選取子類別，並更新它們的 NamePath
        SELECT
            tmp.child_class_id AS parent_class_id,
            tmp.child_class_name AS parent_class_name,
            tmp.name_path AS parent_name_path,
            next_class.class_id AS child_class_id,
            next_class.class_name AS child_class_name,
            tmp.name_path || '/' || next_class.class_name AS name_path
        FROM
            tmp
            JOIN inheritance ON tmp.child_class_id = inheritance.parent_class_id
            JOIN class AS next_class ON inheritance.child_class_id = next_class.class_id)
        -- 更新子類別的 NamePath
        UPDATE
            class
        SET
            name_path = tmp.name_path
        FROM
            tmp
        WHERE
            class.class_id = tmp.child_class_id;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '錯誤：%, 錯誤代碼：%, 錯誤訊息：%', SQLSTATE, SQLERRM, CURRENT_CONTEXT;
END;

$$
LANGUAGE plpgsql;

