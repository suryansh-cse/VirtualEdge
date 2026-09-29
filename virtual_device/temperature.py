import random
from adc import ADC 

class TemperatureSensor:
    def __init__(
        self,
        base_temperature=28.0,
        noise_level=0.3,
        min_temperature=0.0,
        max_temperature=100.0
    ):
        self.base_temperature = base_temperature
        self.noise_level = noise_level
        self.min_temperature = min_temperature
        self.max_temperature = max_temperature

    def read_temperature(self):
        noise = random.gauss(0, self.noise_level)

        temperature = self.base_temperature + noise

        temperature = max(
            self.min_temperature,
            min(temperature, self.max_temperature)
        )

        return round(temperature, 2)

    def temperature_to_voltage(self, temperature):
        voltage = 0.5 + (temperature * 0.02)

        return round(voltage, 4)

if __name__ == "__main__":
    sensor = TemperatureSensor()
    adc = ADC()

    for _ in range(10):
        temperature = sensor.read_temperature()
        voltage = sensor.temperature_to_voltage(temperature)
        digital_value = adc.convert(voltage)

        print(
            f"Temperature: {temperature:.2f} °C | "
            f"Voltage: {voltage:.4f} V | "
            f"ADC: {digital_value}"
        )