class ADC:
    def __init__(self, bits=12, reference_voltage=3.3):
        self.bits = bits
        self.reference_voltage = reference_voltage
        self.max_value = (2 ** bits) - 1

    def convert(self, voltage):
        if voltage < 0 or voltage > self.reference_voltage:
            raise ValueError(
                f"Voltage must be between 0 and {self.reference_voltage} V"
            )

        digital_value = (voltage / self.reference_voltage) * self.max_value

        return round(digital_value)


if __name__ == "__main__":
    adc = ADC()

    test_voltages = [0.0, 0.5, 1.65, 2.5, 3.3, -0.5, 3.5]

    for voltage in test_voltages:
        try:
            digital_value = adc.convert(voltage)

            print(
                f"Voltage: {voltage:.2f} V → "
                f"ADC: {digital_value}"
            )

        except ValueError as error:
            print(
                f"Voltage: {voltage:.2f} V → "
                f"ERROR: {error}"
            )