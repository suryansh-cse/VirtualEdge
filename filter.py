class MovingAverageFilter:
    def __init__(self, window_size=5):
        if window_size <= 0:
            raise ValueError("Window size must be greater than 0")

        self.window_size = window_size
        self.values = []

    def update(self, new_value):
        self.values.append(new_value)

        if len(self.values) > self.window_size:
            self.values.pop(0)

        return sum(self.values) / len(self.values)


if __name__ == "__main__":
    filter = MovingAverageFilter(window_size=5)

    test_values = [
        1320,
        1317,
        1324,
        1319,
        1328,
        1315,
        1322
    ]

    for value in test_values:
        filtered_value = filter.update(value)

        print(
            f"Raw: {value} | "
            f"Filtered: {filtered_value:.2f}"
        )