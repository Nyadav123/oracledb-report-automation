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

## 🗂️ Directory Structure

oracle-report-automation/
│
├── Scripts/ # Folder containing .sql query files
│ ├── sales_report.sql
│ ├── inventory_report.sql
│ └── ...
│
├── Output/ # Auto-generated CSV and ZIP files
│ ├── sales_report_24-10-2025.csv
│ ├── sales_report_24-10-2025.zip
│ └── ...
│
├── logs.csv # Log file with job details and status
├── querymod.txt # List of SQL script filenames to run
├── local_secrets.json # Local fallback secrets (for testing)
├── report_automation.py # 🚀 Main script
└── README.md # Project documentation

yaml
Copy code

---

## 🔐 Secrets Configuration

Your **AWS Secrets Manager** JSON must contain the following keys:

```json
{
  "DB_DSN": "user/password@hostname:port/service",
  "GMAIL_SENDER_EMAIL": "your_email@gmail.com",
  "GMAIL_CLIENT_ID": "your-client-id",
  "GMAIL_CLIENT_SECRET": "your-client-secret",
  "GMAIL_REFRESH_TOKEN": "your-refresh-token",
  "RECEIVERS": ["report-team@example.com"],
  "ERROR_RECEIVERS": ["devops-team@example.com"]
}
Alternatively, store the same structure in a local file named:

pgsql
Copy code
local_secrets.json
⚙️ Installation
1️⃣ Clone Repository
bash
Copy code
git clone https://github.com/<your-username>/oracle-report-automation.git
cd oracle-report-automation
2️⃣ Create Virtual Environment
bash
Copy code
python3 -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)
3️⃣ Install Dependencies
bash
Copy code
pip install -r requirements.txt
4️⃣ Configure AWS or Local Secrets
Ensure AWS credentials are configured (aws configure)

OR create local_secrets.json with the structure shown above

5️⃣ Add SQL Jobs
Add the names of your .sql files to querymod.txt, one per line:

pgsql
Copy code
sales_report.sql
inventory_report.sql
▶️ Usage
Run the automation script:

bash
Copy code
python report_automation.py
Example Output:

css
Copy code
[24-10-2025 10-00-00] [INFO] [MAIN] Starting automated report generation...
[24-10-2025 10-00-01] [JOB-START] [sales_report.sql] Starting job...
[24-10-2025 10-00-10] [JOB-DONE] [sales_report.sql] Completed successfully.
[24-10-2025 10-00-11] [SUMMARY] [MAIN] All jobs completed successfully.
🧩 Technologies Used
Area	Technology
💾 Database	Oracle
☁️ Cloud	AWS Secrets Manager
📧 Email	Gmail API
🐍 Language	Python 3
📊 Data	Pandas, CSV, ZIP
⚡ Concurrency	ThreadPoolExecutor
🪵 Logging	CSV logs

🧠 Logging Format
Every operation (success/failure) is appended to logs.csv:

status	job	time	notes
SUCCESS	sales_report.sql	24-10-2025 10:00:10	Job completed successfully
FAIL	inventory_report.sql	24-10-2025 10:05:22	ORA-00942: Table not found

🛠️ Example querymod.txt
pgsql
Copy code
sales_report.sql
inventory_report.sql
customer_summary.sql
Each .sql file must exist inside the Scripts/ folder.

🧾 License
MIT License © 2025 — Created by [Your Name]

💡 Author Notes
🧩 This project is ideal for:

Automating daily/weekly report generation

Teams handling large Oracle-based analytics workloads

Reducing manual report execution and email tasks

🌟 Contributions & Pull Requests Welcome!

🧰 Icons Used
🤖 Automation

🗂️ Structure

📧 Mail

🔐 Security

🧠 Logging

⚙️ Configuration

🪵 Log tracking
