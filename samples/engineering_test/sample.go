// Package canbus provides a CAN 2.0B message parser for automotive diagnostics.
// PEEKDOCS_TEST_MARKER
package canbus

import (
	"encoding/binary"
	"fmt"
	"time"
)

// Frame represents a single CAN bus frame.
type Frame struct {
	ID        uint32
	Extended  bool
	RTR       bool
	DLC       uint8
	Data      [8]byte
	Timestamp time.Time
}

// Signal extracts a signal value from the frame data using bit position and length.
func (f *Frame) Signal(startBit, bitLength int, signed bool) int64 {
	raw := binary.LittleEndian.Uint64(f.Data[:])
	mask := uint64((1 << bitLength) - 1)
	value := int64((raw >> startBit) & mask)
	if signed && (value>>(bitLength-1))&1 == 1 {
		value -= 1 << bitLength
	}
	return value
}

// String returns a human-readable representation of the frame.
func (f *Frame) String() string {
	return fmt.Sprintf("CAN [%03X] DLC=%d Data=%X", f.ID, f.DLC, f.Data[:f.DLC])
}
