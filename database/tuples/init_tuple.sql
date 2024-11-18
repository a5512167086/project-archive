DO $$
BEGIN
    -- 嘗試插入第一筆資料
    BEGIN
        CALL sp_insert_entity('資源', 'Resource', TRUE);
    EXCEPTION
        WHEN OTHERS THEN
            -- 可以選擇記錄錯誤，或僅略過錯誤
            RAISE NOTICE '忽略插入資源的錯誤: %', SQLERRM;
    END;
    -- 嘗試插入第二筆資料
    BEGIN
        CALL sp_insert_entity('使用者', 'User', TRUE);
    EXCEPTION
        WHEN OTHERS THEN
            -- 可以選擇記錄錯誤，或僅略過錯誤
            RAISE NOTICE '忽略插入使用者的錯誤: %', SQLERRM;
    END;
    -- 插入 classes 資料，檢查是否已存在
    INSERT INTO classes(
        entity_id,
        chinese_name,
        chinese_description,
        english_name,
        english_description,
        id_path,
        name_path,
        hierarchy_level)
    SELECT
        1,
        '根目錄',
        '初始的根目錄，之後的所有Class都會掛在根目錄底下',
        'Root',
        'Initial root, all subsequent Classes will mount under the root',
        '1',
        '根目錄',
        1
    WHERE
        NOT EXISTS(
            SELECT
                1
            FROM
                classes
            WHERE
                entity_id = 1
                AND chinese_name = '根目錄');
END
$$;

