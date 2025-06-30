CREATE TABLE IF NOT EXISTS reservation_item_options (
    option_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    option_group_id UUID NOT NULL,
    option_name TEXT NOT NULL,
    option_description TEXT,
    price INT NOT NULL DEFAULT 0,
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (option_group_id) REFERENCES reservation_option_groups(option_group_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reservation_item_options_option_group_id ON reservation_item_options(option_group_id);