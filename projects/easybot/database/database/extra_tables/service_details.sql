CREATE TABLE IF NOT EXISTS service_details(
    service_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id int NOT NULL,
    duration_minutes INT NOT NULL,
    price INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_service_details_object_id ON service_details(object_id);