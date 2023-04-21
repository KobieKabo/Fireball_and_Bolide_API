import uuid
from flask import Flask
from jobs import q, update_job_status

app = Flask(__name__)


#FINISH THIS CODE for worker.py
@q.worker
def execute_job(job_id):
    """
    Retrieve a job id from the task queue and execute the job.
    Monitors the job to completion and updates the database accordingly.
    """
    jobs.ubdate_job_status(job_id, 'in progress')
    time.sleep(15)
    jobs.update_job_status(job_id, "complete")

