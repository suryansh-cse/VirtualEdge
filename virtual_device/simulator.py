import sys
import os

# Allow Python to find modules from the project root
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from filter import MovingAverageFilter
from adc import ADC
from temperature import TemperatureSensor


def run_simulation(inject_spike=False):
    sensor = TemperatureSensor()
    adc = ADC()
    signal_filter = MovingAverageFilter(window_size=5)

    print("VirtualEdge ECE Sensor Simulation")
    print("-" * 75)

    for sample in range(20):
        temperature = sensor.read_temperature()
        voltage = sensor.temperature_to_voltage(temperature)

        raw_adc = adc.convert(voltage)

        # Inject an artificial ADC fault at sample 10
        if inject_spike and sample == 10:
            raw_adc = 2500
            fault_marker = " <-- SPIKE INJECTED"
        else:
            fault_marker = ""

        filtered_adc = signal_filter.update(raw_adc)

        print(
            f"Sample: {sample + 1:02d} | "
            f"Temperature: {temperature:6.2f} °C | "
            f"Voltage: {voltage:.4f} V | "
            f"Raw ADC: {raw_adc:4d} | "
            f"Filtered ADC: {filtered_adc:7.2f}"
            f"{fault_marker}"
        )


if __name__ == "__main__":
    run_simulation()