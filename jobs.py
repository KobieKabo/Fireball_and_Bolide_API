from uuid import uuid4

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

def queue_job(job_id):
    """
    Adds a job to the queue.
    """


def add_job(start, end, status='submitted'):
    """
    Pushes a job to the redis queue & updates job dictionary.
    """
    job_id = generate_job_id()
    job_dict = instantiate_job(job_id,status,start,end)
    generate_job_id_key(job_id)
    save_job()
    queue_job(job_id)
    return job_dict

def create_job():
    if type(job_id)
