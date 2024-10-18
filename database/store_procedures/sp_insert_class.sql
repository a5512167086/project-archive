CREATE OR REPLACE FUNCTION sp_insert_class(
        parent_class_id INT,
        -- 父節點 ID
        entity_id INT,
        -- 節點類型
        chinese_name VARCHAR(255),
        -- 節點名稱
        chinese_description VARCHAR(4000),
        -- 節點描述
        owner_id INT,
        -- 所有者ID
        OUT new_class_id INT -- 新節點ID，回傳
    ) RETURNS INT AS $$
DECLARE _parent_class_id INT;
_parent_name_path VARCHAR(900);
_new_name_path VARCHAR(900);
_new_class_id INT;
_new_hierarchy_level INT;
BEGIN -- 初始化返回值
new_class_id := NULL;
-- 查詢父節點的 class_id 和 name_path
SELECT class_id,
    name_path INTO _parent_class_id,
    _parent_name_path
FROM class
WHERE class_id = parent_class_id;
IF _parent_class_id IS NOT NULL THEN -- 獲取新節點的 name_path
_new_name_path := fs_get_name_path(parent_class_id, chinese_name);
-- 檢查 name_path 是否已存在
IF (
    SELECT COUNT(*)
    FROM class
    WHERE name_path = _new_name_path
) = 0 THEN -- 插入新節點到 class 表
INSERT INTO class (chinese_name, entity_id, chinese_description)
VALUES (chinese_name, entity_id, chinese_description)
RETURNING class_id INTO _new_class_id;
-- 插入繼承關係
INSERT INTO inheritance (parent_class_id, child_class_id)
VALUES (parent_class_id, _new_class_id);
-- 從父節點繼承權限
INSERT INTO permission (class_id, role_type, role_id, permission_bits)
SELECT _new_class_id,
    role_type,
    role_id,
    permission_bits
FROM permission
WHERE class_id = parent_class_id;
-- 計算新節點的層級
SELECT hierarchy_level + 1 INTO _new_hierarchy_level
FROM class
WHERE class_id = parent_class_id;
-- 更新新節點的屬性
UPDATE class
SET hierarchy_level = _new_hierarchy_level,
    name_path = _new_name_path,
    id_path = fs_get_id_path(parent_class_id, _new_class_id)
WHERE class_id = _new_class_id;
-- 設置返回的新節點ID
new_class_id := _new_class_id;
ELSE -- 節點已存在，拋出錯誤
RAISE EXCEPTION 'Error: 節點已存在，不得再新增';
END IF;
ELSE -- 父節點不存在，拋出錯誤
RAISE EXCEPTION 'Error: 沒有父節點 ID';
END IF;
EXCEPTION
WHEN OTHERS THEN -- 捕獲錯誤並返回錯誤訊息
RAISE EXCEPTION USING MESSAGE = '錯誤訊息：' || SQLERRM,
DETAIL = '錯誤行號：' || GETSTACKEDDIAGNOSTICS.LINE;
END;
$$ LANGUAGE plpgsql;