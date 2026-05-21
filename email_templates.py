# ============================================================
# email_templates.py — Personalized Email Templates
# ============================================================
# Each template auto-fills lead's name, company, etc.
# Add/edit templates freely. System rotates between them.
# ============================================================

import random
from config import YOUR_NAME, YOUR_COMPANY, YOUR_SERVICE, YOUR_WEBSITE, YOUR_INSTAGRAM


def get_email(lead: dict) -> tuple[str, str]:
    """
    Returns (subject, body) for a lead.
    Randomly picks from available templates for variety.
    """
    first_name = lead.get("first_name", "there")
    company = lead.get("company", "your brand")
    title = lead.get("title", "")
    industry = lead.get("industry", "")

    templates = [
        _template_collab(first_name, company),
        _template_partnership(first_name, company, title),
        _template_short_pitch(first_name, company),
    ]

    return random.choice(templates)


def _template_collab(first_name: str, company: str) -> tuple[str, str]:
    subject = f"Collaboration idea for {company} 👋"

    body = f"""Hi {first_name},

I came across {company} and love what you're building — the brand has a great energy.

I'm {YOUR_NAME}, and I run {YOUR_COMPANY}. We specialize in {YOUR_SERVICE}, and I think there could be a really natural fit between what we do and what {company} is working on.

I'd love to explore a potential collaboration — whether that's content, a campaign, or something more creative. Happy to keep it casual to start.

Would you be open to a quick 15-minute call this week?

You can also check out our work here: {YOUR_WEBSITE}

Looking forward to connecting,
{YOUR_NAME}
{YOUR_INSTAGRAM}
{YOUR_WEBSITE}"""

    return subject, body


def _template_partnership(first_name: str, company: str, title: str) -> tuple[str, str]:
    role_line = f"As {title} at {company}, " if title else f"At {company}, "

    subject = f"Quick idea — {company} x {YOUR_COMPANY}"

    body = f"""Hey {first_name},

{role_line}I imagine you're always looking for ways to grow brand visibility and connect with the right audience.

That's exactly what we help with at {YOUR_COMPANY}. We work with US brands in your space on {YOUR_SERVICE} — and we've seen strong results for brands similar to {company}.

I'd love to share a few ideas specific to {company} — no commitment, just a creative conversation.

Worth a quick chat?

Best,
{YOUR_NAME}
{YOUR_COMPANY}
{YOUR_WEBSITE}
{YOUR_INSTAGRAM}"""

    return subject, body


def _template_short_pitch(first_name: str, company: str) -> tuple[str, str]:
    subject = f"{first_name}, quick idea for {company}"

    body = f"""Hi {first_name},

Huge fan of {company} — reached out because I think we could do something interesting together.

I'm {YOUR_NAME} from {YOUR_COMPANY}. We do {YOUR_SERVICE} for US brands and creators. Short, direct, and results-focused.

Portfolio: {YOUR_WEBSITE}
Instagram: {YOUR_INSTAGRAM}

Open to a quick call or even just a DM reply if easier?

{YOUR_NAME}"""

    return subject, body


# ---- PREVIEW TEST ----
if __name__ == "__main__":
    sample_lead = {
        "first_name": "Sarah",
        "company": "Glow Beauty Co",
        "title": "Founder",
        "industry": "Beauty",
    }
    subject, body = get_email(sample_lead)
    print(f"SUBJECT: {subject}\n")
    print(f"BODY:\n{body}")
