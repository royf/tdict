from collections.abc import MutableMapping

from .tmap import Tmap


class Tdict(Tmap, dict, MutableMapping):
    pass
