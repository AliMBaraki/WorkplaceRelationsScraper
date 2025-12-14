import os
import hashlib
from datetime import datetime
import boto3
from bs4 import BeautifulSoup
import shutil

START_DATE = "2025-11-15"
END_DATE = "2025-12-14"  
DOWNLOAD_FOLDER = "downloads"
NEW_FOLDER = "processed_files"
NEW_DYNAMO_TABLE = "processed_workplace_relations"

os.makedirs(NEW_FOLDER, exist_ok=True)

dynamodb = boto3.resource("dynamodb", region_name="eu-north-1")
table = dynamodb.Table("workplace_relations")
new_table = dynamodb.Table(NEW_DYNAMO_TABLE)

def parse_date(date_str):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {date_str}")

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of the file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def process_html_file(file_path):
    """Process HTML file using BeautifulSoup to extract content"""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    soup = BeautifulSoup(content, "html.parser")
    body = soup.find("body")
    
    if body:
        for unwanted in body.find_all(["header", "footer", "nav", "aside"]):
            unwanted.decompose()
        return str(body)
    
    return content

response = table.scan()
items = response.get("Items", [])

start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
end_dt = datetime.strptime(END_DATE, "%Y-%m-%d")

filtered_items = [
    item for item in items
    if start_dt <= parse_date(item["start_date"]) <= end_dt
]

print(f"Found {len(filtered_items)} items between {START_DATE} and {END_DATE}")

for item in filtered_items:
    file_path = item.get("file_path")
    identifier = item.get("identifier")
    
    if not file_path or not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue

    file_extension = file_path.split('.')[-1].lower()
    new_file_name = f"{identifier}.ext"
    new_file_path = os.path.join(NEW_FOLDER, new_file_name)

    print(f"Processing {file_path} for {identifier}")

    if file_extension in ["pdf", "doc", "docx"]:
        print(f"Skipping transformation for {file_path} (PDF/DOC)")
        shutil.copy2(file_path, new_file_path)

    elif file_extension == "html":
        print(f"Processing HTML file: {file_path}")
        content = process_html_file(file_path)
        with open(new_file_path, "w", encoding="utf-8") as f:
            f.write(content)

    new_file_hash = calculate_file_hash(new_file_path)

    new_item = {
        "identifier": identifier,
        "file_path": new_file_path,
        "file_hash": new_file_hash,
        "decision_date": item.get("decision_date", ""),
        "description": item.get("description", ""),
        "start_date": item.get("start_date", ""),
        "end_date": item.get("end_date", ""),
        "link": item.get("link", ""),
        "partition_date": item.get("partition_date", ""),
        "title": item.get("title", "")
    }

    new_table.put_item(Item=new_item)
    print(f"Metadata for {identifier} added to {NEW_DYNAMO_TABLE}")
