"""
GOLIATH Content Moderation

Safety layer that screens tasks before they reach the AI model.
Blocks requests related to illegal activities, hate speech, harassment,
spam, and other harmful content.

This module is integrated into the Engine and runs automatically on every
task. It uses keyword/pattern matching as a fast first-pass filter.
"""

import re

# Each category maps to a set of patterns. Patterns are compiled with
# word-boundary anchors to avoid false positives on partial matches
# (e.g. "assault" in "assault rifle" but not "asphalt").

_CATEGORIES: dict[str, dict] = {
    "illegal_activity": {
        "description": "Requests for help with illegal activities",
        "patterns": [
            r"how\s+to\s+(?:make|build|create|manufacture)\s+(?:an?\s+)?(?:bomb|explosive|weapon|meth|drugs)",
            r"how\s+to\s+(?:hack|break\s+into|crack)\s+(?:someone'?s?\s+|a\s+|an\s+)(?:account|password|system|network|computer|server|email|phone|wifi)",
            r"how\s+to\s+(?:steal|shoplift|rob|burglarize|pickpocket)",
            r"how\s+to\s+(?:forge|counterfeit)\s+(?:money|documents|ids|passports|currency)",
            r"how\s+to\s+(?:buy|sell|obtain)\s+(?:illegal\s+)?(?:drugs|weapons|firearms)\s+(?:illegally|on\s+(?:the\s+)?(?:dark\s*web|black\s*market))",
            r"how\s+to\s+(?:launder|money\s*launder)",
            r"how\s+to\s+(?:kidnap|abduct|traffic)",
            r"how\s+to\s+(?:make|create|distribute)\s+(?:child\s+)?(?:exploitation|csam|cp)\s+material",
            r"how\s+to\s+(?:evade|escape\s+from|flee\s+from)\s+(?:police|law\s+enforcement|authorities)",
        ],
        "message": "This request appears to involve illegal activity. GOLIATH cannot assist with this.",
    },
    "violence_and_threats": {
        "description": "Threats, incitement to violence, or instructions to harm",
        "patterns": [
            r"how\s+to\s+(?:kill|murder|assassinate|poison)\s+(?:a\s+|my\s+|some)?(?!process|container|docker|pod|service|task|session|connection|thread|dns|cache|server|port|job|screen|tmux|myself)\w+",
            r"how\s+to\s+(?:hurt|harm|injure|torture|maim)\s+(?:a\s+|my\s+|some)?(?!process|container|myself)\w+",
            r"(?:i\s+(?:want|plan|going)\s+to|i'?m\s+going\s+to|help\s+me)\s+(?:kill|murder|attack|hurt|harm)\b",
            r"how\s+to\s+(?:get\s+away\s+with|cover\s+up)\s+(?:murder|killing|assault)",
        ],
        "message": "This request contains violent or threatening content. GOLIATH cannot assist with this.",
    },
    "hate_speech": {
        "description": "Content targeting groups based on protected characteristics",
        "patterns": [
            r"(?:why\s+(?:are|do)\s+)?(?:all\s+)?(?:jews|muslims|blacks|whites|asians|mexicans|immigrants|gays|trans\s+people)\s+(?:are\s+)?(?:inferior|evil|disgusting|subhuman|vermin|parasites|animals)",
            r"(?:write|generate|create)\s+(?:an?\s+)?(?:racist|antisemitic|homophobic|transphobic|xenophobic|sexist)\s+(?:joke|speech|rant|manifesto|post|message)",
            r"\b(?:racial|ethnic)\s+(?:cleansing|purification|extermination)\b",
            r"\b(?:white|black|jewish|muslim|christian)\s+(?:supremacy|genocide)\b",
        ],
        "message": "This request contains hate speech targeting a protected group. GOLIATH cannot assist with this.",
    },
    "harassment": {
        "description": "Targeted harassment, stalking, or doxxing",
        "patterns": [
            r"how\s+to\s+(?:stalk|dox|doxx|swat)\s+(?:a\s+|some)?\w+",
            r"how\s+to\s+(?:find|track|locate)\s+(?:someone'?s?|a\s+person'?s?)\s+(?:home\s+)?(?:address|location|phone|workplace)",
            r"(?:write|generate|create)\s+(?:an?\s+)?(?:harassment|threatening|intimidating|bullying)\s+(?:message|email|letter|post)",
            r"how\s+to\s+(?:blackmail|extort|threaten)\s+(?:someone|a\s+person)",
        ],
        "message": "This request involves harassment or stalking. GOLIATH cannot assist with this.",
    },
    "self_harm": {
        "description": "Content promoting self-harm or suicide",
        "patterns": [
            r"how\s+to\s+(?:commit\s+suicide|kill\s+myself|end\s+my\s+life)",
            r"(?:best|easiest|painless|quickest)\s+(?:way|method)\s+to\s+(?:die|kill\s+myself|commit\s+suicide|end\s+(?:my\s+)?life)",
            r"how\s+to\s+(?:cut|harm)\s+myself",
        ],
        "message": (
            "If you or someone you know is in crisis, please reach out for help:\n"
            "  - National Suicide Prevention Lifeline: 988 (call or text)\n"
            "  - Crisis Text Line: text HOME to 741741\n"
            "  - International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/\n"
            "GOLIATH cannot assist with self-harm content."
        ),
    },
    "sexual_exploitation": {
        "description": "Sexual content involving minors or non-consensual",
        "patterns": [
            r"(?:child|minor|underage|teen(?:age)?)\s+(?:porn|sex|nude|naked|exploitation|abuse)",
            r"(?:generate|write|create)\s+(?:sexual|explicit|erotic)\s+(?:content|story|image)\s+(?:involving|about|with)\s+(?:a\s+)?(?:child|minor|kid|underage)",
            r"how\s+to\s+(?:groom|lure|seduce)\s+(?:a\s+)?(?:child|minor|kid|teen)",
        ],
        "message": "This request involves the sexual exploitation of minors. GOLIATH absolutely cannot assist with this. This content may be reported.",
    },
    "spam_and_fraud": {
        "description": "Spam, phishing, scams, and fraud",
        "patterns": [
            r"(?:write|generate|create)\s+(?:a\s+)?(?:phishing|scam)\s+(?:email|page|site|message|sms|text)",
            r"how\s+to\s+(?:create|set\s+up|run)\s+(?:a\s+)?(?:ponzi|pyramid)\s+scheme",
            r"how\s+to\s+(?:impersonate|pretend\s+to\s+be)\s+(?:a\s+|the\s+|an\s+)?(?:bank|government|police|irs|fbi|official|company|authority)",
            r"(?:write|generate|create)\s+(?:a\s+)?(?:fake|fraudulent)\s+(?:review|testimonial|identity|document|invoice|receipt)",
        ],
        "message": "This request involves spam, phishing, or fraud. GOLIATH cannot assist with this.",
    },
}

