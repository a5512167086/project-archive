CREATE TABLE IF NOT EXISTS service_option_groups (
    option_group_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT NOT NULL,
    group_name TEXT NOT NULL,
    group_description TEXT,
    selection_type TEXT NOT NULL CHECK (selection_type IN ('single', 'multiple')),
    is_required BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_service_option_groups_object_id ON service_option_groups(object_id);