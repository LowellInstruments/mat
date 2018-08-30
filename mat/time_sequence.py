

class TimeSequence:
    def __init__(self, interval, frequency, burst_length, page_seconds):
        self.interval = interval
        self.n_samples = burst_length
        self.page_seconds = page_seconds
        self.period = 1 / frequency

    def next_sample(self):
        for interval_time in range(0, self.page_seconds, self.interval):
            for burst_time in range(0, self.n_samples):
                yield interval_time + burst_time * self.period
