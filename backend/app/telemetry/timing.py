from time import perf_counter


class Stopwatch:
    def __init__(self) -> None:
        self.started = perf_counter()

    def elapsed_ms(self) -> float:
        return round((perf_counter() - self.started) * 1000, 2)

