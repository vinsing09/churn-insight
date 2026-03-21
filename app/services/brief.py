"""Claude Sonnet brief generation — placeholder.

Takes a theme and associated classifications and generates
an ad creative brief with angle, gap, headline hypothesis,
and test recommendation.
"""


async def generate_brief(
    theme_name: str,
    theme_description: str,
    sample_responses: list[str],
    ad_copy: str | None,
) -> dict:
    """Call Claude Sonnet to generate an ad creative brief.

    Returns a dict matching the Brief model fields.
    """
    raise NotImplementedError
