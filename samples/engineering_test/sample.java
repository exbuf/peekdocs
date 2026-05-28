/**
 * CircularBuffer.java -- Thread-safe circular buffer for sensor data logging.
 * PEEKDOCS_TEST_MARKER
 */
package com.engineering.datalog;

import java.util.concurrent.locks.ReentrantLock;

public class CircularBuffer<T> {
    private final Object[] buffer;
    private int head;
    private int tail;
    private int count;
    private final ReentrantLock lock = new ReentrantLock();

    public CircularBuffer(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("Capacity must be positive");
        this.buffer = new Object[capacity];
    }

    public void put(T item) {
        lock.lock();
        try {
            buffer[head] = item;
            head = (head + 1) % buffer.length;
            if (count < buffer.length) count++;
            else tail = (tail + 1) % buffer.length;
        } finally {
            lock.unlock();
        }
    }

    @SuppressWarnings("unchecked")
    public T get(int index) {
        lock.lock();
        try {
            if (index < 0 || index >= count) throw new IndexOutOfBoundsException();
            return (T) buffer[(tail + index) % buffer.length];
        } finally {
            lock.unlock();
        }
    }

    public int size() { return count; }
}
