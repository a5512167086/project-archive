CREATE TABLE IF NOT EXISTS reservation_details (
    reservation_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT NOT NULL,
    reservation_item_schedule_id UUID NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'confirmed', 'cancelled', 'completed')
    ),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reservation_details_object_id ON reservation_details(object_id);