# Pre-compile all patterns for performance.
# Order matters: more specific categories (self_harm) are checked before
# broader ones (violence_and_threats) to avoid misclassification.
_CHECK_ORDER = [
    "self_harm",
    "sexual_exploitation",
    "illegal_activity",
    "violence_and_threats",
    "hate_speech",
    "harassment",
    "spam_and_fraud",
]

# Technical contexts that use violent verbs ("kill a process", "poison a
# DNS cache") must be allowed through. These are checked BEFORE the harmful
# patterns. The lazy quantifier (?:\w+\s+)*? scans past adjectives to find
# the technical noun.
_TECH_NOUNS = (
    r"process|processes|container|containers|docker|pod|pods|service|services|"
    r"task|tasks|session|sessions|connection|connections|thread|threads|"
    r"dns|cache|server|servers|port|ports|job|jobs|screen|tmux|daemon|daemons|"
    r"instance|instances|vm|vms|build|builds|app|apps|program|programs|"
    r"script|scripts|command|commands|window|windows|node|nodes|query|queries|"
    r"request|requests|signal|socket|pipe|queue|cron|zombie|orphan|tab|channel"
)
_SAFE_TECH = re.compile(
    rf"how\s+to\s+(?:kill|stop|terminate|end|close|destroy|remove|drop|poison)"
    rf"\s+(?:\w+\s+)*?(?:{_TECH_NOUNS})\b",
    re.IGNORECASE,
)

_COMPILED: list[tuple[str, re.Pattern, str]] = []
for category in _CHECK_ORDER:
    info = _CATEGORIES[category]
    for pattern in info["patterns"]:
        _COMPILED.append(
            (
                category,
                re.compile(pattern, re.IGNORECASE),
                info["message"],
            )
        )


class ModerationError(Exception):
    """Raised when a task is blocked by the content moderation layer."""

    def __init__(self, message: str, category: str):
        super().__init__(message)
        self.category = category


def check(task: str) -> None:
    """Screen a task for harmful content.

    Args:
        task: The user's input text.

    Raises:
        ModerationError: If the task matches a blocked content category.
    """
    # Allow known-safe technical contexts (e.g. "kill a process")
    if _SAFE_TECH.search(task):
        return

    for category, pattern, message in _COMPILED:
        if pattern.search(task):
            raise ModerationError(message, category)
