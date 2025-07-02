CREATE TABLE IF NOT EXISTS service_schedules (
    service_schedule_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id INT NOT NULL,
    schedule_type TEXT NOT NULL CHECK (schedule_type IN ('weekly', 'specific')),
    weekday SMALLINT CHECK (
        weekday BETWEEN 0 AND 6
    ),
    schedule_date DATE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    capacity INT NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_service_schedules_object_id ON service_schedules(object_id);