CREATE TABLE IF NOT EXISTS reservation_details (
    reservation_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT NOT NULL,
    reservation_item_id UUID NOT NULL,
    reservation_item_schedule_id UUID NOT NULL,
    reservation_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    price INT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'confirmed', 'cancelled', 'completed')
    ),
    payment_method TEXT CHECK (
        payment_method IN ('cash', 'bank_transfer')
    ),
    payment_status TEXT CHECK (
        payment_status IN ('unpaid', 'paid', 'refunded')
    ),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reservation_details_object_id ON reservation_details(object_id);

CREATE INDEX IF NOT EXISTS idx_reservation_details_reservation_item_id ON reservation_details(reservation_item_id);

CREATE INDEX IF NOT EXISTS idx_reservation_details_reservation_item_schedule_id ON reservation_details(reservation_item_schedule_id);

CREATE INDEX IF NOT EXISTS idx_reservation_details_reservation_date ON reservation_details(reservation_date);