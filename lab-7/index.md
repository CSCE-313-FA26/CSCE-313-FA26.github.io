---
layout: lab
title: "Lab 7 — Packet Sniffing and Spoofing"
lab_number: 7
lab_title: "Packet Sniffing and Spoofing"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
instructor: "David Kebo Houngninou"
released: "Tuesday, November 17, 2026, 9:00 AM CT"
due: "Friday, December 4, 2026, 11:59 PM CT"
released_short: "Tue Nov 17, 2026"
due_short: "Fri Dec 4, 2026, 11:59 PM CT"
description: "Use Scapy inside a small Docker network to sniff a victim's pings and forge ICMP echo replies that appear to come from the server it is talking to."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}

</nav>

## 1. Objectives

By the end of this lab you should be able to:

1. Explain what it means to *sniff* traffic on a network and why a shared
   local network makes it possible.
2. Read an ICMP echo request and echo reply, and name the fields that tie a
   `ping` reply to the request it answers (type, id, sequence, payload).
3. Use Scapy to capture packets with a BPF filter and a per-packet callback.
4. Use Scapy to *forge* a packet — set the source address to one you do not
   own — and put it on the wire.
5. Carry out an on-path spoofing attack: watch another host's `ping` and answer
   it yourself with a reply the victim accepts.
6. Run a small multi-container network with Docker Compose and find the
   interface that carries its traffic.

## 2. Background

### 2.1 ping, in two packets

`ping` is two ICMP messages. The sender emits an **echo request** (ICMP
**type 8**); whoever holds that address answers with an **echo reply** (ICMP
**type 0**). The reply copies three fields from the request so the sender can
match them up:

- **id** — chosen by the sender, usually its process id;
- **seq** — a counter that climbs by one per packet (`icmp_seq=1`, `2`, …);
- **payload** — a block of bytes the sender includes (often a timestamp), which
  the reply echoes back unchanged.

A reply whose id and seq do not match an outstanding request is dropped, which
is why a forged reply has to copy them.

### 2.2 Sniffing and spoofing

**Sniffing** is reading packets that were not addressed to you. On a shared
local network — one bridge, as here — every host can be put in *promiscuous*
mode and handed a copy of every frame. Scapy's `sniff()` does this for you.

**Spoofing** is sending a packet with a source address you do not own. Nothing
in IP checks that the source address of a packet belongs to the machine that
sent it, so a host on the path can answer *as if* it were someone else.

### 2.3 The attack in this lab

Three containers share one network, `10.9.0.0/24`:

```
  (1)  victim 10.9.0.6  ---- ICMP echo request ---->  server 10.9.0.5

  (2)  attacker  (on the same bridge, sniffing every packet)
           ---- forged echo reply: src=10.9.0.5, ttl=99 ---->  victim 10.9.0.6

  (3)  server 10.9.0.5  ---- its own real reply ---->  victim 10.9.0.6
```

The **victim** pings the **server** at `10.9.0.5`. The **attacker** sits on the
same bridge and sees that request. Before (or alongside) the server's own
reply, the attacker forges an echo reply with the **source set to the server's
address** and a **TTL of 99** — a value a normal reply on this network would
never have. The victim accepts it, and `ping` prints a reply with `ttl=99`.
That odd TTL is your proof that the reply the victim "trusted" was written by
the attacker, not the server.

You will write the attacker.

## 3. Environment setup

### 3.1 What you need

This lab runs on **Docker** with **Docker Compose**. Use a machine that has
both — a department lab machine, the SEED VM, or your own computer with Docker
Desktop. You do **not** need `sudo` for Scapy itself; the containers already
run privileged, which is what lets Scapy open a raw socket *inside* them.

The three containers are defined in `docker-compose.yml`, which you must **not**
modify:

| Container | Address | Role |
|---|---|---|
| `attacker` | shares the host's interfaces (`network_mode: host`) | sniffs the bridge and forges replies |
| `server` | `10.9.0.5` | the host the victim pings |
| `victim` | `10.9.0.6` | runs `ping 10.9.0.5` |

They all use the SEED project image `handsonsecurity/seed-ubuntu:large`. The
first start downloads it, which takes a while; later starts are fast.

### 3.2 Starting the network

From the repository directory:

```
docker-compose build
docker-compose up
```

(On newer Docker, the command is `docker compose` with a space.) Leave that
terminal running — it shows each container's output. The `server` container
starts `server.py` on its own; the `attacker` and `victim` wait for you.

To get a shell inside a container, open another terminal and run one of:

```
docker exec -it attacker /bin/bash
docker exec -it victim   /bin/bash
```

On the SEED VM the alias `docksh <name>` does the same thing.

### 3.3 Finding the attacker's interface

The attacker uses `network_mode: host`, so it shares the host's network
interfaces. Docker builds a **bridge** for `net-10.9.0.0` named `br-<id>`, and
*that* is the interface your sniffer must listen on. The `<id>` is generated
when the network is created, so it is different on every machine and after every
`docker-compose down` — **do not copy a name out of anyone else's code.**

