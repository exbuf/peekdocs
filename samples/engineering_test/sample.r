# sample.r -- Statistical analysis of sensor drift over time
# PEEKDOCS_TEST_MARKER

library(ggplot2)

# Simulate 1000 sensor readings with drift and noise
set.seed(42)
n_samples <- 1000
time_hours <- seq(0, 48, length.out = n_samples)
drift_rate <- 0.015  # mV per hour
noise_sd <- 0.25

baseline <- 2500  # mV nominal output
readings <- baseline + drift_rate * time_hours + rnorm(n_samples, sd = noise_sd)

sensor_data <- data.frame(
  time_h = time_hours,
  voltage_mv = readings
)

# Fit linear model to quantify drift
model <- lm(voltage_mv ~ time_h, data = sensor_data)
drift_estimate <- coef(model)["time_h"]
r_squared <- summary(model)$r.squared

cat(sprintf("Estimated drift: %.4f mV/hour (R^2 = %.4f)\n", drift_estimate, r_squared))

# Check if drift exceeds calibration threshold
threshold <- 0.02  # mV/hour
if (drift_estimate > threshold) {
  warning("Sensor drift exceeds calibration threshold!")
}
