"""
Formats responses for shell/Linux command questions.
Provides structured output: description, usage, options, examples,
and a copyable command block.
"""

from utils.text import extract_command_name

# Command reference database — description, usage, key options, examples
COMMAND_REFERENCE: dict[str, dict] = {
    "nmap": {
        "description": "Nmap (Network Mapper) is a free, open-source tool for network discovery and security auditing.",
        "usage": "nmap [options] <target>",
        "options": [
            "-sS    : SYN (stealth) scan — the most popular scan type",
            "-sV    : Probe open ports to determine service and version info",
            "-sU    : UDP scan",
            "-O     : Enable OS detection",
            "-A     : Aggressive scan (OS, version, scripts, traceroute)",
            "-p     : Specify port(s), e.g. -p 22,80,443 or -p 1-1000",
            "-p-    : Scan all 65535 ports",
            "--script : Run NSE scripts, e.g. --script vuln",
            "-oN    : Save output in normal format",
            "-oX    : Save output in XML format",
            "-T4    : Set timing template (0=paranoid, 5=insane)",
            "--open : Show only open ports",
        ],
        "examples": [
            ("Scan a single host (common ports)", "nmap 192.168.1.1"),
            ("Detect services and versions", "nmap -sV 192.168.1.1"),
            ("Full aggressive scan", "nmap -A -T4 192.168.1.1"),
            ("Scan entire subnet", "nmap 192.168.1.0/24"),
            ("Scan all ports", "nmap -p- 192.168.1.1"),
            ("Run vulnerability scripts", "nmap --script vuln 192.168.1.1"),
            ("UDP scan top ports", "nmap -sU --top-ports 100 192.168.1.1"),
            ("OS detection", "nmap -O 192.168.1.1"),
        ],
    },
    "netstat": {
        "description": "Display network connections, routing tables, and interface statistics.",
        "usage": "netstat [options]",
        "options": [
            "-a  : Show all connections and listening ports",
            "-t  : Show TCP connections",
            "-u  : Show UDP connections",
            "-n  : Show numeric addresses (no DNS resolution)",
            "-l  : Show only listening sockets",
            "-p  : Show the PID and program name",
            "-r  : Show routing table",
        ],
        "examples": [
            ("All active TCP connections with process names", "netstat -tnp"),
            ("All listening ports", "netstat -lnp"),
            ("Show routing table", "netstat -r"),
            ("All UDP connections", "netstat -unp"),
        ],
    },
    "ss": {
        "description": "A faster modern replacement for netstat — display socket statistics.",
        "usage": "ss [options]",
        "options": [
            "-t  : TCP sockets",
            "-u  : UDP sockets",
            "-l  : Listening sockets",
            "-n  : Numeric (don't resolve hostnames)",
            "-p  : Show process using the socket",
            "-a  : All sockets",
        ],
        "examples": [
            ("All listening TCP sockets with processes", "ss -tlnp"),
            ("All established connections", "ss -t state established"),
            ("Find which process is using port 80", "ss -tlnp | grep ':80'"),
        ],
    },
    "wireshark": {
        "description": "Wireshark is a graphical network protocol analyzer. tshark is its CLI version.",
        "usage": "wireshark   |   tshark [options]",
        "options": [
            "-i <iface> : Capture on a specific interface",
            "-r <file>  : Read from a pcap file",
            "-w <file>  : Write capture to file",
            "-f <filter>: Capture filter (BPF syntax)",
            "-Y <filter>: Display filter (Wireshark syntax)",
            "-T fields  : Print specific fields",
            "-e <field> : Field to print with -T fields",
        ],
        "examples": [
            ("Capture on eth0 and save to file", "tshark -i eth0 -w capture.pcap"),
            ("Read a pcap and filter HTTP", "tshark -r capture.pcap -Y 'http'"),
            ("Capture only port 443", "tshark -i eth0 -f 'port 443'"),
            ("Show src/dst IP of each packet", "tshark -r capture.pcap -T fields -e ip.src -e ip.dst"),
        ],
    },
    "hashcat": {
        "description": "Hashcat is the world's fastest and most advanced password recovery tool.",
        "usage": "hashcat [options] <hashfile> <wordlist|mask>",
        "options": [
            "-m <type>  : Hash type (e.g. 0=MD5, 100=SHA1, 1000=NTLM, 1800=sha512crypt)",
            "-a <mode>  : Attack mode (0=dict, 3=brute, 6=hybrid)",
            "-o <file>  : Output cracked passwords to file",
            "--show     : Show already-cracked hashes",
            "--status   : Show status during cracking",
            "-r <rule>  : Apply a rule file",
        ],
        "examples": [
            ("MD5 dictionary attack", "hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt"),
            ("SHA-1 brute force 6 chars", "hashcat -m 100 -a 3 hash.txt ?a?a?a?a?a?a"),
            ("NTLM with rules", "hashcat -m 1000 hashes.txt rockyou.txt -r best64.rule"),
            ("Show cracked results", "hashcat -m 0 hashes.txt --show"),
        ],
    },
    "john": {
        "description": "John the Ripper is a fast open-source password security auditing tool.",
        "usage": "john [options] <password_file>",
        "options": [
            "--wordlist=<file>  : Use a wordlist",
            "--format=<type>    : Specify hash format (e.g. md5, sha1, nt)",
            "--rules            : Apply mangling rules to wordlist",
            "--show             : Show cracked passwords",
            "--incremental      : Brute-force mode",
        ],
        "examples": [
            ("Crack /etc/shadow with rockyou", "john --wordlist=/usr/share/wordlists/rockyou.txt /etc/shadow"),
            ("Crack NTLM hashes", "john --format=nt --wordlist=rockyou.txt hashes.txt"),
            ("Show results", "john --show hashes.txt"),
            ("Incremental brute force", "john --incremental hash.txt"),
        ],
    },
    "hydra": {
        "description": "Hydra is a fast and flexible online password cracking tool (brute-force).",
        "usage": "hydra [options] <target> <service>",
        "options": [
            "-l <user>  : Single username",
            "-L <file>  : Username list",
            "-p <pass>  : Single password",
            "-P <file>  : Password list",
            "-t <n>     : Number of parallel threads",
            "-s <port>  : Custom port",
            "-V         : Show each attempt",
            "-f         : Stop after first successful login",
        ],
        "examples": [
            ("SSH brute force", "hydra -l root -P rockyou.txt ssh://192.168.1.1"),
            ("HTTP POST login form", "hydra -l admin -P rockyou.txt 192.168.1.1 http-post-form '/login:username=^USER^&password=^PASS^:Invalid'"),
            ("FTP brute force", "hydra -L users.txt -P passwords.txt ftp://192.168.1.1"),
            ("RDP brute force", "hydra -l administrator -P rockyou.txt rdp://192.168.1.1"),
        ],
    },
    "gobuster": {
        "description": "Gobuster is a tool for brute-forcing URIs, DNS subdomains, and virtual hostnames.",
        "usage": "gobuster <mode> [options]",
        "options": [
            "dir        : Directory/file brute force mode",
            "dns        : DNS subdomain enumeration mode",
            "-u <url>   : Target URL",
            "-w <file>  : Wordlist",
            "-x <ext>   : File extensions to search (e.g. php,html)",
            "-t <n>     : Threads",
            "-o <file>  : Output file",
            "-s <codes> : Positive status codes (default: 200,204,301,302,307)",
        ],
        "examples": [
            ("Directory brute force", "gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt"),
            ("With PHP/HTML extension", "gobuster dir -u http://target.com -w common.txt -x php,html"),
            ("DNS subdomain enumeration", "gobuster dns -d target.com -w subdomains.txt"),
        ],
    },
    "openssl": {
        "description": "OpenSSL is a robust toolkit for TLS/SSL protocols and general cryptography.",
        "usage": "openssl <command> [options]",
        "options": [
            "enc        : Encrypt/decrypt files",
            "dgst       : Compute hash digests",
            "genrsa     : Generate RSA private key",
            "req        : Certificate request / self-signed cert",
            "s_client   : SSL/TLS client (debug connections)",
            "x509       : Display/manage certificates",
        ],
        "examples": [
            ("Generate SHA-256 hash of a file", "openssl dgst -sha256 file.txt"),
            ("Encrypt a file with AES-256", "openssl enc -aes-256-cbc -in plain.txt -out encrypted.enc"),
            ("Decrypt a file", "openssl enc -d -aes-256-cbc -in encrypted.enc -out plain.txt"),
            ("Generate RSA 2048-bit key", "openssl genrsa -out private.key 2048"),
            ("Check SSL certificate of a site", "openssl s_client -connect example.com:443"),
            ("Self-signed certificate", "openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes"),
        ],
    },
    "ssh": {
        "description": "SSH (Secure Shell) — encrypted remote login and command execution.",
        "usage": "ssh [options] user@host",
        "options": [
            "-p <port>  : Connect on a non-default port",
            "-i <key>   : Use a private key file",
            "-L <local:host:remote> : Local port forwarding",
            "-R <remote:host:local> : Remote port forwarding",
            "-D <port>  : Dynamic (SOCKS5) proxy",
            "-N         : Don't execute remote commands (for tunneling)",
            "-v         : Verbose (debug) mode",
        ],
        "examples": [
            ("Connect to a remote host", "ssh user@192.168.1.1"),
            ("Connect on port 2222", "ssh -p 2222 user@192.168.1.1"),
            ("Connect using private key", "ssh -i ~/.ssh/id_rsa user@192.168.1.1"),
            ("Local port forwarding", "ssh -L 8080:localhost:80 user@192.168.1.1"),
            ("SOCKS5 proxy tunnel", "ssh -D 1080 -N user@192.168.1.1"),
        ],
    },
    "grep": {
        "description": "grep searches files or stdin for lines matching a pattern.",
        "usage": "grep [options] <pattern> [file...]",
        "options": [
            "-i  : Case-insensitive match",
            "-r  : Recursive search in directories",
            "-n  : Show line numbers",
            "-v  : Invert match (show non-matching lines)",
            "-l  : Print only filenames with matches",
            "-c  : Count matching lines",
            "-E  : Extended regex (same as egrep)",
            "--color : Highlight matches",
        ],
        "examples": [
            ("Search for 'password' in a file", "grep -i 'password' config.txt"),
            ("Recursive search in all Python files", "grep -rn 'import os' /project --include='*.py'"),
            ("Find lines NOT containing 'error'", "grep -v 'error' log.txt"),
            ("Count occurrences", "grep -c 'failed' auth.log"),
        ],
    },
    "find": {
        "description": "find searches for files and directories matching criteria in a directory tree.",
        "usage": "find <path> [options] [expression]",
        "options": [
            "-name <pat>   : Match filename pattern",
            "-type f/d     : File (f) or directory (d)",
            "-size <n>     : Match file size",
            "-mtime <n>    : Modified n days ago",
            "-perm <mode>  : Match permissions",
            "-exec <cmd>   : Execute command on each result",
        ],
        "examples": [
            ("Find all .conf files in /etc", "find /etc -name '*.conf' -type f"),
            ("Find SUID binaries (privilege escalation check)", "find / -perm -u=s -type f 2>/dev/null"),
            ("Find files modified in last 24h", "find /var/log -mtime -1 -type f"),
            ("Find and delete .tmp files", "find /tmp -name '*.tmp' -exec rm {} \\;"),
        ],
    },
    "tcpdump": {
        "description": "tcpdump is a command-line packet analyzer for capturing and analyzing network traffic.",
        "usage": "tcpdump [options] [expression]",
        "options": [
            "-i <iface>  : Capture on interface",
            "-w <file>   : Save to pcap file",
            "-r <file>   : Read from pcap file",
            "-n          : Don't resolve hostnames",
            "-c <count>  : Capture exactly N packets",
            "-X          : Show hex and ASCII output",
            "port <n>    : Filter by port",
            "host <ip>   : Filter by host",
        ],
        "examples": [
            ("Capture on eth0", "tcpdump -i eth0"),
            ("Capture HTTP traffic", "tcpdump -i eth0 port 80"),
            ("Save to file", "tcpdump -i eth0 -w traffic.pcap"),
            ("Read pcap file", "tcpdump -r traffic.pcap"),
            ("Capture between two hosts", "tcpdump -i eth0 host 192.168.1.1 and host 192.168.1.2"),
        ],
    },
    "iptables": {
        "description": "iptables is the Linux firewall tool for filtering and manipulating network packets.",
        "usage": "iptables [-t table] <command> [chain] [match] [-j target]",
        "options": [
            "-A  : Append rule to chain",
            "-I  : Insert rule at position",
            "-D  : Delete rule",
            "-L  : List rules",
            "-F  : Flush (delete all rules in chain)",
            "-P  : Set default chain policy",
            "-j  : Jump target (ACCEPT, DROP, REJECT, LOG)",
            "-s  : Source IP/network",
            "-d  : Destination IP/network",
            "-p  : Protocol (tcp, udp, icmp)",
            "--dport : Destination port",
        ],
        "examples": [
            ("Block incoming port 23 (Telnet)", "iptables -A INPUT -p tcp --dport 23 -j DROP"),
            ("Allow SSH from specific IP", "iptables -A INPUT -p tcp -s 10.0.0.5 --dport 22 -j ACCEPT"),
            ("List all rules", "iptables -L -v -n"),
            ("Block all outbound to an IP", "iptables -A OUTPUT -d 192.168.1.100 -j DROP"),
            ("Allow established connections", "iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT"),
        ],
    },
    "sqlmap": {
        "description": "sqlmap is an open-source tool for automated SQL injection detection and exploitation.",
        "usage": "sqlmap -u <url> [options]",
        "options": [
            "-u <url>    : Target URL",
            "--dbs       : Enumerate databases",
            "-D <db>     : Select database",
            "--tables    : Enumerate tables",
            "-T <table>  : Select table",
            "--dump      : Dump table contents",
            "--forms     : Auto-detect and test forms",
            "--batch     : Non-interactive (use defaults)",
            "--level <n> : Test level 1-5",
            "--risk <n>  : Risk level 1-3",
        ],
        "examples": [
            ("Basic injection test", "sqlmap -u 'http://target.com/page?id=1' --batch"),
            ("List all databases", "sqlmap -u 'http://target.com/page?id=1' --dbs"),
            ("Dump a specific table", "sqlmap -u 'http://target.com/page?id=1' -D mydb -T users --dump"),
            ("Test a login form", "sqlmap -u 'http://target.com/login' --forms --batch"),
        ],
    },
    "aircrack-ng": {
        "description": "aircrack-ng is a suite for auditing wireless network security.",
        "usage": "aircrack-ng [options] <capture.cap>",
        "options": [
            "-w <wordlist>  : Wordlist for WPA cracking",
            "-b <bssid>     : Filter by access point MAC address",
            "-e <essid>     : Filter by network name",
        ],
        "examples": [
            ("Crack WPA with wordlist", "aircrack-ng -w rockyou.txt -b AA:BB:CC:DD:EE:FF capture.cap"),
            ("Crack WEP automatically", "aircrack-ng capture.cap"),
        ],
    },
    "volatility": {
        "description": "Volatility is the leading open-source memory forensics framework.",
        "usage": "volatility -f <memory.dmp> --profile=<Profile> <plugin>",
        "options": [
            "-f <file>          : Memory dump file",
            "--profile=<name>   : OS profile (e.g. Win7SP1x64, LinuxUbuntu)",
            "imageinfo          : Detect the profile",
            "pslist             : List running processes",
            "pstree             : Process tree",
            "netscan            : Network connections",
            "dlllist            : Loaded DLLs per process",
            "cmdline            : Command-line arguments",
            "hashdump           : Extract password hashes",
            "malfind            : Find injected code/malware",
        ],
        "examples": [
            ("Identify memory image profile", "volatility -f memory.dmp imageinfo"),
            ("List processes", "volatility -f memory.dmp --profile=Win7SP1x64 pslist"),
            ("Find malicious injected code", "volatility -f memory.dmp --profile=Win7SP1x64 malfind"),
            ("Extract NTLM hashes", "volatility -f memory.dmp --profile=Win7SP1x64 hashdump"),
        ],
    },
}


def has_command_reference(command: str) -> bool:
    return command.lower() in COMMAND_REFERENCE


def build_command_response(command: str) -> str | None:
    cmd = command.lower()
    ref = COMMAND_REFERENCE.get(cmd)
    if ref is None:
        return None

    lines = []
    lines.append(f"[COMMAND: {cmd}]")
    lines.append("=" * 50)
    lines.append(f"Description:\n  {ref['description']}")
    lines.append(f"\nUsage:\n  {ref['usage']}")

    lines.append("\nKey Options:")
    for opt in ref["options"]:
        lines.append(f"  {opt}")

    lines.append("\nExamples:")
    for label, example in ref["examples"]:
        lines.append(f"\n  [{label}]")
        lines.append(f"  ┌─────────────────────────────────────────")
        lines.append(f"  │  {example}")
        lines.append(f"  └─────────────────────────────────────────")

    return "\n".join(lines)
