CREATE OR REPLACE VIEW vs_knowledge_file_list AS
SELECT co.class_id,
    o.object_id,
    kf.file_id,
    kf.filename,
    kf.display_name,
    kf.file_type,
    kf.created_at
FROM objects o
    JOIN knowledge_files kf ON kf.object_id = o.object_id
    JOIN class_object_relations co ON co.object_id = o.object_id
    JOIN classes c ON c.class_id = co.class_id
    JOIN entities e ON e.entity_id = c.entity_id
WHERE e.chinese_name = '知識';