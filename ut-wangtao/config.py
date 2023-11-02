import toml


class Config:
    __data = None

    def __init__(self):
        self.__data = toml.load('config.toml')

    def get(self, key, default_val=None):
        return self.__data.get(key, default_val)


config = Config()
