% sample.m -- MATLAB script: FFT analysis of vibration sensor data
% PEEKDOCS_TEST_MARKER

fs = 10000;          % Sampling frequency (Hz)
T  = 1/fs;           % Sampling period
N  = 4096;           % Number of samples
t  = (0:N-1) * T;    % Time vector

% Simulate vibration signal: bearing defect at 147 Hz + shaft speed 30 Hz
f_shaft = 30;
f_defect = 147;
signal = 2.0 * sin(2*pi*f_shaft*t) + 0.3 * sin(2*pi*f_defect*t);
signal = signal + 0.5 * randn(size(signal));  % Add noise

% Compute FFT
Y = fft(signal);
P2 = abs(Y/N);
P1 = P2(1:N/2+1);
P1(2:end-1) = 2*P1(2:end-1);
f = fs * (0:(N/2)) / N;

% Find dominant frequencies
[peaks, locs] = findpeaks(P1, 'MinPeakHeight', 0.15);
dominant_freqs = f(locs);

fprintf('Dominant frequencies detected:\n');
for k = 1:length(dominant_freqs)
    fprintf('  %.1f Hz  (amplitude: %.3f)\n', dominant_freqs(k), peaks(k));
end

% Plot
figure;
plot(f, P1);
xlabel('Frequency (Hz)');
ylabel('Amplitude');
title('Vibration Spectrum Analysis');
xlim([0 500]);
