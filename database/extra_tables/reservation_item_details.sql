CREATE TABLE IF NOT EXISTS reservation_item_details(
    reservation_item_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id int NOT NULL,
    is_enabled boolean NOT NULL DEFAULT FALSE,
    version varchar(20) NOT NULL DEFAULT '1.0.0',
    description text,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reservation_item_details_object_id ON reservation_item_details(object_id);

