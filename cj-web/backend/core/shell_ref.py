"""
Detects shell/security tool questions and returns structured markdown help.
"""

import re

_COMMAND_PATTERNS = re.compile(
    r"\b(nmap|netstat|ss|wireshark|tshark|tcpdump|hashcat|john|hydra|"
    r"gobuster|dirb|sqlmap|nikto|metasploit|msfconsole|msfvenom|"
    r"openssl|ssh|gpg|iptables|ufw|aircrack-ng|volatility|"
    r"grep|find|tcpdump|strace|ltrace|gdb|strings|binwalk|"
    r"curl|wget|nc|netcat|nslookup|dig|whois)\b",
    re.IGNORECASE,
)

_REF: dict[str, dict] = {
    "nmap": {
        "desc": "Network Mapper — free, open-source tool for network discovery and security auditing.",
        "usage": "nmap [options] <target>",
        "options": [
            "-sS    SYN (stealth) scan",
            "-sV    Service/version detection",
            "-sU    UDP scan",
            "-O     OS detection",
            "-A     Aggressive (OS + version + scripts + traceroute)",
            "-p-    All 65535 ports",
            "-p <ports>  Specific ports: -p 22,80,443",
            "--script <name>  NSE scripts (e.g. --script vuln)",
            "-T4    Speed template (0=slow … 5=insane)",
            "--open Show only open ports",
            "-oN <file>  Save normal output",
        ],
        "examples": [
            ("Basic host scan", "nmap 192.168.1.1"),
            ("Service + version", "nmap -sV 192.168.1.1"),
            ("Aggressive full scan", "nmap -A -T4 192.168.1.1"),
            ("All ports", "nmap -p- -T4 192.168.1.1"),
            ("Subnet discovery", "nmap -sn 192.168.1.0/24"),
            ("Vulnerability scripts", "nmap --script vuln 192.168.1.1"),
        ],
    },
    "hashcat": {
        "desc": "The world's fastest and most advanced password recovery tool.",
        "usage": "hashcat [options] <hashfile> <wordlist|mask>",
        "options": [
            "-m <type>  Hash type: 0=MD5, 100=SHA1, 1000=NTLM, 1800=sha512crypt",
            "-a <mode>  Attack: 0=dict, 3=brute, 6=hybrid",
            "-o <file>  Save cracked passwords",
            "--show     Show already-cracked hashes",
            "-r <rule>  Apply rule file",
        ],
        "examples": [
            ("MD5 dictionary", "hashcat -m 0 hashes.txt rockyou.txt"),
            ("NTLM with rules", "hashcat -m 1000 hashes.txt rockyou.txt -r best64.rule"),
            ("SHA1 brute-force (6 chars)", "hashcat -m 100 -a 3 hash.txt ?a?a?a?a?a?a"),
            ("Show cracked", "hashcat -m 0 hashes.txt --show"),
        ],
    },
    "hydra": {
        "desc": "Fast, flexible online password cracking / brute-force tool.",
        "usage": "hydra [options] <target> <service>",
        "options": [
            "-l <user>   Single username",
            "-L <file>   Username list",
            "-p <pass>   Single password",
            "-P <file>   Password list",
            "-t <n>      Parallel threads (default 16)",
            "-V          Verbose — show each attempt",
            "-f          Stop after first success",
        ],
        "examples": [
            ("SSH brute force", "hydra -l root -P rockyou.txt ssh://192.168.1.1"),
            ("HTTP POST form", "hydra -l admin -P rockyou.txt 192.168.1.1 http-post-form '/login:user=^USER^&pass=^PASS^:Invalid'"),
            ("FTP", "hydra -L users.txt -P passwords.txt ftp://192.168.1.1"),
            ("RDP", "hydra -l administrator -P rockyou.txt rdp://192.168.1.1"),
        ],
    },
    "sqlmap": {
        "desc": "Automated SQL injection detection and exploitation tool.",
        "usage": "sqlmap -u <url> [options]",
        "options": [
            "-u <url>    Target URL",
            "--dbs       Enumerate databases",
            "-D <db>     Select database",
            "--tables    Enumerate tables",
            "-T <table>  Select table",
            "--dump      Dump table data",
            "--forms     Auto-detect forms",
            "--batch     Non-interactive mode",
        ],
        "examples": [
            ("Basic test", "sqlmap -u 'http://target.com/page?id=1' --batch"),
            ("List databases", "sqlmap -u 'http://target.com/page?id=1' --dbs"),
            ("Dump table", "sqlmap -u 'http://target.com/page?id=1' -D mydb -T users --dump"),
        ],
    },
    "openssl": {
        "desc": "Toolkit for TLS/SSL and general cryptography.",
        "usage": "openssl <command> [options]",
        "options": [
            "dgst -sha256 <file>   SHA-256 hash",
            "enc -aes-256-cbc      Symmetric encryption",
            "genrsa -out key 2048  Generate RSA key",
            "req -x509 ...         Self-signed certificate",
            "s_client -connect     Inspect remote TLS certificate",
        ],
        "examples": [
            ("SHA-256 hash of file", "openssl dgst -sha256 file.txt"),
            ("Encrypt with AES-256", "openssl enc -aes-256-cbc -in plain.txt -out enc.bin"),
            ("Decrypt", "openssl enc -d -aes-256-cbc -in enc.bin -out plain.txt"),
            ("Check site TLS cert", "openssl s_client -connect example.com:443"),
            ("Generate RSA key", "openssl genrsa -out private.key 2048"),
        ],
    },
    "gobuster": {
        "desc": "Brute-force URIs, DNS subdomains, and virtual hostnames.",
        "usage": "gobuster <mode> [options]",
        "options": [
            "dir        Directory/file brute force",
            "dns        DNS subdomain enumeration",
            "-u <url>   Target URL",
            "-w <file>  Wordlist",
            "-x <ext>   Extensions: php,html,txt",
            "-t <n>     Threads",
        ],
        "examples": [
            ("Dir brute force", "gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt"),
            ("With extensions", "gobuster dir -u http://target.com -w common.txt -x php,html"),
            ("DNS enum", "gobuster dns -d target.com -w subdomains.txt"),
        ],
    },
    "ssh": {
        "desc": "Secure Shell — encrypted remote login and tunneling.",
        "usage": "ssh [options] user@host",
        "options": [
            "-p <port>   Custom port",
            "-i <key>    Private key file",
            "-L <local:host:remote>  Local port forwarding",
            "-R <remote:host:local>  Remote port forwarding",
            "-D <port>   Dynamic SOCKS5 proxy",
            "-N          No remote commands (for tunnels)",
        ],
        "examples": [
            ("Connect", "ssh user@192.168.1.1"),
            ("Custom port", "ssh -p 2222 user@192.168.1.1"),
            ("With key", "ssh -i ~/.ssh/id_rsa user@192.168.1.1"),
            ("Local forwarding", "ssh -L 8080:localhost:80 user@192.168.1.1"),
            ("SOCKS5 proxy", "ssh -D 1080 -N user@192.168.1.1"),
        ],
    },
    "volatility": {
        "desc": "The industry-standard memory forensics framework.",
        "usage": "volatility -f <dump.mem> --profile=<Profile> <plugin>",
        "options": [
            "imageinfo   Detect memory profile",
            "pslist      List running processes",
            "pstree      Process tree",
            "netscan     Network connections",
            "dlllist     Loaded DLLs",
            "hashdump    Extract NTLM hashes",
            "malfind     Find injected code",
            "cmdline     Process command lines",
        ],
        "examples": [
            ("Detect profile", "volatility -f memory.dmp imageinfo"),
            ("List processes", "volatility -f memory.dmp --profile=Win7SP1x64 pslist"),
            ("Find malware", "volatility -f memory.dmp --profile=Win7SP1x64 malfind"),
            ("Extract hashes", "volatility -f memory.dmp --profile=Win7SP1x64 hashdump"),
        ],
    },
    "tcpdump": {
        "desc": "Command-line packet analyzer — capture and analyze network traffic.",
        "usage": "tcpdump [options] [expression]",
        "options": [
            "-i <iface>  Network interface",
            "-w <file>   Save to pcap",
            "-r <file>   Read pcap",
            "-n          No hostname resolution",
            "-X          Show hex + ASCII",
            "port <n>    Filter by port",
            "host <ip>   Filter by host",
        ],
        "examples": [
            ("Capture on eth0", "tcpdump -i eth0"),
            ("HTTP only", "tcpdump -i eth0 port 80"),
            ("Save to file", "tcpdump -i eth0 -w traffic.pcap"),
            ("Read pcap", "tcpdump -r traffic.pcap"),
        ],
    },
    "iptables": {
        "desc": "Linux firewall — filter and manipulate network packets.",
        "usage": "iptables [-t table] <command> [chain] [match] [-j target]",
        "options": [
            "-A  Append rule",
            "-I  Insert rule",
            "-D  Delete rule",
            "-L  List rules",
            "-F  Flush chain",
            "-j  Target: ACCEPT, DROP, REJECT, LOG",
            "--dport  Destination port",
        ],
        "examples": [
            ("Block Telnet (port 23)", "iptables -A INPUT -p tcp --dport 23 -j DROP"),
            ("Allow SSH from one IP", "iptables -A INPUT -p tcp -s 10.0.0.5 --dport 22 -j ACCEPT"),
            ("List all rules", "iptables -L -v -n"),
            ("Block outbound to IP", "iptables -A OUTPUT -d 192.168.1.100 -j DROP"),
        ],
    },
}


def get_response(text: str) -> str | None:
    m = _COMMAND_PATTERNS.search(text)
    if not m:
        return None
    cmd = m.group(0).lower()
    ref = _REF.get(cmd)
    if not ref:
        return None

    lines = [f"## `{cmd}`", f"\n{ref['desc']}\n",
             f"**Usage:** `{ref['usage']}`\n", "**Key Options:**"]
    for opt in ref["options"]:
        lines.append(f"  - `{opt}`")
    lines.append("\n**Examples:**")
    for label, example in ref["examples"]:
        lines.append(f"\n*{label}*")
        lines.append(f"```bash\n{example}\n```")
    return "\n".join(lines)
