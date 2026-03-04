CREATE TABLE IF NOT EXISTS objects(
    object_id SERIAL PRIMARY KEY,
    entity_id INT,
    chinese_name VARCHAR(2048),
    chinese_description VARCHAR(4000),
    english_name VARCHAR(2048),
    english_description VARCHAR(4000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    owner_id UUID,
    is_hided BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_objects_chinese_name ON objects(chinese_name);

CREATE INDEX IF NOT EXISTS ix_objects_entity_id ON objects(entity_id);

CREATE INDEX IF NOT EXISTS ix_objects_owner_id ON objects(owner_id);