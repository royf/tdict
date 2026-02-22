from collections.abc import MutableMapping

from .tmap import Tmap


class MMdict(dict, MutableMapping):
    pass


class Tdict(Tmap, MMdict):
    pass
