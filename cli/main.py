import click
import requests
import time

API_URL = "http://localhost:8000"

@click.group()
def cli():
    """QualGent CLI Tool"""
    pass

@cli.command()
@click.option("--org-id", required=True, help="Organization ID")
@click.option("--app-version-id", required=True, help="App version ID")
@click.option("--test", required=True, help="Path to test file")
@click.option("--priority", default=1, type=int, help="Job priority (lower is higher priority)")
@click.option("--target", default="device", type=click.Choice(["device", "emulator", "browserstack"]), help="Test target")
@click.option("--wait/--no-wait", default=True, help="Wait for job to complete")
def submit(org_id, app_version_id, test, priority, target, wait):
    """Submit a new test job"""
    payload = {
        "org_id": org_id,
        "app_version_id": app_version_id,
        "test_path": test,
        "priority": priority,
        "target": target
    }
    try:
        response = requests.post(f"{API_URL}/jobs/submit", json=payload)
        response.raise_for_status()
        job_id = response.json()["job_id"]
        click.echo(f"Success! Job submitted: {job_id}")

        if wait:
            click.echo(f"Waiting for job: {job_id} | App Version: {app_version_id} | Priority: {priority} | Test: {test} to complete...")
            last_status = None
            while True:
                status_resp = requests.get(f"{API_URL}/jobs/status/{job_id}")
                status_resp.raise_for_status()
                status = status_resp.json().get("status")

                if status != last_status:
                    click.echo(f"Job status: {status}")
                    last_status = status

                if status in ["passed", "failed"]:
                    break
                time.sleep(3)

            if status == "failed":
                click.echo("Sorry! Test failed.")
                exit(1)
            else:
                click.echo("Success! Test passed.")

    except requests.RequestException as e:
        click.echo(f"Error submitting job: {e}")
        exit(1)

@cli.command()
@click.option("--job-id", required=True, help="Job ID to check")
def status(job_id):
    """Check job status"""
    try:
        response = requests.get(f"{API_URL}/jobs/status/{job_id}")
        response.raise_for_status()
        click.echo(f"Job Status: {response.json()['status']}")
    except requests.RequestException as e:
        click.echo(f"Could not fetch job status: {e}")

if __name__ == "__main__":
    cli()
