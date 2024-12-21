CREATE OR REPLACE PROCEDURE sp_insert_feature_command(_bot_class_id int, _command_name text, _command_keyword text, _type text)
LANGUAGE plpgsql
AS $$
DECLARE
    _command_class_id int;
    _object_id int;
BEGIN
    SELECT
        child_class_id INTO _command_class_id
    FROM
        vs_sub_class
    WHERE
        class_id = _bot_class_id
        AND entity_id = 4
    LIMIT 1;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Error: 找不到 % 底下的 Command Class', _bot_class_id;
    END IF;
    SELECT
        *
    FROM
        vs_command_list
    WHERE
        class_id = _command_class_id
        AND type = _type;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Error: Command Class 存在相同的 Feature %', _type;
    END IF;
    SELECT
        ms.object_id INTO _object_id
    FROM
        vs_module_settings ms
    WHERE
        ms.class_id = _command_class_id
        AND ms.chinese_name = _command_name
    LIMIT 1;
    INSERT INTO objects(chinese_name)
        VALUES (_command_name)
    RETURNING
        object_id INTO _object_id;
    INSERT INTO class_object_relations(class_id, object_id)
        VALUES (_command_class_id, _object_id);
    INSERT INTO command_details(object_id, command_keyword, type)
        VALUES (_object_id, _command_keyword, _type);
END;
$$;

