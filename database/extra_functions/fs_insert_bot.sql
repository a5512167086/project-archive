CREATE OR REPLACE FUNCTION fs_insert_bot(
        _bot_name varchar(50),
        _channel_id varchar(100),
        _channel_access_token varchar(100),
        _channel_secret varchar(100),
        _liff_id varchar(100),
        _owner_id uuid
    ) RETURNS TABLE (
        bot_detail_id uuid,
        class_id int,
        object_id int,
        chinese_name varchar(50),
        channel_access_token varchar(100),
        liff_id varchar(100),
        owner_id uuid
    ) AS $$
DECLARE _main_bot_class_id int;

_new_class_id int;

_new_object_id int;

_new_bot_detail_id uuid;

_bot_entity_id int;

_setting_entity_id int;

_message_entity_id int;

_product_entity_id int;

_knowledge_entity_id int;

_order_entity_id int;

_reservation_entity_id int;

_service_entity_id int;

_admin_group_id int;

_manager_group_id int;

_user_group_id int;

_guest_group_id int;

BEGIN IF (
    _bot_name IS NULL
    OR _channel_id IS NULL
    OR _channel_access_token IS NULL
    OR _channel_secret IS NULL
    OR _owner_id IS NULL
) THEN RAISE EXCEPTION 'Error: 所有參數 (_bot_name, _channel_id, _channel_access_token, _channel_secret, _liff_id, _owner_id) 都必須提供';

END IF;

-- 取得各 entity_id
SELECT entity_id INTO _bot_entity_id
FROM entities e
WHERE e.chinese_name = '機器人'
LIMIT 1;

SELECT entity_id INTO _setting_entity_id
FROM entities e
WHERE e.chinese_name = '設定'
LIMIT 1;

SELECT entity_id INTO _message_entity_id
FROM entities e
WHERE e.chinese_name = '訊息紀錄'
LIMIT 1;

SELECT entity_id INTO _product_entity_id
FROM entities e
WHERE e.chinese_name = '產品'
LIMIT 1;

SELECT entity_id INTO _knowledge_entity_id
FROM entities e
WHERE e.chinese_name = '知識'
LIMIT 1;

SELECT entity_id INTO _order_entity_id
FROM entities e
WHERE e.chinese_name = '訂單'
LIMIT 1;

SELECT entity_id INTO _reservation_entity_id
FROM entities e
WHERE e.chinese_name = '預約'
LIMIT 1;

SELECT entity_id INTO _service_entity_id
FROM entities e
WHERE e.chinese_name = '服務'
LIMIT 1;

SELECT sc.class_id INTO _main_bot_class_id
FROM vs_sub_class sc
WHERE sc.parent_class_id = 1
    AND sc.entity_id = _bot_entity_id
LIMIT 1;

-- 插入主 class
SELECT fs_insert_class(
        _main_bot_class_id,
        _bot_entity_id,
        '',
        '用戶創建的機器人',
        _owner_id
    ) INTO _new_class_id;

-- 插入對應 object
INSERT INTO objects(chinese_name, owner_id)
VALUES (_bot_name, _owner_id)
RETURNING objects.object_id INTO _new_object_id;

-- 插入 bot 詳細資料
INSERT INTO bot_details(
        object_id,
        channel_id,
        channel_access_token,
        channel_secret,
        liff_id
    )
VALUES (
        _new_object_id,
        _channel_id,
        _channel_access_token,
        _channel_secret,
        _liff_id
    )
RETURNING bot_details.bot_detail_id INTO _new_bot_detail_id;

-- 綁定主 class 和 object
INSERT INTO class_object_relations(class_id, object_id)
VALUES (_new_class_id, _new_object_id);

INSERT INTO groups (group_name, group_description)
VALUES (
        'Administrators',
        'Bot Admin Group'
    )
RETURNING group_id INTO _admin_group_id;

-- 插入並取得 _manager_group_id
INSERT INTO groups (group_name, group_description)
VALUES (
        'Managers',
        'Bot Manager Group'
    )
RETURNING group_id INTO _manager_group_id;

-- 插入並取得 _user_group_id
INSERT INTO groups (group_name, group_description)
VALUES ('Users', 'Bot User Group')
RETURNING group_id INTO _user_group_id;

-- 插入並取得 _guest_group_id
INSERT INTO groups (group_name, group_description)
VALUES ('Guests', 'Bot Guest Group')
RETURNING group_id INTO _guest_group_id;

INSERT INTO permissions(class_id, role_type, role_id, permission_bits)
VALUES (_new_class_id, FALSE, _admin_group_id, 63),
    -- 全權
    (_new_class_id, FALSE, _manager_group_id, 15),
    -- 管理權限
    (_new_class_id, FALSE, _user_group_id, 3),
    -- 一般使用
    (_new_class_id, FALSE, _guest_group_id, 1);

-- 插入子 class
PERFORM fs_insert_class(
    _new_class_id,
    _setting_entity_id,
    '設定',
    '跟Module功能有關的設定',
    _owner_id
);

PERFORM fs_insert_class(
    _new_class_id,
    _message_entity_id,
    '訊息紀錄',
    '訊息紀錄',
    _owner_id
);

PERFORM fs_insert_class(
    _new_class_id,
    _product_entity_id,
    '產品',
    '電商功能的產品',
    _owner_id
);

PERFORM fs_insert_class(
    _new_class_id,
    _knowledge_entity_id,
    '知識',
    '問答功能的知識',
    _owner_id
);

PERFORM fs_insert_class(
    _new_class_id,
    _order_entity_id,
    '訂單',
    '電商功能的訂單',
    _owner_id
);

PERFORM fs_insert_class(
    _new_class_id,
    _reservation_entity_id,
    '預約',
    '預約功能的預約',
    _owner_id
);

PERFORM fs_insert_class(
    _new_class_id,
    _service_entity_id,
    '服務',
    '預約功能的服務',
    _owner_id
);

-- 將 class 名稱設為 object_id 字串
CALL sp_rename_class(_new_class_id, CAST(_new_object_id AS text));

RETURN QUERY
SELECT _new_bot_detail_id,
    _new_class_id,
    _new_object_id,
    _bot_name,
    _channel_access_token,
    _liff_id,
    _owner_id;

END;

$$ LANGUAGE plpgsql;