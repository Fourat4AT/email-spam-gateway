


# Email Spam Gateway

This project is an intelligent **email filtering system** that connects to a Gmail inbox, classifies incoming emails as **SPAM** or **HAM** using a machine learning model, and logs the results to the **ELK Stack** for real-time monitoring and visualization.

---

## What It Does

- Connects to Gmail using the Gmail API
- Fetches the latest emails and their metadata
- Classifies them using a trained ML model (`spam_classifier.pkl`)
- Logs results in JSON format and forwards them to Elasticsearch
- Visualizes logs and spam detection stats in **Kibana**

---

##  Tech Stack

| Tool            | Purpose                          |
|-----------------|----------------------------------|
| Python 3        | Main programming language        |
| Scikit-learn    | Machine learning model           |
| Gmail API       | Access to your Gmail inbox       |
| Elasticsearch   | Email log storage and search     |
| Kibana          | Visualization of logs            |
| Logstash        | Optional for piping to Elasticsearch |

---

##  Folder Structure


Email-Spam-Gateway/

├── spam_filter.py # Main Python script
├── spam_classifier.pkl # Trained ML model
├── vectorizer.pkl # TF-IDF vectorizer
├── classified_emails.json # Logged results
├── credentials.json # Gmail API credentials
├── token.json # Gmail API access token
├── .gitignore
└── README.md

---

## 🧠 How It Works

1. Authenticates with Gmail using OAuth
2. Fetches recent email metadata and snippet
3. Extracts headers (e.g. `From`, `Subject`, SPF, DKIM)
4. Predicts if the email is **SPAM** or **HAM**
5. Logs structured data to a JSON file and ELK

---
👤 Author
Fourat Beji
GitHub @Fourat4AT


