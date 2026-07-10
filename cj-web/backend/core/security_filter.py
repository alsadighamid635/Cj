"""
Scope guard for CJ-AI.

Checks whether a user question is cybersecurity-related using a keyword list.
Out-of-scope questions receive a polite decline in the user's language.
"""

from config import CYBERSECURITY_KEYWORDS
from utils.text import normalize

OUT_OF_SCOPE_EN = (
    "I specialize exclusively in **cybersecurity and information security**. "
    "I can't answer questions outside that domain.\n\n"
    "Try asking about: Linux, networking, penetration testing, cryptography, "
    "malware analysis, CTF, OWASP, Kali Linux, Nmap, Wireshark, and more."
)

OUT_OF_SCOPE_AR = (
    "أنا متخصص فقط في **الأمن السيبراني وأمن المعلومات**، "
    "لذلك لا أجيب عن الأسئلة خارج هذا المجال.\n\n"
    "اسألني عن: Linux، الشبكات، اختبار الاختراق، التشفير، "
    "تحليل البرمجيات الخبيثة، CTF، OWASP، Kali Linux، Nmap، وغيرها."
)


def is_cybersecurity_related(text: str) -> bool:
    norm = normalize(text)
    return any(kw in norm for kw in CYBERSECURITY_KEYWORDS)


def out_of_scope_reply(text: str) -> str:
    arabic = sum(1 for ch in text if "\u0600" <= ch <= "\u06ff")
    if arabic > len(text) * 0.25:
        return OUT_OF_SCOPE_AR
    return OUT_OF_SCOPE_EN
