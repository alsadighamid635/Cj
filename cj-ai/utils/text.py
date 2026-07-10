import re
import unicodedata


# Commands that often appear in cybersecurity questions
SHELL_COMMAND_PATTERNS = re.compile(
    r"\b(nmap|netstat|ss|ifconfig|ip|ping|traceroute|dig|nslookup|"
    r"whois|curl|wget|nc|netcat|tcpdump|wireshark|tshark|"
    r"hashcat|john|hydra|medusa|aircrack-ng|airodump-ng|"
    r"metasploit|msfconsole|msfvenom|searchsploit|"
    r"sqlmap|nikto|gobuster|dirb|dirbuster|feroxbuster|"
    r"burpsuite|zaproxy|"
    r"gpg|openssl|ssh|ssh-keygen|scp|rsync|"
    r"chmod|chown|chroot|sudo|su|useradd|passwd|"
    r"ps|top|htop|kill|pkill|lsof|strace|ltrace|"
    r"file|strings|xxd|hexdump|objdump|nm|readelf|"
    r"gdb|pwndbg|peda|radare2|r2|ghidra|ida|"
    r"iptables|ufw|nftables|fail2ban|"
    r"volatility|autopsy|binwalk|foremost|"
    r"git|python|pip|virtualenv|"
    r"find|grep|awk|sed|cut|sort|uniq|wc|cat|less|tail|head|"
    r"tar|zip|unzip|gzip|base64|"
    r"crontab|systemctl|service|journalctl)\b",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    """Lowercase, strip diacritics, collapse whitespace."""
    text = text.lower().strip()
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
    text = re.sub(r"\s+", " ", text)
    return text


def extract_command_name(text: str) -> str | None:
    """Return the first known shell command found in the text, or None."""
    match = SHELL_COMMAND_PATTERNS.search(text)
    if match:
        return match.group(0).lower()
    return None


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]
