"""
webapp.py -- Phishing email classification web application.

A Flask application that demonstrates the phishing classifier with:
- Email inbox with HAM and PHISHING separation
- Email synchronization (generation + classification)
- Agent logs showing classification decisions
- Real-time email scanning and categorization
"""

import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import numpy as np

from agent import PhishingAgent
from generate_data import (
    generate_phishing_email,
    generate_ham_email,
    PHISHING_SUBJECTS,
    PHISHING_BODIES,
    HAM_SUBJECTS,
    HAM_BODIES,
)

# Initialize Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///phishing_mailbox.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Initialize agent
agent = PhishingAgent(model_path="phishing_model.joblib")

# Database Models
class Email(db.Model):
    """Email message stored in the mailbox."""

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    full_text = db.Column(db.Text, nullable=False)
    email_type = db.Column(db.String(50), nullable=False)  # "HAM" or "PHISHING"
    agent_prediction = db.Column(db.String(50), nullable=False)  # What agent predicted
    agent_confidence = db.Column(db.Float, nullable=False)
    is_correct = db.Column(
        db.Boolean, nullable=False
    )  # True if agent prediction matches email_type
    folder = db.Column(db.String(50), default="inbox")  # "inbox" or "junk"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    logs = db.relationship("ScanLog", backref="email", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "subject": self.subject,
            "body": self.body[:200] + "..." if len(self.body) > 200 else self.body,
            "full_body": self.body,
            "email_type": self.email_type,
            "agent_prediction": self.agent_prediction,
            "agent_confidence": f"{self.agent_confidence:.2%}",
            "is_correct": self.is_correct,
            "folder": self.folder,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "N/A",
        }


class ScanLog(db.Model):
    """Log of agent scanning decisions."""

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey("email.id"), nullable=False)
    agent_label = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    matched_patterns = db.Column(db.Text, nullable=False)  # JSON
    assumptions = db.Column(db.Text, nullable=False)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "email_id": self.email_id,
            "agent_label": self.agent_label,
            "confidence": f"{self.confidence:.2%}",
            "matched_patterns": json.loads(self.matched_patterns),
            "assumptions": json.loads(self.assumptions),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "N/A",
        }


def generate_random_email(email_type: str) -> tuple[str, str]:
    """Generate a random email subject and body."""
    import random

    random.seed()  # Use system time for randomness

    if email_type == "PHISHING":
        subject = random.choice(PHISHING_SUBJECTS)
        body = random.choice(PHISHING_BODIES)
    else:  # HAM
        subject = random.choice(HAM_SUBJECTS)
        body = random.choice(HAM_BODIES)

    return subject, body


def scan_email(text: str) -> tuple[str, float, list, list]:
    """Scan email using the agent and return prediction details."""
    result = agent.scan(text)
    return (
        result["label"],
        result["confidence"],
        result["matches"],
        result["assumptions"],
    )


def generate_adversarial_email(email_type: str) -> tuple[str, str]:
    """Generate ambiguous/tricky emails that fool classifiers."""
    import random
    
    if email_type == "PHISHING":
        # Phishing disguised as legitimate email
        tricky_phishing = [
            ("Team meeting rescheduled", "Hi,\n\nOur meeting is now at 3pm. Please click here to confirm attendance.\n\nThanks"),
            ("Document review needed", "Hi,\n\nCan you verify the attached document? Click to review and approve.\n\nRegards"),
            ("Project update", "Hi,\n\nPlease review the following and confirm receipt:\nupdate-link.html\n\nThanks"),
            ("Account notification", "Hello,\n\nWe need to confirm some details. Please visit our site to check.\n\nThank you"),
            ("Invoice for approval", "Hi,\n\nPlease review and approve this invoice:\nclick here\n\nThanks"),
        ]
        subject, body = random.choice(tricky_phishing)
    else:
        # Legitimate email that looks suspicious
        tricky_ham = [
            ("URGENT: Please respond", "Hi team,\n\nWe need your feedback ASAP on the new process.\n\nPlease reply by EOD.\n\nThanks"),
            ("Action required", "Hi,\n\nCan you please verify your contact details in our system?\n\nLogin here\n\nThanks"),
            ("Security reminder", "Hi,\n\nPlease update your password to comply with new policies.\n\nChange now\n\nThank you"),
            ("Urgent: System maintenance", "Alert: We're performing urgent system updates.\n\nPlease confirm your credentials to maintain access.\n\nClick here"),
            ("Please confirm", "Hi,\n\nPlease confirm you received this message by clicking the link below.\n\nConfirm\n\nThanks"),
        ]
        subject, body = random.choice(tricky_ham)
    
    return subject, body


# Routes
@app.route("/")
def index():
    """Homepage - show inbox."""
    return redirect(url_for("inbox"))


