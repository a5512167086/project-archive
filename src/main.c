#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/display.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>
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

// 5x7 字型（支援常見字元）
static const uint8_t font_5x7[][5] = {
    [0] = {0x3E, 0x51, 0x49, 0x45, 0x3E},   // 0
    [1] = {0x00, 0x42, 0x7F, 0x40, 0x00},   // 1
    [2] = {0x62, 0x51, 0x49, 0x49, 0x46},   // 2
    [3] = {0x22, 0x49, 0x49, 0x49, 0x36},   // 3
    [4] = {0x18, 0x14, 0x12, 0x7F, 0x10},   // 4
    [5] = {0x2F, 0x49, 0x49, 0x49, 0x31},   // 5
    [6] = {0x3E, 0x49, 0x49, 0x49, 0x32},   // 6
    [7] = {0x01, 0x71, 0x09, 0x05, 0x03},   // 7
    [8] = {0x36, 0x49, 0x49, 0x49, 0x36},   // 8
    [9] = {0x26, 0x49, 0x49, 0x49, 0x3E},   // 9
    ['.'] = {0x00, 0x60, 0x60, 0x00, 0x00}, // .
    ['C'] = {0x3C, 0x42, 0x42, 0x42, 0x24}, // C
    ['%'] = {0x62, 0x64, 0x08, 0x13, 0x23}, // %
    ['T'] = {0x01, 0x01, 0x7F, 0x01, 0x01}, // T
    ['H'] = {0x7F, 0x08, 0x08, 0x08, 0x7F}, // H
    ['L'] = {0x7F, 0x40, 0x40, 0x40, 0x40}, // L
    ['x'] = {0x41, 0x36, 0x08, 0x36, 0x41}, // x
    [':'] = {0x00, 0x36, 0x36, 0x00, 0x00}, // :
};

// 畫一個 pixel
void set_pixel(int x, int y)
{
        if (x < 0 || x >= DISPLAY_WIDTH || y < 0 || y >= DISPLAY_HEIGHT)
                return;
        framebuffer[(y / 8) * DISPLAY_WIDTH + x] |= (1 << (y % 8));
}

// 畫一個字元
void draw_char(char c, int x, int y, int scale)
{
        const uint8_t *glyph = NULL;
        if (c >= '0' && c <= '9')
        {
                glyph = font_5x7[c - '0'];
        }
        else if ((int)c >= 0 && (int)c < sizeof(font_5x7) / sizeof(font_5x7[0]))
        {
                glyph = font_5x7[(int)c];
        }

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

// 畫整行字串
void draw_text_line(const char *text, int x, int y, int scale)
{
        while (*text && x < DISPLAY_WIDTH - 5 * scale)
        {
                draw_char(*text++, x, y, scale);
                x += 6 * scale;
        }
}

// 顯示感測器資料
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

        if (temp_ok)
        {
                float t = temp.val1 + temp.val2 / 1000000.0f;
                float h = humidity.val1 + humidity.val2 / 1000000.0f;
                char t_line[20], h_line[20];
                snprintf(t_line, sizeof(t_line), "T:%.2fC", t);
                snprintf(h_line, sizeof(h_line), "H:%.2f%%", h);
                LOG_INF("Temp: %.2f C, Hum: %.2f %%", t, h);
                draw_text_line(t_line, 0, y, scale);
                y += line_height;
                draw_text_line(h_line, 0, y, scale);
                y += line_height;
        }

        if (light_ok)
        {
                float lux = illuminance.val1 + illuminance.val2 / 1000000.0f;
                char l_line[20];
                snprintf(l_line, sizeof(l_line), "L:%.2flx", lux);
                LOG_INF("Light: %.2f lx", lux);
                draw_text_line(l_line, 0, y, scale);
                y += line_height;
        }

        display_write(display, 0, 0, &buf_desc, framebuffer);
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

        while (1)
        {
                read_and_display_sensor();
                k_sleep(K_SECONDS(1));
        }
        return;
}
