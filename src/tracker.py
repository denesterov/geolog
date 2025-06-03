import telegram

class DbAdapter:
    def __init__(self, session_data: dict):
        pass

    def get_session_data(self, session_id: str):
        pass


class SessionData:
    #__slots__ = ["session_data", "dirty"]
    def __init__(self, session_data: dict):
        self.__dict__['session_data'] = session_data
        self.__dict__['dirty'] = set()

    def __getattr__(self, item):
        sess_data = self.__dict__['session_data']
        if item in sess_data:
            return sess_data[item]
        raise AttributeError(f"SessionData object has no attribute '{item}'")

    def __setattr__(self, item, value):
        sess_data = self.__dict__['session_data']
        dirty = self.__dict__['dirty']
        sess_data[item] = value
        dirty.add(item)

    def get_dirty(self):
        return self.__dict__['dirty']


class Tracker:
    def __init__(self, session_data: dict):
        self.session_data = session_data

    def add_location(self, location: telegram.Location, new_location: bool = False):

        pass


class Tracker:
    def __init__(self, session_id: str):
        self.session_id = session_id

    def add_location(self, location: telegram.Location):
        pass
