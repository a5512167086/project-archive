CREATE OR REPLACE PROCEDURE sp_insert_search_item(_bot_class_id int, _search_item jsonb)
LANGUAGE plpgsql
AS $$
DECLARE
    _search_class_id int;
    _object_id int;
BEGIN
    -- 獲取子類別 ID
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
    INSERT INTO objects(chinese_name, english_name)
        VALUES (_search_item ->> 'item_name', _search_item ->> 'item_english_name')
    RETURNING
        object_id INTO _object_id;
    INSERT INTO class_object_relations(class_id, object_id)
        VALUES (_search_class_id, _object_id);
    INSERT INTO search_texts(object_id, type, description, price, instruction, ingredient, url)
        VALUES (_object_id, _search_item ->> 'item_type', _search_item ->> 'item_description', _search_item ->> 'item_price', _search_item ->> 'item_instruction', _search_item ->> 'item_ingredient', _search_item ->> 'item_url');
END;
$$;

