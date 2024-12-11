CREATE OR REPLACE VIEW vs_search_item_text_list AS
SELECT
    st.search_text_id,
    co.class_id,
    o.object_id,
    o.chinese_name,
    o.english_name,
    st.type,
    st.description,
    st.price,
    st.instruction,
    st.ingredient,
    st.url
FROM
    objects o
    JOIN search_texts st ON o.object_id = st.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id
