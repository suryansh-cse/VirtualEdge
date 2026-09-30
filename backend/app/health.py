def evaluate_device_health(
    temperature: float,
    voltage: float,
    current: float,
    battery: float
):
    warnings = []
    critical = []

    # Temperature
    if temperature >= 70:
        critical.append("HIGH_TEMPERATURE")
    elif temperature >= 50:
        warnings.append("ELEVATED_TEMPERATURE")

    # Voltage
    if voltage < 2.8:
        critical.append("LOW_VOLTAGE")
    elif voltage < 3.0:
        warnings.append("LOW_VOLTAGE")

    # Current
    if current >= 0.25:
        warnings.append("HIGH_CURRENT")

    # Battery
    if battery <= 15:
        critical.append("CRITICAL_BATTERY")
    elif battery <= 30:
        warnings.append("LOW_BATTERY")

    # Overall status
    if critical:
        status = "critical"
    elif warnings:
        status = "warning"
    else:
        status = "normal"

    return {
        "status": status,
        "warnings": warnings,
        "critical": critical
    }