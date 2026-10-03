class FaultDetector:
    def __init__(self, min_adc=1000, max_adc=1600):
        self.min_adc = min_adc
        self.max_adc = max_adc

    def check(self, adc_value):
        if adc_value < self.min_adc:
            return "FAULT"

        if adc_value > self.max_adc:
            return "FAULT"

        return "NORMAL"


if __name__ == "__main__":
    detector = FaultDetector()

    test_values = [1300, 1315, 1350, 2500, 800]

    for value in test_values:
        status = detector.check(value)
        print(f"ADC: {value} | Status: {status}")