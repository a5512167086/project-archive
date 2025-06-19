DO $$
DECLARE _entity_id INT;

BEGIN BEGIN CALL sp_insert_entity('資源', 'Resource', TRUE);

EXCEPTION
WHEN OTHERS THEN RAISE NOTICE '忽略插入資源的錯誤: %',
SQLERRM;

END;

-- 取得 entity_id
SELECT entity_id INTO _entity_id
FROM entities
WHERE chinese_name = '資源'
LIMIT 1;

-- 插入根目錄 class（如果尚未存在）
INSERT INTO classes(
        entity_id,
        chinese_name,
        chinese_description,
        english_name,
        english_description,
        id_path,
        name_path,
        hierarchy_level
    )
SELECT _entity_id,
    '根目錄',
    '初始的根目錄，之後的所有Class都會掛在根目錄底下',
    'Root',
    'Initial root, all subsequent Classes will mount under the root',
    '1',
    '根目錄',
    1
WHERE NOT EXISTS (
        SELECT 1
        FROM classes
        WHERE entity_id = _entity_id
            AND chinese_name = '根目錄'
    );

SELECT entity_id INTO _entity_id
FROM entities
WHERE chinese_name = '機器人'
LIMIT 1;

IF NOT EXISTS (
    SELECT 1
    FROM classes
    WHERE chinese_name = '機器人'
        AND entity_id = _entity_id
) THEN PERFORM fs_insert_class(1, _entity_id, '機器人', '機器人Class', NULL);

END IF;

END $$;