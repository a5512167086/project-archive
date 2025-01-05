CREATE OR REPLACE PROCEDURE sp_insert_knowledge_items(_bot_class_id int, _knowledge_items jsonb)
LANGUAGE plpgsql
AS $$
DECLARE
    _knowledge_class_id int;
    _knowledge_item jsonb;
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
    FOR _knowledge_item IN
    SELECT
        *
    FROM
        jsonb_array_elements(_knowledge_items)
        LOOP
            INSERT INTO objects(chinese_name, english_name)
                VALUES (_knowledge_item ->> 'question', _knowledge_item ->> 'answer')
            RETURNING
                object_id INTO _object_id;
            INSERT INTO class_object_relations(class_id, object_id)
                VALUES (_knowledge_class_id, _object_id);
        END LOOP;
END;
$$;

