import sys
import os
import time

# Allow imports from project root
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

from filter import MovingAverageFilter
from virtual_device.temperature import TemperatureSensor
from virtual_device.adc import ADC
from virtual_device.fault_detector import FaultDetector


# =========================
# CONFIGURATION
# =========================

TOTAL_SAMPLES = 20
SPIKE_SAMPLE = 10
SPIKE_VALUE = 2500

FILTER_WINDOW = 5
MIN_ADC = 1000
MAX_ADC = 1600


# =========================
# CREATE COMPONENTS
# =========================

sensor = TemperatureSensor(
    base_temperature=28.0,
    noise_level=0.3
)

adc = ADC(
    bits=12,
    reference_voltage=3.3
)

signal_filter = MovingAverageFilter(
    window_size=FILTER_WINDOW
)

fault_detector = FaultDetector(
    min_adc=MIN_ADC,
    max_adc=MAX_ADC
)


# =========================
# MAIN SIMULATION
# =========================

def main():

    print("=" * 70)
    print("VirtualEdge - Day 3 Fault Detection Test")
    print("=" * 70)

    print(f"Samples       : {TOTAL_SAMPLES}")
    print(f"Spike sample  : {SPIKE_SAMPLE}")
    print(f"Spike ADC     : {SPIKE_VALUE}")
    print(f"Filter window : {FILTER_WINDOW}")
    print(f"Normal range  : {MIN_ADC} - {MAX_ADC}")
    print()

    for sample in range(1, TOTAL_SAMPLES + 1):

        # -------------------------
        # Temperature sensor
        # -------------------------

        temperature = sensor.read_temperature()

        # -------------------------
        # Temperature -> Voltage
        # -------------------------

        voltage = sensor.temperature_to_voltage(
            temperature
        )

        # -------------------------
        # Voltage -> ADC
        # -------------------------

        raw_adc = adc.convert(voltage)

        # -------------------------
        # Inject test fault
        # -------------------------

        spike = False

        if sample == SPIKE_SAMPLE:
            raw_adc = SPIKE_VALUE
            spike = True

        # -------------------------
        # Moving average filter
        # -------------------------

        filtered_adc = signal_filter.update(
            raw_adc
        )

        # -------------------------
        # Fault detection
        # -------------------------

        fault_status = fault_detector.check(
            raw_adc
        )

        # -------------------------
        # Display
        # -------------------------

        print("-" * 70)

        if spike:
            print("⚠️  TEST ADC SPIKE INJECTED")

        print(
            f"Sample       : {sample:02d}"
        )

        print(
            f"Temperature  : {temperature:.2f} °C"
        )

        print(
            f"Voltage      : {voltage:.4f} V"
        )

        print(
            f"Raw ADC      : {raw_adc}"
        )

        print(
            f"Filtered ADC : {filtered_adc:.2f}"
        )

        print(
            f"Fault Status : {fault_status}"
        )

        time.sleep(1)

    # -------------------------
    # Finished
    # -------------------------

    print("-" * 70)
    print("Day 3 fault detection test completed.")
    print("=" * 70)


# =========================
# START PROGRAM
# =========================

if __name__ == "__main__":
    main()