CREATE OR REPLACE VIEW vs_knowledge_list AS
SELECT co.class_id,
     o.object_id,
     o.chinese_name AS question,
     o.english_name AS answer
FROM objects o
     JOIN class_object_relations co ON co.object_id = o.object_id
     JOIN classes c ON c.class_id = co.class_id
     JOIN entities e ON e.entity_id = c.entity_id
     LEFT JOIN knowledge_files kf ON o.object_id = kf.object_id
WHERE e.chinese_name = '知識'
     AND kf.object_id IS NULL;