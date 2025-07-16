# QualGent Test Queue CLI and Infrastructure

This project is a backend engineering challenge focused on building a CLI tool and scalable job processing system for AppWright end-to-end test runs. This project supports grouping, prioritizing, and dispatching test jobs across local devices, emulators, and BrowserStack instances — complete with a GitHub Actions integration and monitoring endpoints.

-----

## Project Features
- Modular CLI (`qgjob`) for job submission and status checking
- Utilizes FastAPI backend server with in-memory job queue
- Device-level grouping of tests by `app_version_id`
- Job prioritization and retry logic
- Worker process to simulate test execution
- GitHub Actions workflow to auto-submit jobs and fail on test failure
- Monitoring endpoints: `/health`
- Horizontal scaling via multiple concurrent workers

## Project Structure
```text
code-challenge/
├── cli/                # CLI tool (qgjob)
│   └── main.py
├── server/             # FastAPI backend and job queue logic
│   ├── app.py
│   └── worker.py
├── tests/              # Sample test files
├── .github/
│   └── workflows/
│       └── appwright.yml
├── setup.py            # For pip-installable CLI tool
├── README.md
└── requirements.txt    # Pinned dependencies
```

--------------------

## How it works
To minimize install/setup overhead, test jobs targeting the same app_version_id are grouped together and scheduled on the same device or environment (e.g., local device, emulator, or BrowserStack).

Each job also has an optional --priority value (default is 1). Jobs are sorted by:
-app_version_id (to group compatible tests)
- Priority (lower value = higher priority)
- Submission time (First in, First Out, within the same group and priority)

This means:

- Tests for the same app version are batched and run sequentially on the same runner.
- Higher-priority jobs are executed earlier, even across organizations.
- If a job fails, the system can retry it up to two more times.
- If a fails a third time, the entire process will end regardless if there are other jobs pending.

## Architecture Diagram:
![Architecture Diagram](https://imgur.com/6beKWXS.png)
<details> <summary>Click to view text-based diagram</summary>

qgjob CLI Tool:
(submit / status cmds)

▼

FastAPI Backend:
- Receives job requests
- Exposes REST API

▼

Job Queue:
- Groups by app_version
- Prioritizes by number (lower numbers being the highest priority)

▼

Worker Process:
- Polls for jobs
- Executes jobs and/or retries

▼

Device / Emulator / BrowserStack:
- Runs test
- Sends result
</details>

--------------------

## Prerequisites
- You will need <ins>3 Terminals</ins> open.
- Your system will need to have python downloaded
(If you need to download Pythn, visit: https://www.python.org/downloads/windows/ > Click Download Python 3.x.x (latest version). > Run the installer. > Install Now. > Verify version in your terminal: python --version )

## Machine Setup Instructions
1. Create a virtual environment on three terminals
```bash
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
```
2. Install CLI tool and dependencies
```bash
pip install -e .
pip install fastapi uvicorn requests click
```

##  How to use CLI tool
1. Start the backend server
```bash
python -m uvicorn server.app:app --host 127.0.0.1 --port 8000
```
*Keep this terminal running — it handles job submissions and status tracking.*
2. Start the worker on terminal 2
```bash
python server/worker.py
```
*The worker polls for jobs, runs them, and reports results back.*
3. Submit a test job via CLI in terminal 3.
```bash
qgjob submit --org-id=qualgent --app-version-id=xyz123 --test=tests/offboarding.spec.js --wait
```
*Wait until the job finishes and report the result*
4. You can submit multiple jobs and the worker will process them in order of priority:
```bash
qgjob submit --org-id=demo --app-version-id=xyz123 --test=tests/login.js --priority=3
qgjob submit --org-id=demo --app-version-id=xyz123 --test=tests/signup.js --priority=1
```
*Jobs are batched by app version and prioritized automatically.*
5. You can look up the job status as well:
```bash
qgjob status --job-id=<uuid>
```
*The current job status will be posted.*

##  GitHub Actions Integration
- Located at .github/workflows/appwright.yml, this workflow:
- Installs your CLI
- Starts the backend server and worker
- Submits a test job using qgjob submit
- Fails the CI if the job fails
- Try it by pushing to your repo or opening a pull request.

## Sample Output Logs
Below are example logs demonstrating job submission, execution, and retries.

---

### Single CLI Job Submission
```bash
$ qgjob submit --org-id=qualgent --app-version-id=xyz123 --test=tests/onboarding.spec.js --priority=1 --wait
Success! Job submitted: 02c57c1a-2f47-4e3e-b264-b30a7e92e804
Waiting for job: 02c57c1a-2f47-4e3e-b264-b30a7e92e804 | App Version: xyz123 | Priority: 1 | Test: tests/onboarding.spec.js to complete...
Job status: queued
Job status: running
Job status: passed
Success! Test passed.
```

### Multiple CLI Job Submission (no wait; jobs are completed in order of priority by worker)
```bash
$ qgjob submit --org-id=qualgent --app-version-id=xyz123 --test=tests/login_flow.spec.js --priority=4 --no-wait
  qgjob submit --org-id=qualgent --app-version-id=abc456 --test=tests/signup_validation.spec.js --priority=2 --no-wait
  qgjob submit --org-id=qualgent --app-version-id=abc456 --test=tests/profile_update.spec.js --priority=3 --no-wait
Success! Job submitted: e5d3bdb6-dbf5-4d4c-86ba-136414ebf0c5
Success! Job submitted: ec5977cb-82c7-4d57-b52d-1fe95ddacbbf
Success! Job submitted: 4240577b-e1af-4843-87be-c519e789b520
```

## Worker Job Processing and Waiting
```bash
$ python server/worker.py
Worker has started! Polling for jobs...
Waiting for job: 02c57c1a-2f47-4e3e-b264-b30a7e92e804 | App Version: xyz123 | Priority: 1 | Test: tests/onboarding.spec.js to complete...
Job 02c57c1a-2f47-4e3e-b264-b30a7e92e804 completed with status: passed
No jobs available. Retrying... (1/5)
No jobs available. Retrying... (2/5)
No jobs available. Retrying... (3/5)
No jobs available. Retrying... (4/5)
No jobs available. Retrying... (5/5)
Worker is shutting down after too many idle cycles.
Goodbye.
```

## Retry Logic (After Failure)
```bash
▶Waiting for job: c13acbc9-bb8d-4a3c-81c0-4c124a420001 | App Version: xyz123 | Priority: 3 | Test: tests/checkout.spec.js to complete...
Job c13acbc9-bb8d-4a3c-81c0-4c124a420001 failed. Retrying job... (1/2)
Job c13acbc9-bb8d-4a3c-81c0-4c124a420001 failed. Retrying job... (2/2)
Job c13acbc9-bb8d-4a3c-81c0-4c124a420001 completed with status: passed
```
