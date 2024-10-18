CREATE TABLE IF NOT EXISTS users (
    user_id INT GENERATED ALWAYS AS IDENTITY,
    account VARCHAR(100) NOT NULL,
    password VARCHAR(300),
    is_valid BOOLEAN,
    email VARCHAR(100) NOT NULL,
    status SMALLINT,
    login_count INT DEFAULT 0 NOT NULL,
    last_login_datetime TIMESTAMP,
    login_error_count SMALLINT DEFAULT 0 NOT NULL,
    email_verify_code VARCHAR(300),
    class_id INT,
    gender BOOLEAN,
    birthday TIMESTAMP,
    address VARCHAR(200),
    phone_number VARCHAR(25),
    is_send_email BOOLEAN,
    PRIMARY KEY (user_id),
    CONSTRAINT uq_users_account UNIQUE (account),
    CONSTRAINT uq_users_email UNIQUE (EMail)
);
CREATE INDEX IF NOT EXISTS ix_users_account ON users (account);