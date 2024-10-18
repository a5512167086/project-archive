CREATE OR REPLACE FUNCTION fs_get_id_path(parent_class_id INT, class_id INT) RETURNS VARCHAR(900) AS $$
DECLARE hierarchy_level INT;
id_path VARCHAR(900);
BEGIN -- 獲取父節點的 hierarchy_level
SELECT hierarchy_level INTO hierarchy_level
FROM classes
WHERE class_id = parent_class_id;
-- 判斷 hierarchy_level 是否為 0
IF hierarchy_level = 0 THEN id_path := CAST(class_id AS VARCHAR);
ELSE -- 構建 id_path，拼接父節點的 id_path 和當前節點的 class_id
SELECT COALESCE(id_path, '') || '/' || CAST(class_id AS VARCHAR) INTO id_path
FROM classes
WHERE class_id = parent_class_id;
END IF;
-- 返回 id_path
RETURN id_path;
END;
$$ LANGUAGE plpgsql;