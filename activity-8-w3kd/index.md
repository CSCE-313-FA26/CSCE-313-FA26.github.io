---
layout: activity
title: "Activity 8 — Crafting, Sending and Sniffing Packets"
activity_id: 8
activity_title: "Crafting, Sending and Sniffing Packets"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Networking"
duration: "30 minutes"
listed: false        # reachable by direct link, not shown in the index
description: "Build three packets with Scapy and save them to a capture file; then send them on the loopback interface and sniff them back, reading each one apart as a real sniffer would."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Description

You write your packets in two short halves.

- **Part A — craft.** In `craft.py`, build three packets and save them to
  `out.pcap`, the same capture format Wireshark and tcpdump use.
- **Part B — send & sniff.** Send those packets on the `lo` loopback interface
  from one terminal and watch them arrive in another, where a real `sniff()`
  call prints each one apart.

The demos from lecture are in
[`scapy-practice`](https://github.com/CSCE-313-FA26/scapy-practice) — the
`build/`, `protocols/` and `pcap/` folders cover Part A, and `live/` covers
Part B.

> **Root, and where you need it.** Part A needs none — building packets and
> writing a capture are ordinary file work. Part B opens raw sockets to send and
> to sniff, so you run those two scripts with `sudo`. You have `sudo` on your own
> Ubuntu VM. Everything stays on `lo`, so nothing leaves your machine.

## 2. Getting Your Repository

Accept the assignment, then clone your own copy:

<https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/activity-8/accept>

```bash
git clone https://github.com/CSCE-313-FA26/csce-313-fa26-activity-8-<your-username>.git
cd csce-313-fa26-activity-8-<your-username>
python3 craft.py
```

Check Scapy is installed with `python3 -c "import scapy"`, which prints nothing
and succeeds. The repo ships three files — `craft.py` (Part A) and `sniffer.py`
/ `sender.py` (Part B) — each with a line or two to finish. Part A runs as
yourself; the two Part B scripts open raw sockets, so run them with `sudo`.

## 3. Craft three packets (Part A)

### 3.1 Running what you were given

`craft.py` runs as handed to you and writes an **empty** capture, because the
tasks are not filled in yet:

```bash
$ python3 craft.py
wrote 0 packet(s) to out.pcap
```

Build each packet and `packets.append(...)` it; the
`wrpcap("out.pcap", packets)` line at the bottom is already there.

### 3.2 Task 1 — an ICMP echo request

A ping to the server at `10.9.0.5`. An `IP` layer carrying an `ICMP` layer is an
echo request by default — Scapy sets the ICMP type to 8 for you.

```python
packets.append(IP(dst="10.9.0.5") / ICMP())
```

That one is given as the pattern. The other two are the same idea.

### 3.3 Task 2 — a TCP SYN

The first packet of every TCP connection: a SYN to the web port. Set three
things — the destination `10.9.0.5`, the destination port `80`, and the SYN
flag, which Scapy writes `flags="S"`. Build an `IP(...)/TCP(...)` and append it.
See `protocols/tcp_syn.py`.

### 3.4 Task 3 — a DNS query

A question: "what is the A record for `tamu.edu`?" DNS rides on **UDP port 53**,
and the question is a `DNSQR` (DNS Question Record):

```python
IP(dst=...) / UDP(dport=53) / DNS(rd=1, qd=DNSQR(qname="...", qtype="A"))
```

`protocols/dns_query.py` is this exact packet.

> **Build all three the same way.** `wrpcap` writes one link-layer type for the
> whole file, taken from the first packet. Start every packet with `IP(...)` — no
> Ethernet layer — exactly like Task 1, or the odd ones out get mis-framed and
> the grader cannot read them.

## 4. Send them, and sniff them back (Part B)

Now watch the packets travel. You use **two terminals**: one runs a sniffer that
waits and prints each packet it sees, the other sends your packets. Both work on
`lo`, the loopback interface every machine has — a frame you send on `lo` never
leaves your VM, and the sniffer sees exactly the frames you sent. This is how
real tools work: a capture running in one window, traffic in another.

The repo gives you two short scripts, `sniffer.py` and `sender.py`. Each has one
line for you to finish.

### 4.1 Task 4 — finish the sniffer

A sniffer is just a function that runs once for each packet. In `sniffer.py`,
finish `describe` so it prints what each packet is. The ICMP line is done — add
the TCP and DNS lines the same way:

```python
def describe(pkt):
    if ICMP in pkt:
        print("ICMP echo request to", pkt[IP].dst)
    elif TCP in pkt:
        print(...)       # TODO: "TCP SYN to", pkt[IP].dst, "port", pkt[TCP].dport
    elif DNS in pkt:
        print(...)       # TODO: "DNS query for", pkt[DNS].qd.qname
```

The file ends with a line, already written for you, that starts the sniffer on
`lo` and calls `describe` for each packet.

> **A UDP packet on port 53 *is* DNS to Scapy.** So check `DNS in pkt`, not the
> port number. The name you want is `pkt[DNS].qd.qname`.

### 4.2 Task 5 — finish the sender

`sender.py` reads the capture you made in Part A and puts each packet on `lo`.
Add the `sendp` line. Each packet gets an `Ether()` header, because an interface
carries Ethernet frames (the pcap file in Part A did not need one):

```python
packets = rdpcap("out.pcap")       # the 3 packets from Part A
for pkt in packets:
    sendp(...)                     # TODO: send  Ether() / pkt  on "lo"
```

### 4.3 Run them together

In the **first** terminal, start the sniffer. It waits:

```bash
$ sudo python3 sniffer.py
sniffing on lo - now run sender.py in another terminal
```

In the **second** terminal, send the packets:

```bash
$ sudo python3 sender.py
sent 3 packets on lo
```

Back in the first terminal, the sniffer prints your three packets, then stops on
its own:

```
ICMP echo request to 10.9.0.5
TCP SYN to 10.9.0.5 port 80
DNS query for b'tamu.edu.'
```

(The DNS name comes out as `b'tamu.edu.'` — Scapy stores names as bytes. That is
fine.)

## 5. Checking Your Work

Run the grader yourself before you push — it is the same one that runs on the
server:

```bash
make test
```

It runs your `craft.py` and reads `out.pcap` for Part A, then imports your
`describe` and runs your `sender.py` for Part B, printing a line per task with
the points and, when a task is wrong, what it found versus what it expected.
Everything the grader does is root-free, so `make test` works as yourself.

## 6. How It Is Graded

Everything is judged by what your program *does* — the capture it writes, the
line `describe` prints, and the frames `sender.py` puts on the interface.
Nothing reads your source for credit, and extra fields you set (a source port, a
TTL) do not matter.

| Row | Points |
|---|---|
| **Part A** — `craft.py` runs and writes a readable `out.pcap` | 10 |
| Task 1 — an ICMP echo request to `10.9.0.5` | 15 |
| Task 2 — a TCP SYN to port 80 on `10.9.0.5` | 15 |
| Task 3 — a DNS query for `tamu.edu` on UDP/53 | 10 |
| **Part B** — Task 4: `describe` names ICMP, TCP SYN and DNS correctly | 25 |
| Task 5 — `sender.py` puts all three packets on `lo` | 25 |

> **Do Part A first.** Part B sends the same three packets you built in Part A,
> so a missing packet costs you in both halves. Get the capture right, then wire
> up the sniffer and the sender.

## 7. Submitting

```bash
git add craft.py sniffer.py sender.py
git commit -m "Activity 8"
git push
```

Push as often as you like; every push is graded and the last one counts.

## 8. If You Finish Early

Each is a few lines, none is graded.

- **Add a fourth packet.** Build an ARP who-has for `10.9.0.1` in `craft.py`,
  change the sniffer's `count` to 4, and add an `elif ARP in pkt:` branch to
  `describe`.
- **Sniff from a file instead.** `sniff(offline="out.pcap", prn=describe)` runs
  the same callback over your saved capture — no second terminal, no `sudo`.
  Confirm you get the same lines.
- **Look at the bytes.** `hexdump(packets[1])` prints your TCP SYN as the raw
  bytes that would go on the wire — 20 bytes of IP header, then 20 of TCP.
- **Ask for a different record.** Change Task 3's `qtype` to `"MX"` (mail
  servers) or `"AAAA"` (IPv6) and read the question back out through your
  sniffer.
