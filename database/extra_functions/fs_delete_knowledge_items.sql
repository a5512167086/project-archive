CREATE OR REPLACE FUNCTION fs_delete_knowledge_items(
    _bot_class_id INT,
    _delete_object_ids INT[]
)
RETURNS TABLE(
    _object_id INT,
    _is_deleted BOOLEAN
)
LANGUAGE plpgsql
AS $$
DECLARE
    _knowledge_class_id INT;
    valid_ids INT[];
BEGIN
    SELECT child_class_id 
    INTO _knowledge_class_id
    FROM vs_sub_class
    WHERE class_id = _bot_class_id AND entity_id = 8
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Error: 找不到 % 底下的 Knowledge Class', _bot_class_id;
    END IF;

    SELECT ARRAY_AGG(object_id)
    INTO valid_ids
    FROM class_object_relations
    WHERE class_id = _knowledge_class_id AND object_id = ANY(_delete_object_ids);

    RETURN QUERY
    SELECT obj_id,
           obj_id = ANY(valid_ids) AS _is_deleted
    FROM unnest(_delete_object_ids) AS obj_id;

    IF valid_ids IS NOT NULL AND ARRAY_LENGTH(valid_ids, 1) > 0 THEN
        DELETE FROM class_object_relations
        WHERE class_id = _knowledge_class_id AND object_id = ANY(valid_ids);

        DELETE FROM objects
        WHERE object_id = ANY(valid_ids);
    END IF;
END;
$$;
