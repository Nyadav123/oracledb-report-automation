#!/usr/bin/env python3
"""
Automated Oracle Report Generator and Mailer
---------------------------------------------
🧠 Features:
- Reads SQL scripts from `querymod.txt`
- Executes each query in Oracle DB
- Exports results to CSV and ZIP
- Sends via Gmail API
- Logs all steps in `logs.csv`
- Fetches all credentials securely from AWS Secrets Manager
"""

import csv
import os
import json
import zipfile
import base64
import traceback
import threading
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
import pandas as pd
import oracledb

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# -----------------------------------------------------
# Configuration
# -----------------------------------------------------
SCRIPTS_DIR     = Path("Scripts")
OUTPUT_DIR      = Path("Output")
QUERY_LIST_FILE = Path("querymod.txt")
LOG_CSV         = Path("logs.csv")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------
# Global State
# -----------------------------------------------------
log_lock = threading.Lock()

# -----------------------------------------------------
# Helper Functions
# -----------------------------------------------------

def now_ts() -> str:
    """Return formatted timestamp."""
    return datetime.now().strftime("%d-%m-%Y %H-%M-%S")


def log_append(row: list):
    """Append row to log CSV."""
    header = ["status", "job", "time", "notes"]
    with log_lock:
        write_header = not LOG_CSV.exists()
        with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(header)
            writer.writerow(row)


def log_print(stage: str, job: str, note: str = ""):
    """Print and log message."""
    ts = now_ts()
    msg = f"[{ts}] [{stage}] [{job}] {note}"
    print(msg, flush=True)
    log_append([stage, job, ts, note])


# -----------------------------------------------------
# Secret Manager
# -----------------------------------------------------

def get_secret(secret_name: str, region_name: str = "ap-south-1") -> dict:
    """
    Fetch secret JSON from AWS Secrets Manager.
    Fallback: if AWS not available, read local `local_secrets.json`.
    """
    try:
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)
        response = client.get_secret_value(SecretId=secret_name)
        secret_str = response["SecretString"]
        return json.loads(secret_str)
    except Exception as e:
        log_print("WARN", "SECRETS", f"Using local secret fallback: {e}")
        if Path("local_secrets.json").exists():
            with open("local_secrets.json", "r", encoding="utf-8") as f:
                return json.load(f)
        raise RuntimeError("Failed to fetch secrets from AWS or local file.")


# -----------------------------------------------------
# Gmail Sender via API
# -----------------------------------------------------

def send_mail_gmail_api(
    sender_email: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    recipients: list,
    subject: str,
    body_text: str,
    attachment_path: str | None = None
) -> bool:
    """Send email via Gmail API with optional attachment."""
    job_label = f"MAIL:{subject}"
    try:
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )
        creds.refresh(Request())
        service = build("gmail", "v1", credentials=creds)

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = ",".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain"))

        if attachment_path and Path(attachment_path).exists():
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{Path(attachment_path).name}"'
                )
                msg.attach(part)
            log_print("MAIL", job_label, f"Attached file {attachment_path}")

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        log_print("MAIL-SENT", job_label, f"Mail sent to {recipients}")
        return True

    except Exception as e:
        tb = traceback.format_exc()
        log_print("MAIL-ERROR", job_label, f"{e}\n{tb}")
        return False


# -----------------------------------------------------
# Oracle Query Executor
# -----------------------------------------------------

def execute_query(DB_DSN: str, sql_text: str) -> pd.DataFrame:
    """Execute SQL and return a DataFrame."""
    log_print("DB-CONNECT", "THREAD", "Opening DB connection")
    con = oracledb.connect(dsn=DB_DSN)
    cur = con.cursor()
    try:
        cur.execute(sql_text)
        cols = [col[0] for col in cur.description] if cur.description else []
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        log_print("DB-EXEC", "THREAD", f"Executed SQL | Rows={len(df)}")
        return df
    finally:
        cur.close()
        con.close()
        log_print("DB-CLOSE", "THREAD", "Connection closed.")


# -----------------------------------------------------
# Job Runner
# -----------------------------------------------------

def run_one_job(sql_filename: str, secrets: dict):
    """Run a single SQL job."""
    job_id = f"{sql_filename} {now_ts()}"
    sql_path = SCRIPTS_DIR / sql_filename
    log_print("JOB-START", job_id, "Starting job...")

    try:
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_path}")

        sql_text = sql_path.read_text(encoding="utf-8")
        df = execute_query(secrets["DB_DSN"], sql_text)

        csv_file = OUTPUT_DIR / f"{job_id}.csv"
        df.to_csv(csv_file, index=False)
        log_print("FILE-CSV", job_id, f"Wrote CSV: {csv_file}")

        zip_file = OUTPUT_DIR / f"{job_id}.zip"
        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(csv_file, arcname=csv_file.name)
        log_print("FILE-ZIP", job_id, f"Created ZIP: {zip_file}")

        subject = f"Report: {sql_filename}"
        body = (
            f"Hi All,\n\n"
            f"The report for {sql_filename} is ready.\n"
            f"Attached ZIP file contains the CSV output.\n\n"
            "Regards,\nAutomation System\n\n"
            "**This is an automated email.**"
        )

        send_mail_gmail_api(
            secrets["GMAIL_SENDER_EMAIL"],
            secrets["GMAIL_CLIENT_ID"],
            secrets["GMAIL_CLIENT_SECRET"],
            secrets["GMAIL_REFRESH_TOKEN"],
            secrets["RECEIVERS"],
            subject,
            body,
            str(zip_file)
        )

        log_append(["SUCCESS", job_id, now_ts(), "Job completed successfully"])
        log_print("JOB-DONE", job_id, "Completed successfully.")

    except Exception as e:
        tb = traceback.format_exc()
        log_print("JOB-ERROR", job_id, f"{e}\n{tb}")
        send_mail_gmail_api(
            secrets["GMAIL_SENDER_EMAIL"],
            secrets["GMAIL_CLIENT_ID"],
            secrets["GMAIL_CLIENT_SECRET"],
            secrets["GMAIL_REFRESH_TOKEN"],
            secrets["ERROR_RECEIVERS"],
            f"FAILED: {sql_filename}",
            f"Error executing job {sql_filename}\n\n{tb}"
        )
        log_append(["FAIL", job_id, now_ts(), str(e)])


# -----------------------------------------------------
# Main Entry Point
# -----------------------------------------------------

def main():
    log_print("INFO", "MAIN", "Starting automated report generation...")

    # Fetch secrets
    secrets = get_secret("report_automation_secrets")

    # Ensure query file exists
    if not QUERY_LIST_FILE.exists():
        log_print("FATAL", "MAIN", f"{QUERY_LIST_FILE} not found.")
        return

    # Read job list
    jobs = [
        line.strip()
        for line in QUERY_LIST_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    log_print("INFO", "MAIN", f"Found {len(jobs)} jobs: {jobs}")

    # Execute with thread pool
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(run_one_job, job, secrets): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                future.result()
                log_print("THREAD", job, "Completed.")
            except Exception as e:
                log_print("THREAD-ERR", job, f"Unhandled exception: {e}")

    log_print("SUMMARY", "MAIN", "All jobs completed successfully.")


if __name__ == "__main__":
    main()
