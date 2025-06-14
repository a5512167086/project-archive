CREATE TABLE IF NOT EXISTS reservation_item_schedules (
    reservation_item_schedule_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT NOT NULL,
    schedule_type TEXT NOT NULL CHECK (schedule_type IN ('weekly', 'specific')),
    weekday SMALLINT CHECK (
        weekday BETWEEN 0 AND 6
    ),
    schedule_date DATE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    capacity INT NOT NULL DEFAULT 1,
    is_closed BOOLEAN DEFAULT FALSE,
    note TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    latest_reservation_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reservation_item_schedules_object_id ON reservation_item_schedules(object_id);