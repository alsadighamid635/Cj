from config import CYBERSECURITY_KEYWORDS
from utils.text import normalize

OUT_OF_SCOPE_REPLY_EN = (
    "I specialize exclusively in cybersecurity and information security. "
    "I'm not able to answer questions outside that domain.\n"
    "Please ask me about topics like: Linux, networking, hacking, "
    "cryptography, malware analysis, CTF, OWASP, penetration testing, and more."
)

OUT_OF_SCOPE_REPLY_AR = (
    "أنا متخصص فقط في الأمن السيبراني وأمن المعلومات، "
    "لذلك لا أجيب عن الأسئلة خارج هذا المجال.\n"
    "يمكنك سؤالي عن: Linux، الشبكات، الاختراق الأخلاقي، التشفير، "
    "تحليل البرمجيات الخبيثة، CTF، OWASP، اختبار الاختراق، وغيرها."
)


def is_cybersecurity_related(text: str) -> bool:
    normalized = normalize(text)
    for keyword in CYBERSECURITY_KEYWORDS:
        if keyword in normalized:
            return True
    return False


def out_of_scope_reply(text: str) -> str:
    arabic_chars = sum(1 for ch in text if "\u0600" <= ch <= "\u06ff")
    if arabic_chars > len(text) * 0.25:
        return OUT_OF_SCOPE_REPLY_AR
    return OUT_OF_SCOPE_REPLY_EN
