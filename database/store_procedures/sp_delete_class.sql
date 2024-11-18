CREATE OR REPLACE PROCEDURE sp_delete_class(IN _class_id INT)
LANGUAGE plpgsql
AS $$
DECLARE
    error_message TEXT;
    error_context TEXT;
BEGIN
    -- Check if the class exists
    IF (
        SELECT
            COUNT(*)
        FROM
            classes
        WHERE
            class_id = _class_id) = 1 THEN
        -- Delete related records from class_object_relations and inheritances
        DELETE FROM class_object_relations
        WHERE class_id = _class_id;
        DELETE FROM inheritances
        WHERE child_class_id = _class_id
            OR parent_class_id = _class_id;
        DELETE FROM classes
        WHERE class_id = _class_id;
    ELSE
        -- Raise an error if the class does not exist
        RAISE EXCEPTION 'Error: This class does not exist';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        -- Capture error details and raise the error with additional context
        GET STACKED DIAGNOSTICS error_message = MESSAGE_TEXT,
        error_context = PG_EXCEPTION_CONTEXT;
    RAISE EXCEPTION 'Error code: %, Error message: %, Context: %', SQLSTATE, error_message, error_context;
END;

$$;

