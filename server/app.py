from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List
from uuid import uuid4
from threading import Lock
import random

app = FastAPI()

# In-memory job storage
jobs_by_app_version: Dict[str, List[Dict]] = {}
job_lookup: Dict[str, Dict] = {}

# Lock for thread-safe job assignment
job_lock = Lock()

class JobSubmission(BaseModel):
    org_id: str
    app_version_id: str
    test_path: str
    priority: int = 1
    target: str  # device, emulator, browserstack

@app.post("/jobs/submit")
def submit_job(job: JobSubmission):
    job_id = str(uuid4())
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "retries": 0,
        "max_retries": 2,
        "job": job.dict()
    }

    app_version_id = job.app_version_id
    if app_version_id not in jobs_by_app_version:
        jobs_by_app_version[app_version_id] = []
    jobs_by_app_version[app_version_id].append(job_data)
    job_lookup[job_id] = job_data

    return {"job_id": job_id}

@app.get("/jobs/status/{job_id}")
def get_job_status(job_id: str):
    if job_id not in job_lookup:
        raise HTTPException(status_code=404, detail="Error: Job not found.")

    job_record = job_lookup[job_id]
    return {
        "status": job_record["status"],
        "priority": job_record["job"]["priority"],
        "test_path": job_record["job"]["test_path"],
    }

@app.get("/jobs/next")
def get_next_job():
    with job_lock:
        queued_jobs = []

        for app_version, job_list in jobs_by_app_version.items():
            for job in job_list:
                if job["status"] == "queued":
                    queued_jobs.append(job)

        if not queued_jobs:
            return JSONResponse(status_code=204, content={"message": "No jobs available."})

        # Sort by priority (lowest number = highest priority)
        sorted_jobs = sorted(queued_jobs, key=lambda j: j["job"]["priority"])
        next_job = sorted_jobs[0]
        next_job["status"] = "running"  # claim the job atomically
        return next_job

@app.post("/jobs/complete/{job_id}")
def complete_job(job_id: str, body: dict = Body(...)):
    if job_id not in job_lookup:
        raise HTTPException(status_code=404, detail="Error: Job not found.")

    status = body["status"]
    job_record = job_lookup[job_id]

    if status == "failed":
        if job_record["retries"] < job_record["max_retries"]:
            job_record["retries"] += 1
            job_record["status"] = "queued"
            return {"message": f"Retrying job... ({job_record['retries']}/{job_record['max_retries']})"}
        else:
            job_record["status"] = "failed"
            return {"message": "Job failed after max retries."}
    else:
        job_record["status"] = "passed"
        return {"message": "Job completed successfully!"}

@app.get("/jobs/debug")
def debug_jobs():
    """Return all queued jobs grouped by app_version_id for debug purposes"""
    queued = {}

    for app_version_id, job_list in jobs_by_app_version.items():
        queued[app_version_id] = [
            {
                "job_id": job["job_id"],
                "status": job["status"],
                "priority": job["job"]["priority"],
                "retries": job["retries"],
                "max_retries": job["max_retries"]
            }
            for job in job_list
            if job["status"] == "queued"
        ]

    return queued

@app.get("/health")
def health_check():
    return {"status": "Health status is good!"}
