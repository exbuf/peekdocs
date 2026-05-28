// kalman.rs -- Simple 1D Kalman filter for sensor fusion
// PEEKDOCS_TEST_MARKER

#[derive(Debug, Clone)]
pub struct KalmanFilter {
    state: f64,
    uncertainty: f64,
    process_noise: f64,
    measurement_noise: f64,
}

impl KalmanFilter {
    pub fn new(initial_state: f64, initial_uncertainty: f64,
               process_noise: f64, measurement_noise: f64) -> Self {
        KalmanFilter {
            state: initial_state,
            uncertainty: initial_uncertainty,
            process_noise,
            measurement_noise,
        }
    }

    pub fn predict(&mut self, control_input: f64) {
        self.state += control_input;
        self.uncertainty += self.process_noise;
    }

    pub fn update(&mut self, measurement: f64) {
        let kalman_gain = self.uncertainty / (self.uncertainty + self.measurement_noise);
        self.state += kalman_gain * (measurement - self.state);
        self.uncertainty *= 1.0 - kalman_gain;
    }

    pub fn state(&self) -> f64 { self.state }
    pub fn uncertainty(&self) -> f64 { self.uncertainty }
}
