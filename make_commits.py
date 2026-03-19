import os
import random
from datetime import datetime, timedelta
import subprocess

start_date = datetime(2026, 2, 1)
end_date = datetime(2026, 3, 19)

messages = [
    "update configurations",
    "fix minor bug",
    "refactor UI component",
    "update dependencies",
    "tweak button colors",
    "improve performance",
    "update styles",
    "code cleanup",
    "update api endpoints",
    "fix typo",
    "update database schema",
    "update models",
    "add basic utilities",
    "update readme",
    "refactor code",
    "optimize loops",
    "update UI components"
]

log_file = "dev_log.txt"

current_date = start_date
count = 0

with open(log_file, "a") as f:
    f.write("Project Development Log\n")
os.system(f'git add {log_file}')
os.system(f'git commit -m "initialize development log" --date="{start_date.strftime("%Y-%m-%dT09:00:00")}"')

while current_date <= end_date:
    num_commits = random.randint(3, 4)
    for i in range(num_commits):
        hour = random.randint(9, 18)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        commit_time = current_date.replace(hour=hour, minute=minute, second=second)
        time_str = commit_time.isoformat()
        
        msg = random.choice(messages)
        
        # Modify the log file slightly
        with open(log_file, "a") as f:
            f.write(f"Commit at {time_str}: {msg}\n")
            
        os.system(f'git add {log_file}')
        os.environ['GIT_AUTHOR_DATE'] = time_str
        os.environ['GIT_COMMITTER_DATE'] = time_str
        os.system(f'git commit -m "{msg}"')
        count += 1
        
    current_date += timedelta(days=1)

print(f"Successfully created {count} commits.")
