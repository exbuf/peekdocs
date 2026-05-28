#!/usr/bin/env python3
"""Sensor data acquisition module for industrial monitoring.

This module provides classes for reading and calibrating
thermocouple inputs on data acquisition hardware.
PEEKDOCS_TEST_MARKER
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ThermocoupleReading:
    """A single calibrated thermocouple measurement."""
    channel: int
    raw_mv: float
    temp_celsius: float
    timestamp: float = field(default_factory=time.time)


class DAQController:
    """Controls a multi-channel thermocouple data acquisition unit."""

    COLD_JUNCTION_OFFSET = 0.05  # mV per degree C

    def __init__(self, device_path: str, num_channels: int = 8):
        self.device_path = device_path
        self.num_channels = num_channels
        self._calibration: List[float] = [1.0] * num_channels

    def read_channel(self, channel: int) -> Optional[ThermocoupleReading]:
        """Read a single thermocouple channel and return calibrated value."""
        if channel < 0 or channel >= self.num_channels:
            raise ValueError(f"Channel {channel} out of range [0, {self.num_channels})")
        raw_mv = self._sample_adc(channel)
        temp = (raw_mv - self.COLD_JUNCTION_OFFSET) * self._calibration[channel] * 24.4
        return ThermocoupleReading(channel=channel, raw_mv=raw_mv, temp_celsius=temp)

    def _sample_adc(self, channel: int) -> float:
        """Read raw millivolt value from ADC (stub for hardware driver)."""
        return 0.0
