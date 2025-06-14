CREATE TABLE IF NOT EXISTS reservation_item_details(
    reservation_item_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id int NOT NULL,
    duration_minutes INT NOT NULL,
    price INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reservation_item_details_object_id ON reservation_item_details(object_id);