@app.route("/inbox")
def inbox():
    """Display inbox with legitimate emails (HAM)."""
    emails = Email.query.filter_by(folder="inbox").order_by(Email.created_at.desc()).all()
    stats = {
        "total_inbox": len(emails),
        "correct_classifications": sum(1 for e in emails if e.is_correct),
        "false_positives": sum(1 for e in emails if not e.is_correct and e.email_type == "PHISHING"),
    }
    return render_template("inbox.html", emails=emails, stats=stats)


@app.route("/junk")
def junk():
    """Display junk folder with emails classified as phishing."""
    emails = Email.query.filter_by(folder="junk").order_by(Email.created_at.desc()).all()
    stats = {
        "total_junk": len(emails),
        "correct_classifications": sum(1 for e in emails if e.is_correct),
        "false_negatives": sum(1 for e in emails if not e.is_correct and e.email_type == "HAM"),
    }
    return render_template("junk.html", emails=emails, stats=stats)


@app.route("/inbox/logs")
def logs():
    """Display agent scanning logs."""
    logs = ScanLog.query.order_by(ScanLog.created_at.desc()).all()
    
    # Calculate statistics
    total_scans = len(logs)
    phishing_detected = sum(1 for log in logs if log.agent_label == "PHISHING")
    ham_detected = sum(1 for log in logs if log.agent_label == "HAM")
    
    stats = {
        "total_scans": total_scans,
        "phishing_detected": phishing_detected,
        "ham_detected": ham_detected,
        "avg_confidence": f"{np.mean([log.confidence for log in logs]):.2%}" if logs else "0%",
    }

    return render_template("logs.html", logs=logs, stats=stats)


@app.route("/api/sync", methods=["POST"])
def sync_emails():
    """Generate and classify a batch of new emails."""
    try:
        # Check if model exists
        if not Path("phishing_model.joblib").exists():
            return jsonify({"status": "error", "message": "Model not trained. Run 'python train.py' first."}), 400

        num_emails = request.json.get("count", 5) if request.is_json else 5
        
        # Generate emails (mix of clean and adversarial for realistic false positives/negatives)
        created_emails = []
        for i in range(num_emails):
            # Alternate between HAM and PHISHING for variety
            email_type = "PHISHING" if i % 2 == 0 else "HAM"
            
            # 40% of emails use adversarial generation to create harder test cases
            import random
            use_adversarial = random.random() < 0.4
            
            if use_adversarial:
                subject, body = generate_adversarial_email(email_type)
            else:
                subject, body = generate_random_email(email_type)
            
            full_text = f"Subject: {subject}\n\n{body}"

            # Scan the email
            prediction, confidence, matches, assumptions = scan_email(full_text)

            # Determine if classification is correct
            is_correct = (email_type == "PHISHING" and prediction == "PHISHING") or (
                email_type == "HAM" and prediction == "HAM"
            )

            # Determine folder based on agent prediction (not actual type)
            folder = "junk" if prediction == "PHISHING" else "inbox"

            # Create email record
            email = Email(
                subject=subject,
                body=body,
                full_text=full_text,
                email_type=email_type,
                agent_prediction=prediction,
                agent_confidence=confidence,
                is_correct=is_correct,
                folder=folder,
            )

            # Create scan log
            log = ScanLog(
                email=email,
                agent_label=prediction,
                confidence=confidence,
                matched_patterns=json.dumps([(m[0], m[1]) for m in matches]),
                assumptions=json.dumps(assumptions),
            )

            db.session.add(email)
            db.session.add(log)
            created_emails.append(email.to_dict())

        db.session.commit()

        return jsonify(
            {
                "status": "success",
                "message": f"Synced {num_emails} emails",
                "emails": created_emails,
            }
        )

    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Model file not found. Train the model first."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/email/<int:email_id>")
def get_email(email_id):
    """Get full email details and scan log."""
    email = Email.query.get_or_404(email_id)
    log = ScanLog.query.filter_by(email_id=email_id).first()

    return jsonify(
        {
            "email": email.to_dict(),
            "log": log.to_dict() if log else None,
        }
    )


@app.route("/api/clear-all", methods=["POST"])
def clear_all():
    """Clear all emails and logs (for demo reset)."""
    try:
        Email.query.delete()
        ScanLog.query.delete()
        db.session.commit()
        return jsonify({"status": "success", "message": "All emails and logs cleared"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stats")
def get_stats():
    """Get overall statistics."""
    total_emails = Email.query.count()
    inbox_count = Email.query.filter_by(folder="inbox").count()
    junk_count = Email.query.filter_by(folder="junk").count()
    correct_classifications = Email.query.filter_by(is_correct=True).count()

    return jsonify(
        {
            "total_emails": total_emails,
            "inbox_count": inbox_count,
            "junk_count": junk_count,
            "correct_classifications": correct_classifications,
            "accuracy": f"{(correct_classifications / total_emails * 100):.1f}%" if total_emails > 0 else "N/A",
        }
    )


if __name__ == "__main__":
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    print("Starting Phishing Email Classifier Web App")
    print("Navigate to http://127.0.0.1:5000/")
    app.run(debug=True, port=5000)
