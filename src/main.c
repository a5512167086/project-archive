#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/display.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <bluetooth/services/nus.h>
#include <stdio.h>
#include <string.h>

LOG_MODULE_REGISTER(main);

#define DISPLAY_WIDTH 128
#define DISPLAY_HEIGHT 64
#define FRAMEBUFFER_SIZE (DISPLAY_WIDTH * DISPLAY_HEIGHT / 8)

static const struct device *display;
static const struct device *bme280;
static const struct device *bh1750;

static uint8_t framebuffer[FRAMEBUFFER_SIZE];

static struct display_buffer_descriptor buf_desc = {
    .buf_size = sizeof(framebuffer),
    .width = DISPLAY_WIDTH,
    .height = DISPLAY_HEIGHT,
    .pitch = DISPLAY_WIDTH,
};

static bool nus_ready = false;
static struct bt_conn *current_conn = NULL;

static const uint8_t font_5x7[][5] = {
    [0] = {0x3E, 0x51, 0x49, 0x45, 0x3E},
    [1] = {0x00, 0x42, 0x7F, 0x40, 0x00},
    [2] = {0x62, 0x51, 0x49, 0x49, 0x46},
    [3] = {0x22, 0x49, 0x49, 0x49, 0x36},
    [4] = {0x18, 0x14, 0x12, 0x7F, 0x10},
    [5] = {0x2F, 0x49, 0x49, 0x49, 0x31},
    [6] = {0x3E, 0x49, 0x49, 0x49, 0x32},
    [7] = {0x01, 0x71, 0x09, 0x05, 0x03},
    [8] = {0x36, 0x49, 0x49, 0x49, 0x36},
    [9] = {0x26, 0x49, 0x49, 0x49, 0x3E},
    ['.'] = {0x00, 0x60, 0x60, 0x00, 0x00},
    ['C'] = {0x3C, 0x42, 0x42, 0x42, 0x24},
    ['%'] = {0x62, 0x64, 0x08, 0x13, 0x23},
    ['T'] = {0x01, 0x01, 0x7F, 0x01, 0x01},
    ['H'] = {0x7F, 0x08, 0x08, 0x08, 0x7F},
    ['L'] = {0x7F, 0x40, 0x40, 0x40, 0x40},
    ['x'] = {0x41, 0x36, 0x08, 0x36, 0x41},
    [':'] = {0x00, 0x36, 0x36, 0x00, 0x00},
};

void set_pixel(int x, int y)
{
        if (x < 0 || x >= DISPLAY_WIDTH || y < 0 || y >= DISPLAY_HEIGHT)
                return;
        framebuffer[(y / 8) * DISPLAY_WIDTH + x] |= (1 << (y % 8));
}

void draw_char(char c, int x, int y, int scale)
{
        const uint8_t *glyph = NULL;
        if (c >= '0' && c <= '9')
                glyph = font_5x7[c - '0'];
        else if ((int)c >= 0 && (int)c < sizeof(font_5x7) / sizeof(font_5x7[0]))
                glyph = font_5x7[(int)c];
        if (!glyph)
                return;

        for (int col = 0; col < 5; col++)
        {
                for (int row = 0; row < 7; row++)
                {
                        if (glyph[col] & (1 << row))
                        {
                                for (int dx = 0; dx < scale; dx++)
                                {
                                        for (int dy = 0; dy < scale; dy++)
                                        {
                                                set_pixel(x + col * scale + dx, y + row * scale + dy);
                                        }
                                }
                        }
                }
        }
}

void draw_text_line(const char *text, int x, int y, int scale)
{
        while (*text && x < DISPLAY_WIDTH - 5 * scale)
        {
                draw_char(*text++, x, y, scale);
                x += 6 * scale;
        }
}

