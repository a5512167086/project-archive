CREATE OR REPLACE FUNCTION fs_insert_object(_class_id INT, _entity_id INT, _chinese_name TEXT, _chinese_description TEXT, _owner_id UUID)
    RETURNS INT
    AS $$
DECLARE
    new_oid INT;
    error_message TEXT;
    error_context TEXT;
BEGIN
    -- Check if _class_id is provided
    IF _class_id IS NOT NULL THEN
        -- Check if the class exists
        IF NOT EXISTS (
            SELECT
                1
            FROM
                classes
            WHERE
                class_id = _class_id) THEN
        RAISE EXCEPTION 'Error: 此 Class 不存在';
    END IF;
    -- Insert new object and return the new object id
    INSERT INTO objects(
        entity_id,
        chinese_name,
        chinese_description,
        owner_id)
    VALUES (
        _entity_id,
        _chinese_name,
        _chinese_description,
        _owner_id)
RETURNING
    object_id INTO new_oid;
    -- Insert into the class-object relationship table
    INSERT INTO class_object_relations(
        class_id,
        object_id)
    VALUES (
        _class_id,
        new_oid);
ELSE
    -- If _class_id is NULL, insert the object without the class relationship
    INSERT INTO objects(
        entity_id,
        chinese_name,
        chinese_description,
        owner_id)
    VALUES (
        _entity_id,
        _chinese_name,
        _chinese_description,
        _owner_id)
RETURNING
    object_id INTO new_oid;
END IF;
    -- Return the newly created object ID
    RETURN new_oid;
EXCEPTION
    WHEN OTHERS THEN
        -- Capture error details and raise the error with additional context
        GET STACKED DIAGNOSTICS error_message = MESSAGE_TEXT,
        error_context = PG_EXCEPTION_CONTEXT;
    RAISE EXCEPTION '錯誤代碼：%, 錯誤訊息：%, 錯誤上下文：%', SQLSTATE, error_message, error_context;
END;

$$
LANGUAGE plpgsql;

