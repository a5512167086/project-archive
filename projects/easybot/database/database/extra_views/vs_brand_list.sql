CREATE OR REPLACE VIEW public.vs_brand_list AS
SELECT co.class_id,
    o.object_id,
    o.chinese_name AS brand_name,
    o.english_name AS brand_description
FROM objects o
    JOIN class_object_relations co ON co.object_id = o.object_id
    JOIN classes c ON c.class_id = co.class_id
    JOIN entities e ON e.entity_id = c.entity_id
WHERE e.chinese_name = '品牌';