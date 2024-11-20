CREATE TABLE IF NOT EXISTS bot_details(
    channel_id VARCHAR(256) NOT NULL,
    channel_access_token VARCHAR(256) NOT NULL,
    channel_secret VARCHAR(256) NOT NULL
)
INHERITS (
    objects
);

