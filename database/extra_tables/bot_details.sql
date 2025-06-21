CREATE TABLE IF NOT EXISTS bot_details(
    bot_detail_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_id int NOT NULL,
    channel_id varchar(256) NOT NULL,
    channel_access_token varchar(256) NOT NULL,
    channel_secret varchar(256) NOT NULL,
    login_channel_id varchar(256) NOT NULL,
    login_channel_secret varchar(256) NOT NULL,
    liff_id varchar(256) NOT NULL,
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bot_details_object_id ON bot_details(object_id);