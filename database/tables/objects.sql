CREATE TABLE IF NOT EXISTS objects (
    object_id INT GENERATED ALWAYS AS IDENTITY,
    entity_id INT,
    chinese_name VARCHAR(512),
    chinese_description VARCHAR(4000),
    english_name VARCHAR(512),
    english_description VARCHAR(4000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    extra_datetime TIMESTAMP,
    owner_id UUID,
    click_count INT DEFAULT 0 NOT NULL,
    outlink_count INT,
    inlink_count INT,
    is_hided BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (object_id)
);
CREATE INDEX IF NOT EXISTS ix_objects_chinese_name ON objects (chinese_name);