CREATE TABLE IF NOT EXISTS entities(
    entity_id INT GENERATED ALWAYS AS IDENTITY,
    chinese_name VARCHAR(50) NOT NULL,
    english_name VARCHAR(50) NOT NULL,
    is_relational BOOLEAN DEFAULT TRUE NOT NULL,
    is_hidable BOOLEAN DEFAULT FALSE,
    is_deletable BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (entity_id)
);

CREATE INDEX IF NOT EXISTS idx_entities_chinese_name ON entities(chinese_name);

CREATE INDEX IF NOT EXISTS idx_entities_english_name ON entities(english_name);