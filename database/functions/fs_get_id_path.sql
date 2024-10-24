CREATE OR REPLACE FUNCTION fs_get_id_path(_parent_class_id INT, _class_id INT) RETURNS VARCHAR(900) AS $$
DECLARE hierarchy_level INT;
id_path VARCHAR(900);
BEGIN -- Check if _class_id is NULL
IF _class_id IS NULL THEN -- Return the id_path of the parent class directly
SELECT c.id_path INTO id_path
FROM classes c
WHERE c.class_id = _parent_class_id;
RETURN id_path;
END IF;
-- Retrieve the hierarchy level of the parent class
SELECT c.hierarchy_level INTO hierarchy_level
FROM classes c
WHERE c.class_id = _parent_class_id;
-- Check if the hierarchy_level is 0
IF hierarchy_level = 0 THEN -- If root level, the id_path is just the current class_id
id_path := CAST(_class_id AS VARCHAR);
ELSE -- Concatenate the parent's id_path and the current class_id
SELECT COALESCE(c.id_path, '') || '/' || CAST(_class_id AS VARCHAR) INTO id_path
FROM classes c
WHERE c.class_id = _parent_class_id;
END IF;
-- Return the constructed id_path
RETURN id_path;
END;
$$ LANGUAGE plpgsql;