/*
 * adc_driver.h -- ADC hardware abstraction layer
 * PEEKDOCS_TEST_MARKER
 */

#ifndef ADC_DRIVER_H
#define ADC_DRIVER_H

#include <stdint.h>

#define ADC_MAX_CHANNELS   16
#define ADC_RESOLUTION     12
#define ADC_VREF_MV        3300
#define ADC_MAX_COUNT      ((1 << ADC_RESOLUTION) - 1)

typedef enum {
    ADC_OK = 0,
    ADC_ERR_BUSY,
    ADC_ERR_TIMEOUT,
    ADC_ERR_INVALID_CHANNEL
} adc_status_t;

typedef struct {
    uint8_t  channel;
    uint16_t raw_count;
    float    voltage_mv;
} adc_sample_t;

adc_status_t adc_init(uint32_t clock_divider);
adc_status_t adc_read(uint8_t channel, adc_sample_t *sample);
adc_status_t adc_read_burst(uint8_t start_ch, uint8_t count, adc_sample_t *samples);
void         adc_shutdown(void);

#endif /* ADC_DRIVER_H */
