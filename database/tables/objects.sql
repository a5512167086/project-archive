CREATE TABLE IF NOT EXISTS objects(
    object_id SERIAL,
    entity_id INT,
    chinese_name VARCHAR(512),
    chinese_description VARCHAR(4000),
    english_name VARCHAR(512),
    english_description VARCHAR(4000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    owner_id UUID,
    is_hided BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (object_id)
);

CREATE INDEX IF NOT EXISTS ix_objects_chinese_name ON objects(chinese_name);