CREATE OR REPLACE FUNCTION fs_insert_class(
        _parent_class_id INT,
        _entity_id INT,
        _chinese_name VARCHAR(256),
        _chinese_description VARCHAR(4000),
        _owner_id UUID
    ) RETURNS INT AS $$
DECLARE new_class_id INT;

parent_class_id_local INT;

parent_name_path VARCHAR(450);

new_name_path VARCHAR(450);

new_level SMALLINT;

new_id_path VARCHAR(900);

error_message TEXT;

error_context TEXT;

BEGIN -- Initialize the output value
new_class_id := NULL;

-- Fetch parent class details
SELECT class_id,
    name_path INTO parent_class_id_local,
    parent_name_path
FROM classes
WHERE class_id = _parent_class_id;

IF parent_class_id_local IS NOT NULL THEN -- Generate new name path
new_name_path := fs_get_name_path(_parent_class_id, _chinese_name);

-- Check if the class already exists
IF (
    SELECT COUNT(*)
    FROM classes
    WHERE name_path = new_name_path
) = 0 THEN -- Insert into classes and get the new class_id
INSERT INTO classes(
        entity_id,
        chinese_name,
        chinese_description,
        owner_id
    )
VALUES (
        _entity_id,
        _chinese_name,
        _chinese_description,
        _owner_id
    )
RETURNING class_id INTO new_class_id;

-- Insert into inheritance or relevant hierarchy table
INSERT INTO inheritances(
        parent_class_id,
        child_class_id
    )
VALUES (
        parent_class_id_local,
        new_class_id
    );

-- Calculate new level and update the classes record
new_level :=(
    SELECT hierarchy_level + 1
    FROM classes
    WHERE class_id = _parent_class_id
);

new_id_path := fs_get_id_path(_parent_class_id, new_class_id);

INSERT INTO permissions (
        class_id,
        role_type,
        group_id,
        user_id,
        permission_bits
    )
SELECT new_class_id,
    role_type,
    CASE
        WHEN role_type = FALSE THEN group_id
        ELSE NULL
    END,
    CASE
        WHEN role_type = TRUE THEN user_id
        ELSE NULL
    END,
    permission_bits
FROM permissions
WHERE class_id = _parent_class_id;

UPDATE classes
SET hierarchy_level = new_level,
    name_path = new_name_path,
    id_path = new_id_path
WHERE class_id = new_class_id;

ELSE -- Raise an error if the class already exists
RAISE EXCEPTION 'Error: Class already exists, cannot insert.';

END IF;

ELSE -- Raise an error if no parent class ID is provided
RAISE EXCEPTION 'Error: Parent class ID not found.';

END IF;

-- Return the newly created class ID
RETURN new_class_id;

EXCEPTION
WHEN OTHERS THEN -- Capture error details and raise the error with additional context
GET STACKED DIAGNOSTICS error_message = MESSAGE_TEXT,
error_context = PG_EXCEPTION_CONTEXT;

RAISE EXCEPTION 'Error code: %, Error message: %, Context: %',
SQLSTATE,
error_message,
error_context;

END;

$$ LANGUAGE plpgsql;