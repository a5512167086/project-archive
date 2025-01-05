CREATE OR REPLACE PROCEDURE sp_insert_knowledge_item(_bot_class_id int, _question text, _answer text)
LANGUAGE plpgsql
AS $$
DECLARE
    _knowledge_class_id int;
    _object_id int;
BEGIN
    SELECT
        child_class_id INTO _knowledge_class_id
    FROM
        vs_sub_class
    WHERE
        class_id = _bot_class_id
        AND entity_id = 8
    LIMIT 1;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Error: 找不到 % 底下的 Knowledge Class', _bot_class_id;
    END IF;
    INSERT INTO objects(chinese_name, english_name)
        VALUES (_question, _answer)
    RETURNING
        object_id INTO _object_id;
    INSERT INTO class_object_relations(class_id, object_id)
        VALUES (_knowledge_class_id, _object_id);
END;
$$;

