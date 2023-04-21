import uuid
from flask import Flask
from jobs import q, update_job_status
from hotqueue import HotQueue
import redis
import os
import time

app = Flask(__name__)

redis_ip = os.environ.get('REDIS_IP')

if not redis_ip:
    raise Exception('REDIS_IP enviornment variable not sen\n')

q = HotQueue("queue", host=redis_ip, port=6379, db=1)
rd = redis.Redis(host=redis_ip, port=6379, db=0)


#FINISH THIS CODE for worker.py
@q.worker
def execute_job(job_id):
    """
    Retrieve a job id from the task queue and execute the job.
    Monitors the job to completion and updates the database accordingly.
    """
    update_job_status(job_id, 'in progress')
    time.sleep(15)
    update_job_status(job_id, "complete")

execute_job()
