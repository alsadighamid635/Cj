from pathlib import Path

BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DATABASE_DIR = BASE_DIR / "database"

KNOWLEDGE_FILE = KNOWLEDGE_DIR / "knowledge.json"
TRAINING_FILE = KNOWLEDGE_DIR / "training_data.json"
DB_FILE = DATABASE_DIR / "chat_history.db"
LOG_FILE = BASE_DIR / "cj_ai.log"

APP_NAME = "CJ-AI"
APP_SUBTITLE = "Cybersecurity AI Assistant"
APP_VERSION = "1.0"

MATCH_THRESHOLD = 62  # minimum RapidFuzz score to accept a match
MAX_HISTORY = 30      # messages to keep in session memory

CYBERSECURITY_KEYWORDS = [
    "cybersecurity", "cyber security", "information security", "infosec",
    "hacking", "hack", "penetration", "pentest", "pen test", "red team", "blue team",
    "linux", "bash", "shell", "terminal", "command line", "cli",
    "kali", "kali linux", "parrot", "blackarch",
    "networking", "network", "firewall", "vpn", "tcp", "udp", "ip address",
    "nmap", "wireshark", "metasploit", "burpsuite", "burp suite", "sqlmap",
    "owasp", "web security", "xss", "sql injection", "csrf", "ssrf", "lfi", "rfi",
    "malware", "virus", "trojan", "ransomware", "worm", "rootkit", "spyware",
    "forensics", "digital forensics", "memory forensics",
    "cryptography", "encryption", "decryption", "hash", "ssl", "tls", "certificate",
    "aes", "rsa", "sha", "md5", "base64",
    "soc", "security operations", "incident response", "threat hunting",
    "siem", "splunk", "elastic", "threat intelligence",
    "iam", "identity", "access management", "active directory", "ldap",
    "authentication", "authorization", "mfa", "2fa", "oauth",
    "ids", "ips", "intrusion detection", "intrusion prevention", "snort", "suricata",
    "ctf", "capture the flag", "reverse engineering", "pwn", "binary exploitation",
    "python security", "python exploit", "scapy",
    "windows security", "defender", "privilege escalation", "privesc",
    "vulnerability", "cve", "patch management", "zero day", "0day",
    "secure coding", "code review", "devsecops", "sast", "dast",
    "social engineering", "phishing", "vishing", "smishing", "password",
    "brute force", "dictionary attack", "credential stuffing",
    "port scan", "reconnaissance", "footprinting", "osint",
    "dns", "dhcp", "http", "https", "ftp", "ssh", "rdp", "smb", "telnet",
    "buffer overflow", "heap overflow", "stack overflow", "format string",
    "pki", "gpg", "pgp", "digital signature",
    "mobile security", "android security", "ios security",
    "cloud security", "aws security", "azure security", "gcp security",
    "steganography", "steganalysis",
    "wireless security", "wifi", "wpa", "wep", "wpa2", "wpa3",
    "honeypot", "deception", "canary",
    "exploit", "payload", "shellcode", "rop", "ret2libc",
    "mimikatz", "hashcat", "john the ripper", "hydra", "aircrack",
    "security audit", "compliance", "iso 27001", "nist", "gdpr",
    "hardening", "baseline", "cis benchmark",
    "malware analysis", "sandbox", "dynamic analysis", "static analysis",
    "packet", "sniffing", "arp", "mitm", "man in the middle",
    "tor", "darkweb", "onion",
    "keylogger", "backdoor", "c2", "command and control",
    "antivirus", "edr", "xdr", "endpoint security",
    "threat model", "attack surface", "kill chain", "mitre att&ck",
    "أمن", "اختراق", "شبكات", "تشفير", "حماية", "هكر", "فايروس", "برمجيات خبيثة",
]
