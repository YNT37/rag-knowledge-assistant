from threading import RLock

OP_LOCK = RLock()
index_dirty = True


def invalidate_rag_index() -> None:
    global index_dirty
    with OP_LOCK:
        index_dirty = True
