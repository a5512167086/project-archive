CREATE TABLE IF NOT EXISTS reservation_item_options (
    option_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT NOT NULL,
    option_name TEXT NOT NULL,
    option_description TEXT,
    price INT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('text', 'select', 'number')),
    is_required BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reservation_item_options_object_id ON reservation_item_options(object_id);