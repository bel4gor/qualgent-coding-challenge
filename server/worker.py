import time
import random
import requests

BACKEND_URL = "http://localhost:8000"

def run_worker(max_idle_cycles=5):
    print("Worker has started! Polling for jobs...")
    idle_cycles = 0

    while idle_cycles < max_idle_cycles:
        try:
            # Ask the backend for the next job
            response = requests.get(f"{BACKEND_URL}/jobs/next")
            if response.status_code == 204:
                idle_cycles += 1
                print(f"Oops! No jobs available. Retrying... ({idle_cycles}/{max_idle_cycles})")
                time.sleep(2)
                continue

            # Job found — reset idle counter
            idle_cycles = 0
            job = response.json()
            job_id = job["job_id"]
            test_path = job["job"]["test_path"]

            print(f"Running job {job_id} for test {test_path}...")

            # Simulate test execution (random result)
            time.sleep(3)
            result = random.choice(["passed", "failed"])

            # Report result to backend
            post_resp = requests.post(f"{BACKEND_URL}/jobs/complete/{job_id}", json={"status": result})
            post_resp.raise_for_status()
            msg = post_resp.json().get("message", "")

            if "Retrying" in msg:
                print(f"Job {job_id} failed. {msg}")
            else:
                print(f"Job {job_id} completed with status: {result}")

        except Exception as e:
            print(f"Worker ran into an error: {e}")
            time.sleep(2)

    print("Worker is shutting down after too many idle cycles.")
    print(f"Goodbye.")

if __name__ == "__main__":
    run_worker()
