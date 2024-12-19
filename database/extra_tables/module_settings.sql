CREATE TABLE IF NOT EXISTS module_settings(
    module_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id int NOT NULL,
    is_enabled boolean NOT NULL DEFAULT FALSE,
    version varchar(20) NOT NULL DEFAULT '1.0.0',
    description text,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_module_settings_object_id ON module_settings(object_id);

