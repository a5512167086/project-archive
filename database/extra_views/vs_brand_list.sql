CREATE OR REPLACE VIEW vs_brand_list AS
SELECT co.class_id,
    o.object_id,
    o.chinese_name AS brand_name,
    o.english_name AS brand_description
FROM objects o
    JOIN class_object_relations co ON co.object_id = o.object_id
    JOIN classes c ON c.class_id = co.class_id
WHERE c.entity_id = (
        SELECT entity_id
        FROM entities
        WHERE chinese_name = '品牌'
        LIMIT 1
    );