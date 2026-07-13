"""
Central configuration for CJ-AI Web.
All tuneable values live here so they can be adjusted without touching business logic.
"""

import os
import sys
import logging
from pathlib import Path

# ── Directory layout ──────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOG_FILE = DATA_DIR / "app.log"

# ── Database ──────────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Path to the seeded Q&A knowledge base (shared with cj-ai CLI)
KNOWLEDGE_FILE = BASE_DIR.parent.parent / "cj-ai" / "knowledge" / "knowledge.json"

# ── Qdrant Cloud ──────────────────────────────────────────────────────────────

QDRANT_URL     = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")

COLLECTION_KNOWLEDGE = "cybersec_knowledge"
COLLECTION_SOURCES   = "cybersec_sources"
COLLECTION_CHAT      = "chat_memory"

# ── Admin ─────────────────────────────────────────────────────────────────────

# Username of the system owner — only this account can access /api/admin/users
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "249shadow")

# ── Authentication ────────────────────────────────────────────────────────────

JWT_SECRET      = os.environ.get("SESSION_SECRET", "")
JWT_ALGORITHM   = "HS256"
JWT_EXPIRE_HOURS = 24 * 30   # tokens stay valid for 30 days

MIN_USERNAME_LEN = 3
MAX_USERNAME_LEN = 32
MIN_PASSWORD_LEN = 8

# ── LLM (Groq) ────────────────────────────────────────────────────────────────

GROQ_API_KEY    = os.environ.get("GROQ_API_KEY", "")
LLM_MODEL       = "llama-3.3-70b-versatile"
VISION_MODEL    = "meta-llama/llama-4-scout-17b-16e-instruct"   # vision-capable model
LLM_MAX_TOKENS  = 1024
LLM_TEMPERATURE = 0.4

# Maximum upload sizes enforced at the API layer (bytes)
MAX_UPLOAD_IMAGE_BYTES = 3 * 1024 * 1024   # 3 MB
MAX_UPLOAD_DOC_BYTES   = 5 * 1024 * 1024   # 5 MB

# ── RAG thresholds (Qdrant cosine distance: 0=identical) ─────────────────────

DIST_HIGH   = 0.55   # high-confidence direct answer
DIST_MED    = 0.90   # partial / related answer
MAX_RESULTS = 6

# ── Learning scheduler ────────────────────────────────────────────────────────

SCRAPER_INTERVAL_HOURS = 6

# ── API safety limits ─────────────────────────────────────────────────────────

MAX_MESSAGE_LEN        = 2_000   # characters per user message
MAX_USER_ID_LEN        = 64      # characters for the browser-generated user UUID
MAX_SESSION_TITLE_LEN  = 45      # characters for auto-generated session titles

# Rate limiting: at most RATE_LIMIT_REQUESTS per RATE_LIMIT_WINDOW_SECONDS
RATE_LIMIT_REQUESTS        = 20
RATE_LIMIT_WINDOW_SECONDS  = 60

# ── Default RSS feeds ─────────────────────────────────────────────────────────

DEFAULT_FEEDS = [
    {"name": "The Hacker News",   "url": "https://feeds.feedburner.com/TheHackersNews",                  "enabled": True},
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/",                            "enabled": True},
    {"name": "SANS ISC Diary",    "url": "https://isc.sans.edu/rssfeed_full.xml",                        "enabled": True},
    {"name": "SecurityWeek",      "url": "https://feeds.feedburner.com/securityweek",                    "enabled": True},
    {"name": "NVD CVE (recent)",  "url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss-analyzed.xml","enabled": True},
    {"name": "BleepingComputer",  "url": "https://www.bleepingcomputer.com/feed/",                       "enabled": True},
]

# ── Cybersecurity scope keywords ──────────────────────────────────────────────

CYBERSECURITY_KEYWORDS = [
    "cybersecurity","cyber security","information security","infosec",
    "hacking","hack","penetration","pentest","red team","blue team",
    "linux","bash","shell","terminal","kali","parrot",
    "networking","network","firewall","vpn","tcp","udp","ip address",
    "nmap","wireshark","metasploit","burp","sqlmap","gobuster",
    "owasp","web security","xss","sql injection","csrf","ssrf","lfi",
    "malware","virus","trojan","ransomware","worm","rootkit","spyware",
    "forensics","digital forensics","memory forensics","volatility",
    "cryptography","encryption","decryption","hash","ssl","tls","aes","rsa",
    "soc","security operations","incident response","threat hunting","siem",
    "iam","identity","active directory","ldap","authentication","mfa","oauth",
    "ids","ips","intrusion detection","snort","suricata",
    "ctf","capture the flag","reverse engineering","pwn","binary",
    "python security","scapy","pwntools",
    "windows security","privilege escalation","privesc",
    "vulnerability","cve","patch","zero day","0day",
    "secure coding","devsecops","sast","dast",
    "social engineering","phishing","password","brute force",
    "port scan","reconnaissance","osint","footprinting",
    "dns","http","https","ftp","ssh","rdp","smb","telnet",
    "buffer overflow","heap","shellcode","rop",
    "cloud security","aws","azure","gcp",
    "steganography","wireless","wifi","wpa","wep",
    "honeypot","threat intelligence","mitre","att&ck",
    "أمن","اختراق","شبكات","تشفير","حماية","هكر","فايروس","برمجيات خبيثة",
]


# ── Startup validation ────────────────────────────────────────────────────────

def validate_required_env() -> None:
    """
    Verify that every required environment variable is set.
    Logs a clear error and exits early rather than failing deep inside a request handler.
    """
    missing = []
    if not DATABASE_URL:
        missing.append("DATABASE_URL")
    if not QDRANT_URL:
        missing.append("QDRANT_URL")
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not JWT_SECRET:
        missing.append("SESSION_SECRET")

    if missing:
        logging.getLogger("cj_web").error(
            "Missing required environment variables: %s. "
            "Set them in Replit Secrets and restart.",
            ", ".join(missing),
        )
        sys.exit(1)
