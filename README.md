# 🤖 Oracle Report Automation System

A fully automated Python system for executing Oracle SQL reports, exporting them to CSV/ZIP, and sending them via Gmail — with secure credentials fetched from AWS Secrets Manager.

---

## 🚀 Features

✨ **Fully Automated Workflow**
- Reads SQL scripts from `querymod.txt`
- Executes each query in Oracle Database
- Exports results to CSV and ZIP files
- Sends reports via Gmail API

🔒 **Secure Credential Handling**
- Fetches database and email credentials from AWS Secrets Manager
- Local fallback via `local_secrets.json` for offline testing

📜 **Logging & Tracking**
- Logs every step and status in `logs.csv`
- Thread-safe parallel execution of multiple SQL jobs

⚙️ **High Performance**
- Multi-threaded using Python’s `ThreadPoolExecutor`
- Separate threads for each SQL job

📧 **Email Automation**
- Uses Gmail API (OAuth2)
- Sends success and error notifications automatically

---

## 🧱 Directory Structure

