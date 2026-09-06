import csv
import os

data = [
    ["Test ID", "Category", "Scenario", "Expected Result", "Status"],
    ["T01", "API Baseline", "GET / Request", "200 OK", "PASS"],
    ["T02", "Core AI", "POST /diagnose with Leaf Image", "Diagnosis & Advice returned", "PASS"],
    ["T03", "Fallback", "Blurry/Unclear Leaf Photo", "Needs Expert = True", "PASS"],
    ["T04", "Negative Test", "POST /diagnose without image", "422 Validation Error", "PASS"],
    ["T05", "Followup AI", "POST /ask-followup with question", "Relevant Urdu response", "PASS"],
    ["T06", "Integration", "Frontend Upload -> Backend API", "Result renders on React UI", "PASS"]
]

os.makedirs("documentation", exist_ok=True)
file_path = "documentation/Member5_Testing_Report.csv"

with open(file_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(data)

print(f"Testing Report Successfully Generated: {file_path}")