import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma"
DB_FILE = DATA_DIR / "cj_web.db"
KNOWLEDGE_FILE = BASE_DIR.parent.parent / "cj-ai" / "knowledge" / "knowledge.json"
LOG_FILE = DATA_DIR / "app.log"

# Qdrant Cloud
QDRANT_URL     = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")

# Vector collections (shared names used by both ChromaDB legacy and Qdrant)
COLLECTION_KNOWLEDGE = "cybersec_knowledge"
COLLECTION_SOURCES   = "cybersec_sources"
COLLECTION_CHAT      = "chat_memory"

# LLM (Groq)
LLM_MODEL        = "llama-3.3-70b-versatile"
LLM_MAX_TOKENS   = 1024
LLM_TEMPERATURE  = 0.4
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")

# Similarity thresholds (ChromaDB cosine distance: 0=identical, 2=opposite)
DIST_HIGH  = 0.55   # confident direct answer
DIST_MED   = 0.90   # partial / related answer
MAX_RESULTS = 6

# Learning scheduler
SCRAPER_INTERVAL_HOURS = 6

# Default RSS feeds (cybersecurity)
DEFAULT_FEEDS = [
    {"name": "The Hacker News",       "url": "https://feeds.feedburner.com/TheHackersNews",       "enabled": True},
    {"name": "Krebs on Security",     "url": "https://krebsonsecurity.com/feed/",                  "enabled": True},
    {"name": "SANS ISC Diary",        "url": "https://isc.sans.edu/rssfeed_full.xml",              "enabled": True},
    {"name": "SecurityWeek",          "url": "https://feeds.feedburner.com/securityweek",          "enabled": True},
    {"name": "NVD CVE (recent)",      "url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss-analyzed.xml", "enabled": True},
    {"name": "BleepingComputer",      "url": "https://www.bleepingcomputer.com/feed/",             "enabled": True},
]

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
