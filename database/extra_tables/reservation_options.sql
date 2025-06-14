CREATE TABLE IF NOT EXISTS reservation_options (
    option_id UUID NOT NULL,
    object_id INT NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (object_id, option_id)
);

CREATE INDEX IF NOT EXISTS idx_reservation_options_object_id ON reservation_options(object_id);