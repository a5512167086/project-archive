CREATE TABLE IF NOT EXISTS command_details(
    command_detail_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id int NOT NULL,
    command_keyword varchar(50) NOT NULL,
    type varchar(50) NOT NULL,
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_type_per_object ON command_details(object_id, type)
WHERE
    type IN ('FAQ', 'Ecomm', 'Search', 'Reservation');

