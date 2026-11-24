"""Auto-tagging for shiur titles: rabbi name, topic, and cleaned title.

Used both by ingest.py (live YouTube feeds) and build_seed.py (seed data).
Rules are keyword based on purpose: cheap, transparent, easy to fix.
Later this can be swapped for an LLM classifier on title + description.
"""
import re

TOPICS = [
    ("גמרא", ["מסכת", "גמרא", "דף היומי", "הדף היומי", "שיעור כללי", "סוגיה", "זבחים", "בבא ", "ערכין", "בכורות", "יומא", "דף ", "קצות החושן", "עיתים לתורה", "סנהדרין", "סוגיית"]),
    ("הלכה", ["הלכה", "הלכות", "משנה ברורה", "שולחן ערוך", "אורח חיים", "בורר", "דיני", "דין ", "עיוני הלכה", "ערלה", "בשר לחלב", "ממתינים"]),
    ("פרשת השבוע", ["פרשת", "פרשה", "בפרשה", "לפרשת", "חידוש מהגוש", "משיכות חכמה"]),
    ('תנ"ך', ['תנ"ך', "נביאים", "שמואל", "יהושע", "שופטים", "מלכים", "ישעיהו", "תהלים", "תהילים", "ספר "]),
    ("חסידות וקבלה", ["זוהר", "חסידות", "ליקוטי מוהר", "צדקת הצדיק", "פנימיות התורה", "קבלה", "שפת אמת"]),
    ("מוסר", ["מוסר", "מסילת ישרים", "המידות", "מכתב מאליהו", "יראת", "יראה", "פרקי אבות", "מידות"]),
    ("מועדים", ["פורים", "חנוכה", "פסח", "סוכות", "שבועות", "ראש השנה", "יום כיפור", "יום הכפורים", "סליחות", "יום העצמאות", "יום ירושלים", "תשעה באב", "אלול", "יוה\"כ", "לג' בעומר"]),
    ("אמונה ומחשבה", ["אורות", "אמונה", "מהר\"ל", "מהר״ל", "נצח ישראל", "נתיבות", "תפארת ישראל", "כוזרי", "עין איה", "הרב קוק", "הרצי\"ה", "גאולה", "אחדות", "הכנה אמונית"]),
]

RABBI_RE = re.compile(r'(?:מו"ר\s+)?(?:רה"י\s+|רה\'\'י\s+|רה״י\s+)?(הרב|פרופ\'|ד"ר)\s+([^\s|,\-–()#]+(?:\s+[^\s|,\-–()#]+){0,2})')
STOP = {"שיעור", "לפרשת", "בפרשת", "פרשת", "והרב", "שליט\"א", "ישיבת", "זצ\"ל"}


def clean_title(t):
    t = re.sub(r"#(?!\d)\S+", "", t)              # hashtags (keep "#5" lesson numbers)
    t = re.sub(r"\s+I\s+", " | ", t)              # "I" used as a separator
    t = re.sub(r"\s*\|\|\s*", " | ", t)
    t = re.sub(r"\s*\|\s*ישיבת [^|]+$", "", t)     # trailing "| ישיבת X"
    t = re.sub(r"\s*\|\s*$", "", t)
    return re.sub(r"\s{2,}", " ", t).strip(" |")


def find_rabbi(t):
    m = RABBI_RE.search(t)
    if not m:
        return ""
    words = [w for w in m.group(2).split() if w not in STOP]
    # stop the name where the title moves on to the topic
    name = []
    for w in words:
        if w.startswith(("ו", "ל", "ב")) and len(name) >= 2:
            break
        name.append(w.strip('׳"\''))
        if len(name) >= 2 and name[-1] not in ("בן", "בר"):
            break
    if not name:
        return ""
    prefix = "פרופ'" if m.group(1).startswith("פרופ") else "הרב"
    return f"{prefix} {' '.join(name)}"


def find_topic(t):
    for topic, keys in TOPICS:
        if any(k in t for k in keys):
            return topic
    return "אמונה ומחשבה"


def tag(title):
    t = clean_title(title)
    return {"t": t, "r": find_rabbi(t), "c": find_topic(t)}


def to_minutes(d):
    parts = [int(p) for p in d.split(":")]
    secs = 0
    for p in parts:
        secs = secs * 60 + p
    return max(1, round(secs / 60))
