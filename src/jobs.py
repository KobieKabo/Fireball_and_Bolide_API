import uuid
from hotqueue import HotQueue
from flask import jsonify
import redis
from uuid import uuid4
import os

redis_ip = os.environ.get('REDIS_IP')
if not redis_ip:
    raise Exception('REDIS_IP enviornment variable not sen\n')
q = HotQueue("queue", host=redis_ip, port=6379, db=1)
rd = redis.Redis(host=redis_ip, port=6379, db=0)

#q = HotQueue("queue", host='172.17.0.1', port=6379, db=1)
#rd = redis.Redis(host='172.17.0.1', port=6379, db=0)

def generate_job_id():
    """
    Creates a random job id.
    """
    return str(uuid.uuid4())

def generate_job_id_key(job_id):
    """
    Generates redis key from job ID. Used for retrieving or updating a job in in the redis db.
    """
    job_id_key = 'job.{}'.format(job_id)
    return job_id_key

def instantiate_job(job_id,status,start,end):
    """
    Creates job object as a dictionary. Needing the job id, job status & start/end parameters.
    """
    if type(job_id) == str:
        return {'id': job_id,
                'status': status,
                'start': start,
                'end': end}
    
    return {'id': job_id.decode('utf-8'),
            'status': status.decode('utf-8'),
            'start': start.decode('utf-8'),
            'end': end.decode('utf-8') }

def save_job(job_key, job_dict):
    """Save a job object in the Redis database."""
    #print("save_job, job_key = ", job_key)
    rd.hset(job_key,mapping = job_dict)
    

def queue_job(job_id):
    """
    Adds a job to the queue.
    """
    q.put(job_id)

#def add_job(start, end, status='submitted'):
def add_job(start, end, status):
    """
    Pushes a job to the redis queue & updates job dictionary.
    """
    print(type(start))
    print(type(end))
    job_id = generate_job_id()
    job_dict = instantiate_job(job_id,status,start,end)
    #generate_job_id_key(job_id)
    save_job(job_id, job_dict)
    queue_job(job_id)
    return jsonify(job_dict)

def update_job_status(job_id, status):
    """Update the status of job with job id `jid` to status `status`."""
    #job = get_job_by_id(job_id)
    job = rd.hgetall(job_id)
    #print('update_job, job = ', job)
    if job:
        job['status'] = status
        #save_job(_generate_job_key(jid), job)
        save_job(job_id, job)
    else:
        raise Exception()


#def create_job():
#    if type(job_id)
