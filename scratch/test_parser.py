import re
import os

DATA_RE = re.compile(
    r'\[\s*(?P<id>\d+|SUM)\]\s+'
    r'(?P<t0>[\d.]+)-(?P<t1>[\d.]+)\s+sec\s+'
    r'[\d.]+\s+\w+Bytes\s+'
    r'(?P<rate>[\d.]+)\s+(?P<unit>[GkMK])bits/sec'
    r'(?:\s+(?P<retx>\d+))?'
    r'(?:\s+(?P<jitter>[\d.]+)\s+ms)?'
    r'(?:\s+(?P<lost>\d+)/\s*(?P<total>\d+))?'
)

ACCEPTED_RE = re.compile(r'Accepted connection from')
LISTEN_RE   = re.compile(r'Server listening on')

LOG_PATH = "/home/dtovar/bayblade/iperf/logs/iperf3_server.log"

def test_parse():
    if not os.path.exists(LOG_PATH):
        print("Log not found")
        return

    with open(LOG_PATH, "r") as f:
        lines = f.readlines()
    
    print(f"Total lines: {len(lines)}")
    
    session_start = 0
    for i in range(len(lines) - 1, -1, -1):
        if ACCEPTED_RE.search(lines[i]):
            session_start = i
            break
    
    print(f"Session start at line: {session_start}")
    session_lines = lines[session_start:]
    print(f"Lines in session: {len(session_lines)}")

    count = 0
    for line in session_lines:
        m = DATA_RE.search(line)
        if m:
            count += 1
            if count < 5 or count > len(session_lines) - 5:
                print(f"Match: {m.groups()}")
    
    print(f"Total matches: {count}")

if __name__ == "__main__":
    test_parse()
