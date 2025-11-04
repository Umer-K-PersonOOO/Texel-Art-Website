# Simple shim so your hub can register/unregister the feature like other modules
from . import cgt_live_mirror

def register():
    cgt_live_mirror.register()

def unregister():
    cgt_live_mirror.unregister()
