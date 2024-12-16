CREATE OR REPLACE VIEW vs_search_item_image_list AS
SELECT
    si.search_image_id,
    co.class_id,
    o.object_id,
    o.chinese_name,
    o.english_name,
    si.image_src,
    si.ocr_text,
    st.url
FROM
    objects o
    JOIN search_images si ON o.object_id = si.object_id
    JOIN search_texts st ON o.object_id = st.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id
WHERE
    si.ocr_text IS NOT NULL AND si.ocr_text != '';
