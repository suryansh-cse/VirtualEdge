import time
import uuid
import random
import requests

from temperature import TemperatureSensor
from adc import ADC


# =========================
# DEVICE CONFIGURATION
# =========================

DEVICE_ID = "VDEV-001"

BACKEND_URL = "http://127.0.0.1:8000/api/telemetry"

SIMULATION_INTERVAL = 5


# =========================
# HARDWARE SIMULATION
# =========================

temperature_sensor = TemperatureSensor(
    base_temperature=28.0,
    noise_level=0.3
)

adc = ADC(
    bits=12,
    reference_voltage=3.3
)


# =========================
# SIMULATED DEVICE VALUES
# =========================

def generate_current():
    """
    Simulates current consumption in amperes.
    """

    return round(random.uniform(0.05, 0.25), 3)


def generate_battery():
    """
    Simulates battery percentage.
    """

    return round(random.uniform(70.0, 100.0), 2)


# =========================
# GENERATE TELEMETRY
# =========================

def generate_telemetry():

    # Read simulated temperature sensor
    temperature = temperature_sensor.read_temperature()

    # Convert temperature to analog voltage
    voltage = temperature_sensor.temperature_to_voltage(
        temperature
    )

    # Convert analog voltage to digital ADC value
    adc_value = adc.convert(voltage)

    # Simulate other electrical values
    current = generate_current()
    battery = generate_battery()

    # Generate unique packet ID
    packet_id = str(uuid.uuid4())

    telemetry = {
        "device_id": DEVICE_ID,
        "temperature": temperature,
        "voltage": voltage,
        "current": current,
        "battery": battery,
        "packet_id": packet_id
    }

    return telemetry, adc_value


# =========================
# SEND DATA TO BACKEND
# =========================

def send_to_backend(telemetry):

    try:

        response = requests.post(
            BACKEND_URL,
            json=telemetry,
            timeout=5
        )

        return response

    except requests.RequestException as error:

        print(f"Backend connection error: {error}")

        return None


# =========================
# MAIN SIMULATION LOOP
# =========================

def main():

    print("=" * 60)
    print("VirtualEdge Device Simulator")
    print("=" * 60)

    print(f"Device ID : {DEVICE_ID}")
    print(f"Backend   : {BACKEND_URL}")
    print(f"Interval  : {SIMULATION_INTERVAL} seconds")
    print()

    print("Starting simulation...\n")

    while True:

        telemetry, adc_value = generate_telemetry()

        print("-" * 60)

        print("SENSOR DATA")

        print(
            f"Temperature : "
            f"{telemetry['temperature']:.2f} °C"
        )

        print(
            f"Voltage     : "
            f"{telemetry['voltage']:.4f} V"
        )

        print(
            f"ADC         : "
            f"{adc_value}"
        )

        print(
            f"Current     : "
            f"{telemetry['current']:.3f} A"
        )

        print(
            f"Battery     : "
            f"{telemetry['battery']:.2f} %"
        )

        print(
            f"Packet ID   : "
            f"{telemetry['packet_id']}"
        )

        print()

        # Send telemetry to FastAPI
        response = send_to_backend(telemetry)

        if response is not None:

            print(
                f"Backend     : "
                f"{response.status_code}"
            )

            try:
                print(
                    f"Response    : "
                    f"{response.json()}"
                )

            except ValueError:
                print(
                    f"Response    : "
                    f"{response.text}"
                )

        print()

        time.sleep(SIMULATION_INTERVAL)


# =========================
# START PROGRAM
# =========================

if __name__ == "__main__":
    main()