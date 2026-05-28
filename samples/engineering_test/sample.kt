// sample.kt -- Data class model for equipment maintenance records
// PEEKDOCS_TEST_MARKER

package com.plant.maintenance

import java.time.LocalDateTime

enum class Priority { LOW, MEDIUM, HIGH, CRITICAL }

data class MaintenanceRecord(
    val equipmentId: String,
    val description: String,
    val priority: Priority,
    val scheduledDate: LocalDateTime,
    val completedDate: LocalDateTime? = null,
    val technicianId: String? = null
) {
    val isOverdue: Boolean
        get() = completedDate == null && scheduledDate.isBefore(LocalDateTime.now())

    val status: String
        get() = when {
            completedDate != null -> "COMPLETED"
            isOverdue -> "OVERDUE"
            else -> "SCHEDULED"
        }
}

class MaintenanceScheduler {
    private val records = mutableListOf<MaintenanceRecord>()

    fun schedule(record: MaintenanceRecord) { records.add(record) }

    fun overdueItems(): List<MaintenanceRecord> =
        records.filter { it.isOverdue }.sortedBy { it.priority }

    fun completeWork(equipmentId: String, techId: String): Boolean {
        val idx = records.indexOfFirst { it.equipmentId == equipmentId && it.completedDate == null }
        if (idx < 0) return false
        records[idx] = records[idx].copy(completedDate = LocalDateTime.now(), technicianId = techId)
        return true
    }
}
