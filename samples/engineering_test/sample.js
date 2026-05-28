/**
 * serial_port.js -- Node.js module for RS-485 device communication.
 * PEEKDOCS_TEST_MARKER
 */

'use strict';

const EventEmitter = require('events');

class ModbusClient extends EventEmitter {
    constructor(portPath, baudRate = 9600) {
        super();
        this.portPath = portPath;
        this.baudRate = baudRate;
        this.slaveId = 1;
        this._buffer = Buffer.alloc(0);
    }

    async readHoldingRegisters(startAddr, count) {
        const request = this._buildFrame(0x03, startAddr, count);
        const response = await this._sendAndReceive(request);
        return this._parseRegisters(response, count);
    }

    _buildFrame(functionCode, addr, value) {
        const frame = Buffer.alloc(8);
        frame.writeUInt8(this.slaveId, 0);
        frame.writeUInt8(functionCode, 1);
        frame.writeUInt16BE(addr, 2);
        frame.writeUInt16BE(value, 4);
        const crc = this._calculateCRC(frame.slice(0, 6));
        frame.writeUInt16LE(crc, 6);
        return frame;
    }

    _calculateCRC(buffer) {
        let crc = 0xFFFF;
        for (const byte of buffer) {
            crc ^= byte;
            for (let i = 0; i < 8; i++) {
                crc = (crc & 1) ? (crc >> 1) ^ 0xA001 : crc >> 1;
            }
        }
        return crc;
    }
}

module.exports = { ModbusClient };
