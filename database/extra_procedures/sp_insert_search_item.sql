CREATE OR REPLACE PROCEDURE sp_insert_search_item(_bot_class_id int, _items jsonb)
LANGUAGE plpgsql
AS $$
DECLARE
    _search_class_id int;
    _item jsonb;
    _object_id int;
BEGIN
    SELECT
        child_class_id INTO _search_class_id
    FROM
        vs_sub_class
    WHERE
        class_id = _bot_class_id
        AND entity_id = 11
    LIMIT 1;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Error: 找不到 % 底下的 Search Class', _bot_class_id;
    END IF;
    FOR _item IN
    SELECT
        *
    FROM
        jsonb_array_elements(_items)
        LOOP
            INSERT INTO objects(chinese_name)
                VALUES (_item ->> 'item_name')
            RETURNING
                object_id INTO _object_id;
            INSERT INTO class_object_relations(class_id, object_id)
                VALUES (_search_class_id, _object_id);
            INSERT INTO search_texts(object_id, crawler_text)
                VALUES (_object_id, _item ->> 'crawler_text');
        END LOOP;
END;
$$;

