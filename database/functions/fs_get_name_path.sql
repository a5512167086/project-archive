CREATE OR REPLACE FUNCTION fs_get_name_path(
        _parent_class_id INT,
        _chinese_name VARCHAR(255)
    ) RETURNS VARCHAR(900) AS $$
DECLARE hierarchy_level INT;
name_path VARCHAR(900);
BEGIN -- Check if _chinese_name is NULL
IF _chinese_name IS NULL THEN -- Return the name_path of the parent class directly
SELECT c.name_path INTO name_path
FROM classes c
WHERE c.class_id = _parent_class_id;
RETURN name_path;
END IF;
-- Retrieve the hierarchy level of the parent class
SELECT c.hierarchy_level INTO hierarchy_level
FROM classes c
WHERE c.class_id = _parent_class_id;
-- Determine name_path based on the hierarchy_level
IF hierarchy_level = 0 THEN -- Root level uses the chinese_name directly
name_path := _chinese_name;
ELSE -- Concatenate the parent's name_path and current node's chinese_name
SELECT c.name_path || '/' || _chinese_name INTO name_path
FROM classes c
WHERE c.class_id = _parent_class_id;
END IF;
-- Return the computed name_path
RETURN name_path;
END;
$$ LANGUAGE plpgsql;