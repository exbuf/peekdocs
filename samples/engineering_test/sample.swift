// sample.swift -- BLE peripheral manager for sensor data broadcast
// PEEKDOCS_TEST_MARKER

import Foundation

struct SensorPacket {
    let sensorId: UInt8
    let temperature: Double
    let humidity: Double
    let batteryPct: UInt8
    let timestamp: Date

    func encode() -> Data {
        var data = Data(capacity: 16)
        data.append(sensorId)
        var temp = Float(temperature)
        data.append(Data(bytes: &temp, count: 4))
        var hum = Float(humidity)
        data.append(Data(bytes: &hum, count: 4))
        data.append(batteryPct)
        return data
    }
}

class SensorBeacon {
    private var advertisingInterval: TimeInterval = 1.0
    private var lastPacket: SensorPacket?

    func updateReading(temperature: Double, humidity: Double, battery: UInt8) {
        lastPacket = SensorPacket(
            sensorId: 0x01,
            temperature: temperature,
            humidity: humidity,
            batteryPct: battery,
            timestamp: Date()
        )
    }

    func packetData() -> Data? {
        return lastPacket?.encode()
    }
}
