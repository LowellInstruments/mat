class DataFileRegistry:
    registry = {}

    @classmethod
    def register(cls, klass):
        cls.registry[klass.extension] = klass
