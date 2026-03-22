"""Seed 75 fake churn responses for the test account."""
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make sure the project root is on the path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.models import Account, Response
from app.db.session import SessionLocal

ACCOUNT_EMAIL = "vineet.singh1208@gmail.com"
TOTAL = 75

# 10 base templates — we cycle through them with minor word substitutions
_TEMPLATES = [
    # 0 – competitor / complexity
    [
        "We switched to Notion because it was much simpler for our whole team to use without training",
        "We moved to Notion because it was far simpler for our entire team to adopt without any training",
        "Our team switched to Notion since it was considerably simpler to use with no training required",
        "We migrated to Notion because the learning curve was almost zero for the whole team",
        "Notion won us over because every team member could use it immediately without training",
        "We chose Notion over this because the onboarding was nearly effortless for everyone",
        "The whole company moved to Notion — zero training needed and everyone was up to speed fast",
    ],
    # 1 – price
    [
        "Too expensive for what we got. We found a cheaper alternative that does 80% of the same things",
        "The pricing was too high relative to the value. A cheaper tool covers most of our needs",
        "We couldn't justify the cost. Another option at half the price does almost everything we need",
        "Way too expensive for a small team. We found a budget-friendly alternative with similar features",
        "The price-to-value ratio just wasn't there. We switched to something more affordable",
        "After our renewal quote came in, we realised a cheaper tool would serve us just as well",
        "Honestly the cost wasn't sustainable. We found a cheaper alternative that covers 80% of it",
    ],
    # 2 – complexity
    [
        "The learning curve was too steep. My team kept asking me for help every single day",
        "It was just too complex. I was constantly fielding questions from my team every day",
        "The steep learning curve was a dealbreaker. My team needed my help constantly",
        "Onboarding took forever. Team members were still confused after weeks of use",
        "Too much complexity for what we needed. The daily support requests from my team wore me out",
        "My team could never figure it out independently. Daily help requests were unsustainable",
        "The learning curve never flattened. I was still answering the same questions after two months",
    ],
    # 3 – competitor / missing feature
    [
        "We moved to ClickUp. It has the features we needed that you were missing",
        "ClickUp had the exact features we required that weren't available here",
        "We switched to ClickUp because it offered the capabilities this product was lacking",
        "ClickUp covered our feature gaps and we had to make the switch",
        "The missing features pushed us toward ClickUp which had everything we needed",
        "We tried to make it work but ClickUp had the feature set we required out of the box",
        "After comparing, ClickUp won because it had the integrations and features we were missing here",
    ],
    # 4 – service / complexity
    [
        "Couldn't figure out how to set up the integrations we needed. Support took too long to respond",
        "Integration setup was confusing and when I reached out support was very slow to reply",
        "We gave up on the integrations — too hard to configure and support wasn't responsive enough",
        "The integration documentation was unclear and support response times were too slow for us",
        "Setting up integrations was a nightmare. Support took days to get back to us each time",
        "We needed specific integrations but couldn't get them working. Support didn't help in time",
        "Integrations were too difficult to configure and support response times were unacceptably slow",
    ],
    # 5 – poor fit
    [
        "We're a small team and this felt built for enterprise. Too many features we'd never use",
        "This product is clearly designed for large teams. As a small company we're overwhelmed by features",
        "Way too much overhead for our five-person team. Built for enterprise not startups like us",
        "The feature bloat made it feel like enterprise software. Our small team didn't need most of it",
        "As a small company this felt like overkill. Too complex and feature-heavy for our size",
        "Every screen has dozens of options we'll never touch. Built for enterprise not us",
        "We're a lean team and this felt like it was designed for a 500-person company",
    ],
    # 6 – product (mobile)
    [
        "The mobile app was unusable. We need to work on the go and it just didn't work for us",
        "Our team relies on mobile heavily and the app was just too buggy and slow to use",
        "The mobile experience was terrible. We work remotely and need a reliable mobile app",
        "Mobile app kept crashing. We can't use a tool that doesn't work reliably on phones",
        "The iOS app was so buggy it was basically unusable for our field team",
        "We're a remote-first team and the mobile app performance was a constant source of frustration",
        "Mobile was an afterthought. Half our team works from their phone and the app let them down",
    ],
    # 7 – competitor
    [
        "Switched to Linear for our engineering team. Much better fit for our development workflow",
        "Linear was the obvious choice for our engineering team. Much better suited to how we work",
        "Our devs pushed for Linear and honestly it fits our engineering workflow much better",
        "We migrated to Linear — it's purpose-built for engineering teams like ours",
        "After a Linear trial the team refused to go back. Much better for our dev workflow",
        "Linear won over the entire engineering team. It just fits the way developers think and work",
        "The engineering team had been asking for Linear for months. We finally made the switch",
    ],
    # 8 – price
    [
        "Price went up at renewal and we couldn't justify it anymore given our current budget",
        "The renewal price increase was the final straw. We found a more affordable option",
        "When our plan renewed at a higher price we decided to look for alternatives",
        "The price hike at renewal forced us to reconsider whether this was worth the spend",
        "Renewal came with a 30% price increase we couldn't absorb in our current budget",
        "Our budget didn't have room for the new pricing tier. Had to look for cheaper options",
        "The annual renewal cost jumped significantly. That triggered us to evaluate alternatives",
    ],
    # 9 – consolidation / poor fit
    [
        "We consolidated tools and chose a platform that had this functionality built in already",
        "As part of a tooling review we consolidated and picked a platform with this built in",
        "Consolidating our stack meant choosing an all-in-one tool that made this redundant",
        "We reduced our SaaS spend across the board. One platform now covers what you did",
        "Our ops team consolidated tools. The platform we chose already includes this feature",
        "We moved to an all-in-one solution. Your product became redundant after that decision",
        "In a cost-cutting exercise we consolidated and a single tool replaced several products including yours",
    ],
]


def _pick_text(i: int) -> str:
    """Pick a variant for response index i, cycling through templates."""
    template_idx = i % 10
    variants = _TEMPLATES[template_idx]
    return variants[i % len(variants)]


def _random_date() -> datetime:
    """Random date within the last 6 months."""
    days_ago = random.randint(0, 180)
    return datetime.now(timezone.utc) - timedelta(days=days_ago)


def main() -> None:
    db = SessionLocal()
    try:
        account = db.query(Account).filter(Account.email == ACCOUNT_EMAIL).first()
        if account is None:
            print(f"ERROR: No account found for {ACCOUNT_EMAIL}")
            print("Register the account first via POST /api/v1/auth/register")
            sys.exit(1)

        # Remove any previously seeded test responses to allow re-running
        existing_ids = [f"tf_test_{i:03d}" for i in range(1, TOTAL + 1)]
        db.query(Response).filter(
            Response.account_id == account.id,
            Response.source_id.in_(existing_ids),
        ).delete(synchronize_session=False)
        db.commit()

        responses = []
        for i in range(TOTAL):
            source_id = f"tf_test_{i + 1:03d}"
            responses.append(
                Response(
                    id=str(uuid.uuid4()),
                    account_id=account.id,
                    source="typeform",
                    source_id=source_id,
                    text_stripped=_pick_text(i),
                    text_raw_encrypted=None,
                    response_date=_random_date(),
                    metadata_json={"form_id": "test_form_001"},
                )
            )

        db.add_all(responses)
        db.commit()
        print(f"Seeded {TOTAL} responses for account {account.id} ({ACCOUNT_EMAIL})")
    finally:
        db.close()


if __name__ == "__main__":
    random.seed(42)
    main()
