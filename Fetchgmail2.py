import sys
import joblib
import smtplib
import json
import time
from email import policy
from email.parser import BytesParser
from email.message import EmailMessage

# Load ML model and vectorizer (paths relative or absolute)
model = joblib.load("/home/gateway/Desktop/tool/email-spam-gateway/spam_classifier.pkl")
vectorizer = joblib.load("/home/gateway/Desktop/tool/email-spam-gateway/vectorizer.pkl")

# Real mail server to forward to (VM2 IP or hostname)


REAL_MAIL_SERVER = "192.168.1.58"
REAL_MAIL_PORT = 25

# Optional log file path
LOG_PATH = "/home/gateway/Desktop/tool/email-spam-gateway/classified_emails.json"

def classify_email(text):
    features = vectorizer.transform([text])
    prediction = model.predict(features)
    return "HAM" if prediction[0] == 1 else "SPAM"

def extract_plain_text(email_message):
    # Extract plain text body from multipart or single part email
    if email_message.is_multipart():
        for part in email_message.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition"))
            if ctype == "text/plain" and "attachment" not in disp:
                return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
    else:
        return email_message.get_payload(decode=True).decode(email_message.get_content_charset() or "utf-8", errors="replace")
    return ""

def log_classification(data):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

def forward_email(raw_email, email_message):
    from_addr = email_message.get("From", "")
#    to_addr = email_message.get("To", "")
    to_addr = "fourat@mailserver.local"
    

    with smtplib.SMTP(REAL_MAIL_SERVER, REAL_MAIL_PORT) as smtp:
        smtp.sendmail(from_addr, [to_addr], raw_email)

def main():
    # Read raw email from stdin (binary mode)
    raw_email = sys.stdin.buffer.read()

    # Parse email
    email_message = BytesParser(policy=policy.default).parsebytes(raw_email)

    # Extract plain text for classification
    text = extract_plain_text(email_message)

    # Classify
    classification = classify_email(text)

    # Log
    log_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "from": email_message.get("From"),
        "to": email_message.get("To"),
        "subject": email_message.get("Subject"),
        "classification": classification
    }
    log_classification(log_data)

    if classification == "HAM":
        # Forward raw email to real mail server
        forward_email(raw_email, email_message)
        sys.stderr.write("Ham. Email sent.\n")
        sys.exit(0)  # Accept email
    else:
        # Reject/drop spam email
        sys.stderr.write("Spam detected. Email rejected.\n")
        sys.exit(1)  # Reject email

if __name__ == "__main__":
    main()