CREATE TABLE IF NOT EXISTS customers(
    user_id UUID,
    full_name VARCHAR(255) NOT NULL,
    gender BOOLEAN NOT NULL,
    birthday DATE NOT NULL,
    address VARCHAR(255) NOT NULL,
    phone_number VARCHAR(255) NOT NULL
);

