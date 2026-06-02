"""
generate_data.py -- Synthetic phishing / ham email dataset.

Produces a deterministic dataset of ~600 short email texts with binary labels:
    1 = phishing
    0 = ham (legitimate)

Fixed random seed ensures reproducibility: same dataset every run, no downloads.
"""

import numpy as np
import pandas as pd

SEED = 42


# ---------------------------------------------------------------------------
# Word pools
# ---------------------------------------------------------------------------

PHISHING_SUBJECTS = [
    "urgent account verification required",
    "your account has been suspended",
    "verify your information immediately",
    "security alert: action required",
    "your payment failed - update now",
    "click here to claim your reward",
    "limited time offer expires today",
    "confirm your identity or lose access",
    "unusual activity on your account",
    "your password will expire soon",
]

PHISHING_BODIES = [
    "Dear customer, your account has been temporarily suspended. Click here to verify your identity immediately or your access will be terminated.",
    "Urgent: We detected suspicious login attempts on your account. Verify your credentials now to avoid losing access.",
    "Your bank account requires immediate attention. Provide your details within 24 hours to prevent account closure.",
    "Congratulations! You have been selected for a special reward. Click the link below to claim $500 now.",
    "Warning: Your password expires in 24 hours. Update it immediately by clicking here or you will be locked out.",
    "We noticed unusual activity on your account. Confirm your information now to secure your account and avoid suspension.",
    "Your invoice payment is overdue. Provide your credit card details immediately to avoid late fees and service interruption.",
    "Final notice: verify your email address now or your account will be deleted within 24 hours.",
    "Dear valued user, your account security is at risk. Click here to verify your identity and restore full access.",
    "You have a pending package delivery. Confirm your address and pay a small customs fee to receive your item.",
    "IMPORTANT: Your Netflix subscription has expired. Update your billing information now to continue watching.",
    "Your PayPal account is limited. Please confirm your details to lift the limitation immediately.",
    "Action required: unusual sign-in detected on your Microsoft account. Verify now or your account will be suspended.",
    "You have won a prize in our latest lottery. Send your bank details to claim your winnings today.",
    "Immediate action needed: your Social Security number may have been compromised. Verify your identity now.",
]

HAM_SUBJECTS = [
    "team meeting tomorrow at 10am",
    "re: project update for this week",
    "lunch plans for Friday?",
    "welcome to the new team member",
    "reminder: submit your timesheet",
    "notes from yesterday's standup",
    "quick question about the report",
    "office closed on public holiday",
    "feedback on your presentation",
    "monthly newsletter from the library",
]

HAM_BODIES = [
    "Hi everyone, just a reminder that our weekly team meeting is tomorrow at 10am in conference room B. Please bring your project updates.",
    "Hi Sara, I reviewed the draft you sent over. Looks good overall. I have a few small suggestions, I'll send them over later today.",
    "Hey, are you free for lunch on Friday? There's a new Thai place near the office I've been wanting to try.",
    "Welcome to the team! Please help me in welcoming our new colleague who joins us this Monday in the Stockholm office.",
    "This is a reminder to submit your timesheet by end of day Thursday. Contact HR if you have any questions.",
    "Here are the notes from yesterday's standup. Main discussion points: the API refactor is on track, deployment scheduled for next week.",
    "Hi, I had a quick question about the Q2 report format. Should we include the appendix from last year or update it with new data?",
    "Please note that the office will be closed on Monday due to the public holiday. Enjoy the long weekend!",
    "Thank you for your presentation today. The stakeholders were impressed. A few follow-up questions came in, I'll forward them shortly.",
    "The monthly book club newsletter is attached. This month we are reading a novel set in northern Sweden during winter.",
    "Just wanted to check in on how you are settling in to the new role. Let me know if you need anything from my side.",
    "The Q3 budget review meeting has been moved to Wednesday at 2pm. The agenda will be shared by end of today.",
    "Can you send me the link to the shared drive folder again? I seem to have lost the bookmark on my new laptop.",
    "Great news: the client approved the proposal. We can start the discovery phase next week. I'll set up a kick-off call.",
    "Reminder: the all-hands meeting is at 3pm today. Dial-in details are in the calendar invite you received last week.",
]

PHISHING_FRAGMENTS = [
    "click here to verify",
    "your account will be suspended",
    "urgent action required",
    "provide your password",
    "confirm your bank details",
    "limited time offer",
    "claim your reward now",
    "your account has been compromised",
    "immediate verification needed",
    "do not ignore this message",
]

HAM_FRAGMENTS = [
    "please let me know if you have questions",
    "looking forward to meeting you",
    "see you at the meeting",
    "thanks for your help",
    "have a great weekend",
    "let me know your thoughts",
    "i'll send the files tomorrow",
    "talk to you soon",
    "hope you are doing well",
    "best regards",
]


def _build_phishing_email(rng: np.random.Generator) -> str:
    subject = rng.choice(PHISHING_SUBJECTS)
    body = rng.choice(PHISHING_BODIES)
    fragment = rng.choice(PHISHING_FRAGMENTS)
    # Sometimes add an extra urgency fragment
    if rng.random() > 0.5:
        return f"Subject: {subject}\n\n{body} {fragment}."
    return f"Subject: {subject}\n\n{body}"


def _build_ham_email(rng: np.random.Generator) -> str:
    subject = rng.choice(HAM_SUBJECTS)
    body = rng.choice(HAM_BODIES)
    fragment = rng.choice(HAM_FRAGMENTS)
    if rng.random() > 0.5:
        return f"Subject: {subject}\n\n{body} {fragment}."
    return f"Subject: {subject}\n\n{body}"


def generate_dataset(n_phishing: int = 300, n_ham: int = 300) -> pd.DataFrame:
    """Return a DataFrame with columns: text, label (1=phishing, 0=ham)."""
    rng = np.random.default_rng(SEED)

    texts = []
    labels = []

    for _ in range(n_phishing):
        texts.append(_build_phishing_email(rng))
        labels.append(1)

    for _ in range(n_ham):
        texts.append(_build_ham_email(rng))
        labels.append(0)

    df = pd.DataFrame({"text": texts, "label": labels})
    # Shuffle rows so classes are interleaved
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = generate_dataset()
    print(f"Dataset: {len(df)} samples ({df['label'].sum()} phishing, {(df['label']==0).sum()} ham)")
    print("\nSample phishing email:")
    print(df[df["label"] == 1]["text"].iloc[0])
    print("\nSample ham email:")
    print(df[df["label"] == 0]["text"].iloc[0])
