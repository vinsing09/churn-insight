"""Weekly digest email via Resend."""
import logging

import resend
from resend.exceptions import ResendError

from app.core.config import settings

logger = logging.getLogger(__name__)

_FROM = "Churn Insight <digest@churninsight.io>"


def _priority_badge(score: float) -> str:
    if score >= 0.7:
        return (
            '<span style="background:#ef4444;color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:700;">HIGH</span>'
        )
    if score >= 0.4:
        return (
            '<span style="background:#f59e0b;color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:700;">MED</span>'
        )
    return (
        '<span style="background:#6b7280;color:#fff;padding:2px 8px;'
        'border-radius:4px;font-size:11px;font-weight:700;">LOW</span>'
    )


def _build_html(account_id: str, stats: dict) -> str:
    new_responses: int = stats.get("new_responses", 0)
    total_responses: int = stats.get("total_responses", 0)
    themes: list[dict] = stats.get("themes", [])
    new_theme_names: list[str] = stats.get("new_themes", [])
    top_headline: str | None = stats.get("top_brief_headline")

    dashboard_url = settings.FRONTEND_URL

    # ── New-this-week section ─────────────────────────────────────────────────
    new_themes_html = ""
    if new_theme_names:
        items = "".join(
            f'<li style="margin:4px 0;color:#d1d5db;">{name}</li>'
            for name in new_theme_names
        )
        new_themes_html = f"""
        <tr><td style="padding:24px 0 8px;">
          <p style="margin:0 0 12px;font-size:13px;font-weight:600;
                     text-transform:uppercase;letter-spacing:.05em;color:#9ca3af;">
            New this week
          </p>
          <ul style="margin:0;padding-left:20px;">{items}</ul>
        </td></tr>"""

    # ── Top 3 themes table ────────────────────────────────────────────────────
    top3 = themes[:3]
    theme_rows = ""
    for theme in top3:
        name = theme.get("name", "—")
        count = theme.get("response_count", 0)
        score = float(theme.get("priority_score", 0))
        theme_rows += f"""
        <tr>
          <td style="padding:10px 12px;color:#e5e7eb;font-size:14px;">{name}</td>
          <td style="padding:10px 12px;color:#9ca3af;font-size:14px;
                     text-align:center;">{count}</td>
          <td style="padding:10px 12px;text-align:center;">{_priority_badge(score)}</td>
        </tr>"""

    themes_table = f"""
    <tr><td style="padding:24px 0 8px;">
      <p style="margin:0 0 12px;font-size:13px;font-weight:600;
                 text-transform:uppercase;letter-spacing:.05em;color:#9ca3af;">
        Top themes
      </p>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;background:#1f2937;border-radius:8px;
                    overflow:hidden;">
        <thead>
          <tr style="background:#111827;">
            <th style="padding:8px 12px;text-align:left;font-size:11px;
                       color:#6b7280;text-transform:uppercase;
                       letter-spacing:.05em;">Theme</th>
            <th style="padding:8px 12px;text-align:center;font-size:11px;
                       color:#6b7280;text-transform:uppercase;
                       letter-spacing:.05em;">Responses</th>
            <th style="padding:8px 12px;text-align:center;font-size:11px;
                       color:#6b7280;text-transform:uppercase;
                       letter-spacing:.05em;">Priority</th>
          </tr>
        </thead>
        <tbody>{theme_rows}</tbody>
      </table>
    </td></tr>""" if top3 else ""

    # ── Top brief headline ────────────────────────────────────────────────────
    headline_html = ""
    if top_headline:
        headline_html = f"""
        <tr><td style="padding:24px 0 8px;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;
                     text-transform:uppercase;letter-spacing:.05em;color:#9ca3af;">
            This week's top angle
          </p>
          <div style="background:#1f2937;border-left:3px solid #6366f1;
                      border-radius:0 8px 8px 0;padding:14px 16px;">
            <p style="margin:0;font-size:16px;font-weight:600;
                       color:#e5e7eb;line-height:1.4;">
              &ldquo;{top_headline}&rdquo;
            </p>
          </div>
        </td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#030712;font-family:-apple-system,BlinkMacSystemFont,
             'Segoe UI',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="max-width:580px;background:#111827;border-radius:12px;
                    overflow:hidden;border:1px solid #1f2937;">

        <!-- Header -->
        <tr>
          <td style="background:#0f172a;padding:28px 32px;
                     border-bottom:1px solid #1f2937;">
            <span style="font-size:20px;font-weight:700;color:#fff;
                          letter-spacing:-.02em;">
              Churn<span style="color:#6366f1;">Insight</span>
            </span>
          </td>
        </tr>

        <!-- Body -->
        <tr><td style="padding:32px 32px 0;">
          <table width="100%" cellpadding="0" cellspacing="0">

            <!-- Greeting -->
            <tr><td style="padding-bottom:24px;">
              <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;
                          color:#f9fafb;line-height:1.3;">
                Your weekly churn report
              </h1>
              <p style="margin:0;font-size:14px;color:#9ca3af;">
                Here's what your churned customers are telling you.
              </p>
            </td></tr>

            <!-- Summary stats -->
            <tr><td style="padding-bottom:8px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td width="50%" style="padding-right:8px;">
                    <div style="background:#1f2937;border-radius:8px;padding:16px;">
                      <p style="margin:0 0 4px;font-size:28px;font-weight:700;
                                 color:#6366f1;">{new_responses}</p>
                      <p style="margin:0;font-size:13px;color:#9ca3af;">
                        new responses
                      </p>
                    </div>
                  </td>
                  <td width="50%" style="padding-left:8px;">
                    <div style="background:#1f2937;border-radius:8px;padding:16px;">
                      <p style="margin:0 0 4px;font-size:28px;font-weight:700;
                                 color:#6366f1;">{len(themes)}</p>
                      <p style="margin:0;font-size:13px;color:#9ca3af;">
                        active themes
                      </p>
                    </div>
                  </td>
                </tr>
              </table>
            </td></tr>

            {new_themes_html}
            {themes_table}
            {headline_html}

            <!-- CTA -->
            <tr><td style="padding:32px 0;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:#6366f1;border-radius:8px;">
                    <a href="{dashboard_url}"
                       style="display:inline-block;padding:12px 24px;
                              font-size:14px;font-weight:600;color:#fff;
                              text-decoration:none;">
                      View your dashboard &rarr;
                    </a>
                  </td>
                </tr>
              </table>
            </td></tr>

          </table>
        </td></tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 32px;border-top:1px solid #1f2937;
                     background:#0f172a;">
            <p style="margin:0;font-size:12px;color:#4b5563;line-height:1.5;">
              You're receiving this because you have an active Churn Insight account.
              Total responses in your account: {total_responses}.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_weekly_digest(to_email: str, account_id: str, stats: dict) -> None:
    """Send the weekly digest email via Resend.

    Logs a warning and returns without raising if RESEND_API_KEY is not set,
    so the scheduler never crashes over a missing email key.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — skipping digest email for %s", to_email)
        return

    new_responses: int = stats.get("new_responses", 0)
    subject = f"Your churn insights this week — {new_responses} new responses"

    resend.api_key = settings.RESEND_API_KEY
    params: resend.Emails.SendParams = {
        "from": _FROM,
        "to": [to_email],
        "subject": subject,
        "html": _build_html(account_id, stats),
    }
    try:
        result = resend.Emails.send(params)
        logger.info("Digest email sent to %s (id=%s)", to_email, result.get("id"))
    except ResendError as exc:
        logger.warning("Resend API error for %s — %s (add a valid RESEND_API_KEY to send real email)", to_email, exc)
