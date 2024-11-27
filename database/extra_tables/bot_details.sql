CREATE TABLE IF NOT EXISTS bot_details(
    object_id int NOT NULL PRIMARY KEY,
    channel_id varchar(256) NOT NULL,
    channel_access_token varchar(256) NOT NULL,
    channel_secret varchar(256) NOT NULL,
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE
);