void read_and_display_sensor(void)
{
        struct sensor_value temp, humidity, illuminance;
        bool temp_ok = sensor_sample_fetch(bme280) == 0 &&
                       sensor_channel_get(bme280, SENSOR_CHAN_AMBIENT_TEMP, &temp) == 0 &&
                       sensor_channel_get(bme280, SENSOR_CHAN_HUMIDITY, &humidity) == 0;
        bool light_ok = sensor_sample_fetch(bh1750) == 0 &&
                        sensor_channel_get(bh1750, SENSOR_CHAN_LIGHT, &illuminance) == 0;

        memset(framebuffer, 0, sizeof(framebuffer));
        int y = 0;
        int scale = 1;
        int line_height = scale * 8 + 2;

        float t = 0.0, h = 0.0, lux = 0.0;
        char msg[64] = {0};

        if (temp_ok)
        {
                t = temp.val1 + temp.val2 / 1000000.0f;
                h = humidity.val1 + humidity.val2 / 1000000.0f;
                char t_line[20], h_line[20];
                snprintf(t_line, sizeof(t_line), "T:%.2fC", (double)t);
                snprintf(h_line, sizeof(h_line), "H:%.2f%%", (double)h);
                draw_text_line(t_line, 0, y, scale);
                y += line_height;
                draw_text_line(h_line, 0, y, scale);
                y += line_height;
        }

        if (light_ok)
        {
                lux = illuminance.val1 + illuminance.val2 / 1000000.0f;
                char l_line[20];
                snprintf(l_line, sizeof(l_line), "L:%.2flx", (double)lux);
                draw_text_line(l_line, 0, y, scale);
                y += line_height;
        }

        display_write(display, 0, 0, &buf_desc, framebuffer);

        if (nus_ready && current_conn)
        {
                snprintf(msg, sizeof(msg), "%.2f,%.2f,%.2f\n", t, h, lux);
                int err = bt_nus_send(current_conn, msg, strlen(msg));
                if (err)
                {
                        LOG_ERR("bt_nus_send failed: %d", err);
                }
                else
                {
                        LOG_INF("Sent NUS data");
                }
        }
}

void nus_sent_cb(struct bt_conn *conn)
{
        nus_ready = true;
        LOG_INF("NUS notifications enabled");
}

void nus_received_cb(struct bt_conn *conn, const uint8_t *data, uint16_t len)
{
        LOG_INF("Received: %.*s", len, data);
}

static struct bt_nus_cb nus_callbacks = {
    .received = nus_received_cb,
    .sent = nus_sent_cb,
};

static void connected(struct bt_conn *conn, uint8_t err)
{
        if (err)
        {
                LOG_ERR("Connection failed (err %u)", err);
                return;
        }
        current_conn = bt_conn_ref(conn);
        nus_ready = true;
        LOG_INF("Central connected");
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
        LOG_INF("Central disconnected (reason %u)", reason);
        if (current_conn)
        {
                bt_conn_unref(current_conn);
                current_conn = NULL;
                nus_ready = false;
        }
}

BT_CONN_CB_DEFINE(conn_callbacks) = {
    .connected = connected,
    .disconnected = disconnected,
};

void bt_ready(int err)
{
        if (err)
        {
                LOG_ERR("Bluetooth init failed (err %d)", err);
                return;
        }

        LOG_INF("Bluetooth initialized");

        err = bt_nus_init(&nus_callbacks);
        if (err)
        {
                LOG_ERR("NUS init failed (err %d)", err);
                return;
        }

        static const struct bt_le_adv_param adv_params =
            BT_LE_ADV_PARAM_INIT(BT_LE_ADV_OPT_CONNECTABLE,
                                 BT_GAP_ADV_FAST_INT_MIN_2,
                                 BT_GAP_ADV_FAST_INT_MAX_2,
                                 NULL);

        err = bt_le_adv_start(&adv_params, NULL, 0, NULL, 0);
        if (err)
        {
                LOG_ERR("Advertising failed to start (err %d)", err);
                return;
        }

        LOG_INF("Bluetooth advertising started");
}

void main(void)
{
        display = DEVICE_DT_GET_ANY(solomon_ssd1306fb);
        bme280 = DEVICE_DT_GET_ANY(bosch_bme280);
        bh1750 = DEVICE_DT_GET_ANY(rohm_bh1750);

        if (!device_is_ready(display))
        {
                LOG_ERR("Display not ready");
                return;
        }
        if (!device_is_ready(bme280))
        {
                LOG_ERR("BME280 not ready");
                return;
        }
        if (!device_is_ready(bh1750))
        {
                LOG_ERR("BH1750 not ready");
                return;
        }

        display_blanking_off(display);
        display_set_contrast(display, 0xFF);

        int err = bt_enable(bt_ready);
        if (err)
        {
                LOG_ERR("Bluetooth enable failed (err %d)", err);
                return;
        }

        while (1)
        {
                read_and_display_sensor();
                k_sleep(K_SECONDS(2));
        }
}