Find yours. In a shell on the attacker (or on the host), run:

```
ifconfig
```

and look for the interface whose `inet` address is on `10.9.0.x` (the bridge
gateway, usually `10.9.0.1`). Its name — something like `br-84ac5bd10008` — is
what you pass to Scapy as `iface`.

## 4. Walkthrough

### 4.1 The files

- `docker-compose.yml` — the three-container network. **Do not modify.**
- `server.py` — the server. Prints a banner and sniffs ICMP so you can see the
  requests arrive. **Do not modify.**
- `victim.py` — pings `10.9.0.5` ten times. **Do not modify.** (You can also
  just run `ping 10.9.0.5` by hand inside the victim.)
- `attacker.py` — **the file you edit.** It imports Scapy and leaves two blanks
  for you to fill.

### 4.2 The Scapy you need

```python
from scapy.all import *

# sniff: capture packets and run a function on each one
sniff(iface="br-...", filter="icmp", prn=handle, store=False)

# build layers and stack them with '/'
pkt = IP(src="a", dst="b", ttl=99) / ICMP(type=0, id=1, seq=1) / Raw(load=data)

# read fields off a sniffed packet
pkt[IP].src, pkt[IP].dst          # addresses
pkt[ICMP].type, pkt[ICMP].id, pkt[ICMP].seq
pkt[Raw].load                     # the payload bytes, if any

# put a packet on the wire
send(pkt, verbose=0)
```

`filter="icmp"` is a BPF filter: Scapy hands your callback only ICMP packets.
`store=False` tells it not to keep every packet in memory — you are reacting to
them, not collecting them.

## 5. To-do

You edit **only `attacker.py`**, in the two places marked `YOUR CODE HERE`.

### 5.1 Write `spoof_pkt(pkt)`

This function runs once per captured packet. When `pkt` is an ICMP **echo
request** (`pkt[ICMP].type == 8`):

1. Build an IP layer whose **source is the request's destination** and whose
   **destination is the request's source** — so the reply appears to come from
   the server the victim pinged. Give it `ttl=99`.
2. Build an ICMP layer with **`type=0`** (echo reply) and the **same `id` and
   `seq`** as the request.
3. If the request carries a payload (`Raw in pkt`), copy `pkt[Raw].load` onto
   your reply so the lengths match.
4. `send()` the finished packet.

Ignore anything that is not an echo request — do not answer your own replies.

### 5.2 Call `sniff` on the right interface

At the bottom of the file, call `sniff` with:

- `iface=` the `br-…` name you found in §3.3,
- `filter="icmp"`,
- `prn=spoof_pkt`,
- `store=False`.

### 5.3 Run it

1. Start the network (`docker-compose up`) and open a shell on the attacker.
2. Run your attacker so it is sniffing: `python3 attacker.py`.
3. In another shell, run the victim's ping: `docker exec -it victim python3 victim.py` (or `ping -c 10 10.9.0.5` inside the victim).
4. Watch the victim's output. Among the replies you should see lines with
   **`ttl=99`**, and some marked **`(DUP!)`** — the real server answers too, so
   the victim gets two replies per request. The `ttl=99` reply is yours.

> The exact lines depend on timing and on your machine — which reply arrives
> first, how many are marked `DUP!`. What is fixed is the `ttl=99`: a normal
> reply on this network never has it, so seeing it means your forged packet was
> accepted.

## 6. Checking your work

The autograder grades the one thing you write — your `spoof_pkt` handler — by
importing `attacker.py` with Scapy's `sniff()` and `send()` replaced by stubs,
then feeding your handler known ICMP packets and inspecting the replies it tries
to send. **It needs neither Docker nor root**, so you can run it anywhere Python
and Scapy are installed, including inside the attacker container:

```
python3 tests/grade.py
```

It reports, out of 100:

| Check | Points |
|---|---|
| `attacker.py` sniffs ICMP and calls your handler | 15 |
| a ping (echo request) is answered with one echo reply | 25 |
| the reply is spoofed to come from the pinged host | 20 |
| the reply uses a different TTL from the request | 20 |
| the reply copies the ICMP id, seq and payload | 20 |

The live three-container run in §5.3 is how you *see* the attack work; it is not
re-run by the grader. If `tests/grade.py` gives you 100 but the live demo does
not show `ttl=99`, the usual cause is the `iface` name in your `sniff` call —
re-check §3.3.

## 7. Deliverables

Commit and push your edited `attacker.py`:

```
git add attacker.py
git commit -m "Lab 7"
git push
```

Every push is graded and the last one before the deadline counts. Do not commit
`server.py`, `victim.py` or `docker-compose.yml` — they are given and unchanged.

## 8. Getting help

Ask on the course **Discord** or come to office hours. When you ask about the
live run, say which interface name `ifconfig` showed you and paste the victim's
`ping` output — most problems here are the wrong `iface`.

## Revision history

- **Nov 17, 2026** — initial release.
