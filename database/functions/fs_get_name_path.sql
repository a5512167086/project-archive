CREATE OR REPLACE FUNCTION fs_get_name_path(parent_class_id INT, chinese_name VARCHAR(255)) RETURNS VARCHAR(900) AS $$
DECLARE hierarchy_level INT;
name_path VARCHAR(900);
BEGIN -- 查詢父節點的 hierarchy_level
SELECT hierarchy_level INTO hierarchy_level
FROM classes
WHERE class_id = parent_class_id;
-- 根據 hierarchy_level 判斷生成 name_path
IF hierarchy_level = 0 THEN name_path := chinese_name;
ELSE -- 拼接父節點的 name_path 和當前節點的 chinese_name
SELECT name_path || '/' || chinese_name INTO name_path
FROM classes
WHERE class_id = parent_class_id;
END IF;
-- 返回 name_path
RETURN name_path;
END;
$$ LANGUAGE plpgsql;