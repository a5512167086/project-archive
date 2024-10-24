CREATE OR REPLACE PROCEDURE sp_delete_class_by_mark(_class_id INT) LANGUAGE plpgsql AS $$ BEGIN BEGIN IF EXISTS(
        SELECT 1
        FROM classes
        WHERE class_id = _class_id
    ) THEN -- 更新 classes 表，将 b_del 设置为 true
UPDATE classes
SET is_deleted = TRUE,
    updated_at = NOW()
WHERE class_id = _class_id;
ELSE -- 如果 class 不存在，则抛出异常
RAISE EXCEPTION 'Error: 此 Class 不存在';
END IF;
EXCEPTION
WHEN OTHERS THEN -- 捕获错误，并返回错误信息
RAISE EXCEPTION '錯誤代碼：%, 錯誤訊息：%, 錯誤行號：%, 錯誤程序名稱：%',
SQLSTATE,
SQLERRM,
PG_EXCEPTION_CONTEXT,
COALESCE(CURRENT_QUERY(), '');
END;
END;
$$;