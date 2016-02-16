import pykka

from mopidy import backend


class CacherBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config, audio):
        super(CacherBackend, self).__init__()
		
