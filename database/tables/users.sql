CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users(
    user_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username VARCHAR(100),
    password VARCHAR(300),
    is_valid BOOLEAN DEFAULT FALSE,
    email VARCHAR(100) NOT NULL,
    status SMALLINT,
    login_count INT DEFAULT 0 NOT NULL,
    last_login_datetime TIMESTAMP,
    login_error_count SMALLINT DEFAULT 0 NOT NULL,
    email_verify_code VARCHAR(300),
    class_id INT,
    is_send_email BOOLEAN DEFAULT FALSE,
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

