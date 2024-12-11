CREATE OR REPLACE PROCEDURE sp_insert_search_items(_bot_class_id int, _search_items jsonb)
LANGUAGE plpgsql
AS $$
DECLARE
    _search_class_id int;
    _search_item jsonb;
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
    FOR _search_item IN
    SELECT
        *
    FROM
        jsonb_array_elements(_search_items)
        LOOP
            INSERT INTO objects(chinese_name, english_name)
                VALUES (_search_item ->> 'product_chinese_name', _search_item ->> 'product_english_name')
            RETURNING
                object_id INTO _object_id;
            INSERT INTO class_object_relations(class_id, object_id)
                VALUES (_search_class_id, _object_id);
            INSERT INTO search_texts(object_id, type, description, price, instruction, ingredient, url)
                VALUES (_object_id, _search_item ->> 'product_brand_name', _search_item ->> 'product_description', _search_item ->> 'product_lowest_price', _search_item ->> 'product_instruction', _search_item ->> 'product_ingredient', _search_item ->> 'product_link');
        END LOOP;
END;
$$;

