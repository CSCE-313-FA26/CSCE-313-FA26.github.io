---
layout: activity
title: "Activity 7 — Client and Server with the Socket API"
activity_id: 7
activity_title: "Client and Server with the Socket API"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Lab 6"
listed: false        # reachable by direct link, not shown in the index
description: "Complete a TCP client and server, then make the server serve one client after another and let each client send as many messages as it likes."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Description

You are given the client and server we walked through in lecture, with six
calls taken out of them and two loops missing. Both programs run on your own
machine: the client connects to the server over `localhost`, and they exchange
messages.

Four tasks, and they build on each other:

| Task | Where | What |
|---|---|---|
| 1 | `server.c` | Create the socket, fill in the address, bind it, accept a connection |
| 2 | `client.c` | Read the port, create the socket, look up the host, connect |
| 3 | `server.c` | Loop around `accept()` so the server serves one client after another |
| 4 | `server.c` and `client.c` | Loop around the exchange so each client can send more than one message |

**Do Tasks 1 and 2 first.** Nothing can be tested until a client can reach a
server, so the two loops are impossible to check before the connection works.

## 2. Getting Your Repository

Accept the assignment, then clone your own copy:

<https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/activity-7/accept>

```bash
git clone https://github.com/CSCE-313-FA26/csce-313-fa26-activity-7-<your-username>.git
cd csce-313-fa26-activity-7-<your-username>
make
```

The starter compiles, but **with six warnings** — `sockfd`, `newsockfd`,
`portno` and `server` "may be used uninitialized", and `clilen` "set but not
used". They are telling you exactly where the missing calls go, and they all
disappear as you fill the tasks in.

## 3. Running the Program You Were Given

You need **two terminals**. Pick a port above 1024, and pick your own number —
these machines are shared, and two people on the same port collide.

Terminal 1, the server:

```bash
./server 8080
```

Terminal 2, the client:

```bash
./client localhost 8080
```

Before Task 1 the server will not get as far as listening, so the client
cannot connect. That is the starting point.

## 4. The Four Tasks

### 4.1 Task 1 — the server's half of the connection

Four lines, marked `TASK 1a` to `TASK 1e` in `server.c`:

- **`socket()`** with the IPv4 address family and a stream (TCP) socket type.
  Store the result in `sockfd`.
- **`sin_family`** — the address family of the address you are about to bind.
- **`sin_port`** — the port number, passed through `htons()`. Network byte
  order is big-endian; leave `htons()` out and port 8080 becomes 36895, so no
  client can find you.
- **`bind()`** — attach the socket to that address. Call
  `error("ERROR on binding")` if it fails.
- **`accept()`** — block until a client arrives, and store the result in
  `newsockfd`.

`accept()` returns a **second** socket. `sockfd` is the one that listens;
`newsockfd` is the one this conversation happens on. Keeping them straight is
the whole trick in Tasks 3 and 4: closing `newsockfd` ends one conversation,
closing `sockfd` stops the server.

### 4.2 Task 2 — the client's half

Six lines, marked `TASK 2a` to `TASK 2f` in `client.c`: the port number from
`argv[2]`, the socket, `gethostbyname(argv[1])`, `sin_family`, `sin_port`, and
`connect()`.

A client does **not** call `bind()`. The kernel picks a local port for it. That
is the number after the colon when the server prints where its client came
from, and it is different for every connection.

### 4.3 Task 3 — one client after another

As it stands, the server accepts one connection, talks, and exits. Put a loop
around the part of `main` that starts at `accept()`, so that when a client
disconnects the server goes back to waiting instead of returning.

Two things to get right:

- **`close(newsockfd)` belongs inside the loop; `close(sockfd)` does not.**
  Close the listening socket and your server stops listening.
- Nothing after the loop runs. Stop the server with **Ctrl+C**.

### 4.4 Task 4 — more than one message

Put a loop around the read-and-answer pair, so one client can keep sending.
End that loop when either of these happens:

- the client sends `bye`, or
- **`read()` returns 0.**

`read()` returning 0 is not an error — it is end-of-file, and it means the
client closed its end of the connection. This is the single most common place
to get sockets wrong: a server that treats 0 as "nothing to read, try again"
spins at 100% CPU forever, and one that treats it as a failure reports an error
that never happened.

Give the client the matching loop, so you can type several messages in a row.
`fgets()` returning `NULL` is the client's end-of-file — that is Ctrl+D.

## 5. Expected Output

Server terminal, after one client sent three messages and a second client
connected and pressed Ctrl+D:

```
$ ./server 8080
Server listening on port 8080
Press Ctrl+C to stop the server.

Server received a connection!
Message from client (12 bytes): hello there
Message from client (34 bytes): sockets are just file descriptors
Message from client (4 bytes): bye
Server received a connection!
Message from client (27 bytes): second client, same server
```

The client's terminal:

```
$ ./client localhost 8080
Connected to localhost on port 8080
Hello from the server! Send a message, or 'bye' to disconnect.
Please enter the message: hello there
Server: received (12 bytes): HELLO THERE
Please enter the message: sockets are just file descriptors
Server: received (34 bytes): SOCKETS ARE JUST FILE DESCRIPTORS
Please enter the message: bye
Server: Goodbye!
```

**The exact wording is yours.** The lines above are what the given code prints;
nothing is graded on the text of a message. What is graded is that an answer
comes back, that several come back on one connection, and that the server is
still there for the next client.

## 6. How It Is Graded

Everything is measured by **running your programs over a real TCP connection**.
Nothing reads your source for credit.

| Row | Points |
|---|---|
| Builds with no errors | 10 |
| Your client connects to a server and exchanges a message | 20 |
| Your server accepts a connection and answers one message | 20 |
| Your server answers repeated messages on one connection | 25 |
| Your server accepts another client after the first leaves | 25 |

Your client is tested against a reference server, and your server is tested
with a reference client, so the two halves are scored **independently** — a
client that does not work cannot cost you the server's rows.

You can run the same checks yourself before you push:

```bash
python3 tests/grade.py
```

## 7. Submitting

```bash
git add client.c server.c
git commit -m "Activity 7"
git push
```

Push as often as you like; every push is graded and the last one counts.

## 8. If You Finish Early

Each of these is a few lines, and none of them is graded.

- **Serve a web browser.** Run your server, then open
  `http://localhost:8080` in a browser instead of running your client. Print
  what arrives: a real HTTP request, in plain text. Reply with
  `HTTP/1.1 200 OK`, a blank line and some HTML, and the browser will render
  it.
- **Throw your client away.** `nc localhost 8080` talks to your server just as
  well. The protocol is the contract, not the program.
- **Two clients at once.** Connect a second client while the first is still
  connected. Your server answers one and makes the other wait, because one
  process can only be inside one conversation at a time. Serving both means
  forking a child per connection — which is Lab 6.
- **Watch the handshake.** `sudo tcpdump -i lo -n port 8080` in a third
  terminal, then connect. SYN, SYN-ACK, ACK — and FIN when you disconnect.
