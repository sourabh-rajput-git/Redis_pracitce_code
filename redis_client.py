import redis
from rq import Queue
# Connect to Redis
# Update with your Redis server details
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0
)
q = Queue(connection=r)


