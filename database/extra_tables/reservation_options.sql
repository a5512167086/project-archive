-- 預約選項表 (記錄顧客在訂單中選擇的選項)
CREATE TABLE IF NOT EXISTS reservation_options (
    object_id INT NOT NULL,
    option_group_id UUID NOT NULL,
    option_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (object_id, option_group_id, option_id),
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reservation_options_object_id ON reservation_options(object_id);

CREATE INDEX IF NOT EXISTS idx_reservation_options_option_group_id ON reservation_options(option_group_id);

CREATE INDEX IF NOT EXISTS idx_reservation_options_option_id ON reservation_options(option_id);