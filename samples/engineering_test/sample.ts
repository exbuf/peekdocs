/**
 * telemetry.ts -- Typed telemetry data pipeline for IoT devices.
 * PEEKDOCS_TEST_MARKER
 */

interface SensorConfig {
    id: string;
    type: 'temperature' | 'pressure' | 'humidity' | 'flow';
    unit: string;
    minValue: number;
    maxValue: number;
}

interface TelemetryPacket {
    deviceId: string;
    timestamp: number;
    readings: Map<string, number>;
}

class TelemetryAggregator {
    private configs: Map<string, SensorConfig> = new Map();
    private buffer: TelemetryPacket[] = [];
    private readonly flushInterval: number;

    constructor(flushIntervalMs: number = 5000) {
        this.flushInterval = flushIntervalMs;
    }

    registerSensor(config: SensorConfig): void {
        this.configs.set(config.id, config);
    }

    ingest(packet: TelemetryPacket): boolean {
        for (const [sensorId, value] of packet.readings) {
            const cfg = this.configs.get(sensorId);
            if (cfg && (value < cfg.minValue || value > cfg.maxValue)) {
                console.warn(`Out-of-range reading on ${sensorId}: ${value} ${cfg.unit}`);
                return false;
            }
        }
        this.buffer.push(packet);
        return true;
    }

    flush(): TelemetryPacket[] {
        const batch = this.buffer.splice(0);
        return batch;
    }
}

export { TelemetryAggregator, SensorConfig, TelemetryPacket };
