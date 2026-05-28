' sample.vb -- Visual Basic module for process tank level monitoring
' PEEKDOCS_TEST_MARKER

Imports System.Math

Namespace ProcessControl

    Public Class TankLevelMonitor
        Private ReadOnly _tankDiameter As Double  ' meters
        Private ReadOnly _tankHeight As Double    ' meters
        Private _currentLevel As Double           ' meters

        Public Sub New(diameter As Double, height As Double)
            _tankDiameter = diameter
            _tankHeight = height
            _currentLevel = 0.0
        End Sub

        Public ReadOnly Property VolumeGallons As Double
            Get
                Dim radiusM As Double = _tankDiameter / 2.0
                Dim volumeM3 As Double = PI * radiusM * radiusM * _currentLevel
                Return volumeM3 * 264.172  ' cubic meters to US gallons
            End Get
        End Property

        Public ReadOnly Property PercentFull As Double
            Get
                Return (_currentLevel / _tankHeight) * 100.0
            End Get
        End Property

        Public Sub UpdateLevel(sensorReading As Double)
            If sensorReading < 0 OrElse sensorReading > _tankHeight Then
                Throw New ArgumentOutOfRangeException(NameOf(sensorReading))
            End If
            _currentLevel = sensorReading
        End Sub
    End Class

End Namespace
