# Phishing Email Classifier Web Application

A modern, interactive web application for demonstrating phishing email detection using machine learning.

## Features

✨ **Inbox Management**
- View incoming emails classified as legitimate (HAM)
- Click on any email to see full details and agent analysis
- Track false positives (phishing emails misclassified as HAM)

🗑️ **Junk Folder**
- View emails detected as phishing by the agent
- Monitor false negatives (legitimate emails misclassified as phishing)
- See agent confidence scores for each classification

📋 **Agent Logs**
- Complete scanning history with timestamps
- Detected patterns and signatures for each email
- Agent assumptions explaining the classification
- Aggregate statistics on detection rates

🔄 **Email Synchronization**
- Generate synthetic emails (mix of HAM and PHISHING)
- Automatically classify with the trained ML model
- Save classification results with confidence scores
- No manual email creation needed

## Quick Start

### 1. Prerequisites
Ensure the model is trained:
```bash
python train.py
```

### 2. Start the Web App
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python webapp.py
```

The app will be available at: **http://127.0.0.1:5000/**

### 3. Using the App

#### Generate Emails
1. Click **"🔄 Sync Incoming Emails"** button
2. The system will:
   - Generate 5 random emails (mix of HAM and PHISHING)
   - Scan each email with the trained agent
   - Classify them based on agent prediction
   - **Real phishing emails are NOT automatically marked as junk!**
   - Only emails the agent detects as phishing go to junk

#### Inbox Tab
- Shows emails classified as **HAM** (legitimate)
- Displays confidence scores
- Green checkmark (✓) = correct classification
- Orange X (✗) = false positive (real phishing misclassified as HAM)

#### Junk Tab
- Shows emails classified as **PHISHING**
- Green checkmark (✓) = correct classification
- Orange X (✗) = false negative (real HAM misclassified as PHISHING)

#### Logs Tab
- View all scanning operations with timestamps
- See detected signature patterns
- Review agent assumptions for each classification
- Statistics on overall detection performance

## Key Concept: Agent-Based Classification

**Important:** This webapp demonstrates a critical security principle:
- Emails are NOT automatically moved to junk based on their "true type"
- **The agent predicts first**, and the folder assignment is based on the prediction
- This allows demonstrating:
  - False positives (agent misses real phishing)
  - False negatives (agent wrongly flags legitimate mail)
  - How imperfect classifiers can be fooled

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Redirect to inbox |
| `/inbox` | GET | View legitimate emails |
| `/junk` | GET | View detected phishing emails |
| `/inbox/logs` | GET | View agent scanning logs |
| `/api/sync` | POST | Generate and classify new emails |
| `/api/email/<id>` | GET | Get full email details and analysis |
| `/api/stats` | GET | Get overall statistics |
| `/api/clear-all` | POST | Clear all emails and logs |

### Example: Generate Emails via API
```bash
curl -X POST http://127.0.0.1:5000/api/sync \
  -H "Content-Type: application/json" \
  -d '{"count": 10}'
```

### Example: Get Email Details
```bash
curl http://127.0.0.1:5000/api/email/1
```

### Example: Get Statistics
```bash
curl http://127.0.0.1:5000/api/stats
```

## Database

The app uses SQLite with the following tables:

**Email Table**
- `id`: Unique identifier
- `subject`: Email subject line
- `body`: Email body text
- `full_text`: Complete email with subject
- `email_type`: Actual type (HAM or PHISHING)
- `agent_prediction`: What the agent predicted
- `agent_confidence`: Prediction confidence (0-1)
- `is_correct`: Whether prediction matches actual type
- `folder`: Storage folder (inbox or junk)
- `created_at`: Timestamp

**ScanLog Table**
- `id`: Log entry ID
- `email_id`: Reference to email
- `agent_label`: Prediction (HAM or PHISHING)
- `confidence`: Confidence score
- `matched_patterns`: Detected phishing signatures
- `assumptions`: Agent reasoning
- `created_at`: Timestamp

Database file: `phishing_mailbox.db`

## Demonstration Talking Points

Perfect for a 5-minute live demo:

1. **Start fresh:** Click "Clear All" to reset
2. **Generate emails:** Click "Sync Incoming Emails" to create 5 sample emails
3. **Show accuracy:** Display inbox and junk tabs to show classifications
4. **Highlight problems:** 
   - Scroll to logs to show false positives/negatives
   - Click an email to see what signatures the agent detected
5. **Interactive testing:** Generate more emails, ask audience about confidence
6. **Conclusion:** Explain why robustness testing (via `attack.py`) is crucial

## Team Integration

This webapp complements your team's work:

- **Data Team (Sebastian)**: Uses `generate_data.py` functions to seed emails
- **Model Team (Liam, Mert)**: Validates trained model performance visually
- **Attack Team (André)**: Can test attack scenarios and see false positives
- **Presentation Team (Abdulghani)**: Perfect for live demo and stakeholder presentations

## Troubleshooting

### "Model file not found" error
- Run `python train.py` to train the model first
- Ensure `phishing_model.joblib` exists in the root directory

### Database locked error
- Close the app: `Ctrl+C`
- Delete `phishing_mailbox.db`
- Restart the app: `python webapp.py`

### Port 5000 already in use
- Stop other Flask apps
- Or modify the port in `webapp.py`: `app.run(debug=True, port=5001)`

## Security Note

This is a **demonstration app** for educational purposes. It is not suitable for production use:
- No authentication/authorization
- No rate limiting
- All data stored in local SQLite
- No encryption in transit

For real phishing detection, consider:
- SPF/DKIM/DMARC verification
- URL reputation checking
- Content filtering with DLP
- User training and reporting
- Integration with enterprise email security

## Performance

- Lightweight (~2 MB model size)
- Instant email generation
- Agent scanning typically completes in milliseconds
- Supports hundreds of emails without slowdown

## License & Credits

Part of the Lillteamet Phishing Classifier project.

---

**Questions?** Check the main [README.md](README.md) for project context and team info.
