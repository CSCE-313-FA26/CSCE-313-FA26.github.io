---
layout: activity
title: "Activity 8 — Crafting Packets with Scapy"
activity_id: 8
activity_title: "Crafting Packets with Scapy"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Networking"
published: false     # HELD - flip to true at release
listed: false        # reachable by direct link, not shown in the index
description: "Build three network packets to specification with Scapy — an ICMP echo request, a TCP SYN and a DNS query — and save them to a capture file the autograder reads."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Description

You write one file, `craft.py`. It builds three packets with
[Scapy](https://scapy.net) and saves them to `out.pcap`, the same capture
format Wireshark and tcpdump use. The autograder reads that file and checks
each packet.

Nothing is sent on a wire, so **none of this needs root**. Putting a packet on
a real network needs a raw socket, which you do not have on the lab machines —
but building a packet, turning it into bytes and writing it to a capture file
are all unprivileged. That is the whole activity.

Three packets, independent of each other:

| Task | Packet |
|---|---|
| 1 | an ICMP echo request (a ping) to `10.9.0.5` |
| 2 | a TCP SYN to port 80 on `10.9.0.5` |
| 3 | a DNS query for the A record of `tamu.edu` |

The demos from lecture are in
[`scapy-practice`](https://github.com/CSCE-313-FA26/scapy-practice) — the
`build/`, `protocols/` and `pcap/` folders there do exactly the pieces you need.

## 2. Getting Your Repository

Accept the assignment, then clone your own copy:

<https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/activity-8/accept>

```bash
git clone https://github.com/CSCE-313-FA26/csce-313-fa26-activity-8-<your-username>.git
cd csce-313-fa26-activity-8-<your-username>
python3 craft.py
```

Scapy is already installed on the lab machines — check with
`python3 -c "import scapy"`, which prints nothing and succeeds.

## 3. Running What You Were Given

`craft.py` runs as handed to you:

```bash
$ python3 craft.py
wrote 0 packet(s) to out.pcap
```

It writes an **empty** capture, because the three tasks are not filled in yet.
Your job is to build each packet and append it to the `packets` list; the
`wrpcap("out.pcap", packets)` line at the bottom is already there.

## 4. The Three Tasks

Each task is a packet. Build it, then `packets.append(...)` it.

### 4.1 Task 1 — an ICMP echo request

A ping to the server at `10.9.0.5`. An `IP` layer carrying an `ICMP` layer is
an echo request by default — Scapy sets the ICMP type to 8 (echo request) for
you.

```python
packets.append(IP(dst="10.9.0.5") / ICMP())
```

That one is given to you as the pattern. The other two are the same idea.

### 4.2 Task 2 — a TCP SYN

The first packet of every TCP connection: a SYN to the web port. You set three
things on this one — the destination `10.9.0.5`, the destination port `80`, and
the SYN flag, which Scapy writes `flags="S"`.

Build an `IP(...)/TCP(...)` and append it. Look at
`protocols/tcp_syn.py` in `scapy-practice` if you need the field names.

### 4.3 Task 3 — a DNS query

A question: "what is the A record for `tamu.edu`?" DNS rides on **UDP port 53**,
and the question itself is a `DNSQR` (DNS Question Record) with the name in it.
The shape is three layers:

```
IP(dst=...) / UDP(dport=53) / DNS(rd=1, qd=DNSQR(qname="...", qtype="A"))
```

`protocols/dns_query.py` in `scapy-practice` is this exact packet.

### Build all three the same way

`wrpcap` writes **one** link-layer type for the whole file, taken from the
first packet. If you build some packets with an `Ether()` layer and some
without, the odd ones out get mis-framed and the grader cannot read them. The
simplest rule: start every packet with `IP(...)` — no Ethernet layer — exactly
like Task 1 above.

## 5. Checking Your Work

Run the grader yourself before you push — it is the same one that runs on the
server:

```bash
make test
```

It builds your `out.pcap` and prints a line per task, with the points and, when
a task is wrong, what it found versus what it expected.

## 6. How It Is Graded

The grader runs your `craft.py`, reads the `out.pcap` it writes, and looks for a
packet matching each task. Nothing reads your source for credit, and **extra
fields you set — a source port, a TTL, an Ethernet layer on all three — do not
matter.** A task passes when a packet that fits is in the file.

| Row | Points |
|---|---|
| `craft.py` runs and writes a readable `out.pcap` | 10 |
| Task 1 — an ICMP echo request to `10.9.0.5` | 30 |
| Task 2 — a TCP SYN to port 80 on `10.9.0.5` | 30 |
| Task 3 — a DNS query for `tamu.edu` on UDP/53 | 30 |

## 7. Submitting

```bash
git add craft.py
git commit -m "Activity 8"
git push
```

Push as often as you like; every push is graded and the last one counts.

## 8. If You Finish Early

Each is a few lines, none is graded, and none needs root.

- **Read your own capture back.** `rdpcap("out.pcap")` returns a list; loop over
  it and print `p.summary()` for each, then `.show()` one in full. This is what
  the grader does.
- **Make the ping to a different host.** Change Task 1's destination, run again,
  and read it back to confirm the field changed.
- **Look at the bytes.** `hexdump(packets[1])` prints your TCP SYN as the raw
  bytes that would go on the wire — 20 bytes of IP header, then 20 of TCP.
- **Ask for a different record.** Change Task 3's `qtype` to `"MX"` (mail
  servers) or `"AAAA"` (IPv6) and read the question back out.
