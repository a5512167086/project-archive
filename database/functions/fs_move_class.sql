CREATE OR REPLACE FUNCTION fs_move_class(_class_id INT, _parent_class_id INT)
    RETURNS TABLE(
        parent_class_id INT,
        parent_class_name TEXT,
        parent_name_path TEXT,
        child_class_id INT,
        child_class_name TEXT,
        name_path TEXT,
        id_path TEXT,
        level INT
    )
    AS $$
DECLARE
    original_parent_id INT := get_class_parent_id(_class_id);
    message TEXT;
    class_name TEXT;
    current_id_path TEXT;
    parent_id_path TEXT;
BEGIN
    -- 獲取 class 和 parent 的相關資料
    SELECT
        class_name,
        id_path INTO class_name,
        current_id_path
    FROM
        class
    WHERE
        class_id = _class_id;
    SELECT
        id_path INTO parent_id_path
    FROM
        class
    WHERE
        class_id = _parent_class_id;
    -- 檢查是否符合各種條件
    IF NOT EXISTS (
        SELECT
            1
        FROM
            class
        WHERE
            class_id = _parent_class_id) THEN
    message := 'Error: parent_class_id 不存在，無法移動 Class';
ELSIF _class_id = _parent_class_id THEN
    message := 'Error: 無法移動到自己，class_id 與 parent_class_id 相同';
ELSIF EXISTS (
        SELECT
            1
        FROM
            subclass_view
        WHERE
            class_id = _parent_class_id
            AND class_name = class_name) THEN
    message := 'Error: 名稱重複，無法移動';
ELSIF parent_id_path LIKE current_id_path || '%' THEN
    message := 'Error: 無法移動到自身的子 class';
END IF;
    -- 如果有錯誤訊息，則拋出異常
    IF message IS NOT NULL THEN
        RAISE EXCEPTION '%', message;
    END IF;
    -- 更新繼承關係
    IF original_parent_id IS NULL THEN
        INSERT INTO inheritance(
            parent_class_id,
            child_class_id)
        VALUES (
            _parent_class_id,
            _class_id);
    ELSE
        UPDATE
            inheritance
        SET
            parent_class_id = _parent_class_id
        WHERE
            parent_class_id = original_parent_id
            AND child_class_id = _class_id;
    END IF;
    -- 執行更新並返回結果
    RETURN QUERY WITH RECURSIVE tmp AS (
        -- 初始層級
        SELECT
            _parent_class_id AS parent_class_id,
            class_name AS parent_class_name,
            parent_id_path AS parent_name_path,
            _class_id AS child_class_id,
            class_name AS child_class_name,
            parent_id_path || '/' || class_name AS name_path,
            parent_id_path || '/' || _class_id::TEXT AS id_path,
            1 AS level
        FROM
            class
        WHERE
            class_id = _class_id
        UNION ALL
        -- 遞迴選取子類別
        SELECT
            tmp.child_class_id AS parent_class_id,
            tmp.child_class_name AS parent_class_name,
            tmp.name_path AS parent_name_path,
            next_class.class_id AS child_class_id,
            next_class.class_name AS child_class_name,
            tmp.name_path || '/' || next_class.class_name AS name_path,
            tmp.id_path || '/' || next_class.class_id::TEXT AS id_path,
            tmp.level + 1 AS level
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

