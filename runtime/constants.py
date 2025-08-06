from queue import Queue

TIMEOUT: int = 5  # seconds
ENTRYPOINT_GROUP: str = "fabric_nodes.executors"
STATUS_Q: Queue[str] = Queue()

