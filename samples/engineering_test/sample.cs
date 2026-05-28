// sample.cs -- SCADA data point class with alarm thresholds
// PEEKDOCS_TEST_MARKER

using System;

namespace IndustrialControl.SCADA
{
    public enum AlarmLevel { Normal, Warning, Alarm, Critical }

    public class DataPoint
    {
        public string TagName { get; }
        public double Value { get; private set; }
        public DateTime Timestamp { get; private set; }
        public double LowAlarm { get; set; }
        public double HighAlarm { get; set; }
        public double LowWarning { get; set; }
        public double HighWarning { get; set; }

        public DataPoint(string tagName, double lowAlarm, double highAlarm)
        {
            TagName = tagName;
            LowAlarm = lowAlarm;
            HighAlarm = highAlarm;
            LowWarning = lowAlarm + (highAlarm - lowAlarm) * 0.1;
            HighWarning = highAlarm - (highAlarm - lowAlarm) * 0.1;
        }

        public AlarmLevel Update(double newValue)
        {
            Value = newValue;
            Timestamp = DateTime.UtcNow;

            if (newValue <= LowAlarm || newValue >= HighAlarm) return AlarmLevel.Critical;
            if (newValue <= LowWarning || newValue >= HighWarning) return AlarmLevel.Warning;
            return AlarmLevel.Normal;
        }
    }
}
