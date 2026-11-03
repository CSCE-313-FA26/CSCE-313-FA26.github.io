---
layout: lab
title: "Lab 6 — Networking"
lab_number: 6
lab_title: "Networking"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
instructor: "David Kebo Houngninou"
released: "Tuesday, November 3, 2026, 9:00 AM CT"
due: "Monday, November 16, 2026, 11:59 PM CT"
released_short: "Tue Nov 3, 2026"
due_short: "Mon Nov 16, 2026, 11:59 PM CT"
description: "Replace the banking system's local pipes with TCP sockets, so the client and the three servers can run on different machines."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}

</nav>

## 1. Objectives

By the end of this lab you should be able to:

1. Create a TCP server with `socket`, `bind`, `listen` and `accept`, and a TCP
   client with `socket` and `connect`.
2. Explain why a TCP connection is a stream of bytes rather than a stream of
   messages, and frame messages so that the receiver can tell where each one
   ends.
3. Convert between host and network byte order, and say which values need it.
4. Serve several clients at the same time by handing each accepted connection
   to a thread pool.
5. Decide what a program should do when the other end of a connection
   disappears — which, on a network, it will.
6. Report a failure to the caller instead of ending the process, so one broken
   connection does not take the whole program down.

## 2. Background

### 2.1 What changed since Lab 5

Labs 2 to 5 connected the client and the three servers with **named pipes**.
A FIFO is a file in a directory, so both ends had to be on the same machine,
and the client created its servers as child processes.

This lab replaces that with **TCP sockets**. `channel.h` and `channel.cpp` are
gone; in their place are `network_channel.h` and `network_channel.cpp`, holding
a `NetworkRequestChannel` class with much the same interface. Four things
follow from the change:

- **The servers are now independent programs.** You start each one yourself,
  in its own terminal, and it keeps listening until you stop it. The client no
  longer forks anything.
- **A server can be on another machine.** The client takes a hostname and a
  port for each of the three servers.
- **One server serves many clients.** It accepts a connection, hands it to the
  thread pool you wrote in Lab 5, and goes straight back to accepting.
- **Either end can vanish at any moment.** A FIFO's reader was a child process
  you controlled. A network peer can be switched off, and your program has to
  keep working when it is.

`thread_pool.cpp` and `signals.cpp` are complete and are **not** part of this
lab's grade. They are the code you wrote for Labs 5 and 4.

### 2.2 Sockets, in six calls

A socket is one end of a connection, named by an IP address and a port number.
TCP sockets are reliable and connection-oriented: what you send arrives, in
order, or the connection fails.

A **server** makes a socket, claims a port, and waits:

| Call | What it does |
|---|---|
| `socket(AF_INET, SOCK_STREAM, 0)` | creates an IPv4 TCP socket and returns a descriptor |
| `setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, …)` | allows the port to be re-used (see §3.3) |
| `bind(fd, addr, len)` | claims a port on this machine |
| `listen(fd, 10)` | marks the socket passive, with room for 10 connections waiting to be accepted |
| `accept(fd, …)` | blocks until a client connects, then returns **a new descriptor** for that one client |

A **client** makes a socket and reaches out:

| Call | What it does |
|---|---|
| `socket(AF_INET, SOCK_STREAM, 0)` | the same as above |
| `connect(fd, addr, len)` | connects to a listening server |

Both ends then use `send` and `recv`, and `close` when they are done.

The descriptor `accept` returns is the one you talk to a client over. The
listening descriptor is never used for data — it only ever produces more
connections. That is why the class has two constructors: one that sets up a
listening socket, and one that wraps a descriptor `accept` has just returned.

`struct sockaddr_in` is where the address goes:

```c
struct sockaddr_in {
    short          sin_family;   // AF_INET
    unsigned short sin_port;     // port, in NETWORK byte order
    struct in_addr sin_addr;     // IPv4 address
    char           sin_zero[8];  // padding
};
```

### 2.3 Network byte order

Machines disagree about which end of a number comes first in memory. The
network has one convention — big-endian, most significant byte first — and
every multi-byte number that travels over a socket has to be in it.

| Function | Use it for |
|---|---|
| `htons` / `ntohs` | 16-bit values: `sin_port` |
| `htonl` / `ntohl` | 32-bit values: this protocol's length header |

The address itself is already in network order when `inet_pton` or
`gethostbyname` fills it in, so do not convert it again. On an x86 machine
leaving out the conversion often appears to work when both ends are the same
machine, and then fails the moment they are not — so do it anyway.

### 2.4 TCP is a stream of bytes, not a stream of messages

This is the one idea in the lab that catches people out, so it is worth being
precise about.

When you call `send` with 1,000,000 bytes, TCP does not promise to deliver them
as one unit, and when you call `recv` asking for 1,000,000 bytes, **the kernel
is free to give you fewer** — whatever has arrived so far. It does exactly that
as soon as a message is larger than the socket buffer, which on a typical
machine is a few hundred kilobytes.

That failure is quiet. Measured on the previous version of this code, which
called `recv` once: a **1,048,576-byte** file upload arrived as **127,986
bytes**, the file server wrote the truncated copy, and the client printed
`File upload successful`. The next read then started in the middle of the old
message and the connection fell over with a parse error. Nothing said the file
had been cut.

The fix is the reason this protocol puts a length in front of every message:

1. Read **exactly 4 bytes**. That is the length.
2. Read **exactly that many bytes**. That is the message.

"Exactly N bytes" means a loop, and two helpers in
`network_channel.cpp` — `send_all` and `recv_all` — are **given to you** with
that loop already written. Read them, and call them instead of calling `send`
and `recv` yourself. `recv_all` returns three different things, and all three
matter:

| Return | Meaning |
|---|---|
| `1` | all N bytes arrived |
| `0` | the peer closed the connection — **end of file, not an error** |
| `-1` | a real error; `errno` says what |

A `0` treated as success means parsing a buffer that was never filled. A `0`
treated as an error means reporting a problem where the other end simply
finished.

### 2.5 The wire format

Two message shapes, both sent as a 4-byte big-endian length followed by that
many bytes of text:

```
request    TYPE|USER_ID|AMOUNT|FILENAME|DATA
response   SUCCESS|BALANCE|DATA|MESSAGE
```

| Field | Meaning |
|---|---|
| `TYPE` | the `RequestType` enum as an integer |
| `USER_ID` | which account |
| `AMOUNT` | the amount, for a financial operation |
| `FILENAME` | the file, for a file operation |
| `DATA` | file contents, or anything else that does not fit above |
| `SUCCESS` | `1` or `0` |
| `BALANCE` | the account balance |
| `MESSAGE` | text for the user |

`DATA` is the **last** field of a request on purpose. It carries file contents,
and file contents contain `|` — every C++ file with an `||` in it does. So a
request is split at its first four delimiters and everything after the fourth
is `DATA`, delimiters included. `Request::parseRequest` in `common.cpp` already
does that, and `split_response` in `network_channel.cpp` does the matching
thing for a response: first two fields from the left, `MESSAGE` from the right,
`DATA` in between.

That works only because `MESSAGE` is written by the server and never contains
`|`. It is a genuine weakness of a delimiter-separated format with an unescaped
payload, and it is worth knowing it is there rather than discovering it later.
A filename containing `|` still cannot be sent at all.

### 2.6 One connection, one thread, from a pool

Each server does this:

```
make a listening channel
make a ThreadPool
loop until shutdown is requested:
    fd = accept a connection
    hand (fd) to the pool, which runs handle_client(fd, …)
```

`handle_client` builds a channel from that descriptor and then answers requests
on it until the client quits. It runs for as long as the client stays
connected, so one pool thread is busy per connected client, and a pool of four
threads serves four clients at once.

The important part is what the accept loop does **not** do. If it calls
`handle_client` itself instead of handing it to the pool, the server answers
one client correctly and never reaches `accept` again — a second client
connects, sends a request, and waits for ever. Nothing in the first client's
session reveals the problem.

### 2.7 When the other end disappears

Three things can happen that have no equivalent in the FIFO labs.

**Writing to a closed connection raises `SIGPIPE`**, whose default action kills
the process outright, with no message. On a network that is unacceptable: one
client pressing Ctrl+C would take the server down for everybody else.
`SignalHandling::setup_handlers()` ignores it, so `send` returns `-1` with
`errno` set to `EPIPE` and you can report it. All four programs call
`setup_handlers` first, so this is already done for you — but it is the reason
your `send_response` must cope with failing rather than assume it worked.

**`receive_request` cannot tell a polite goodbye from a disappearance.** Both
arrive as "nothing more to read", so both return `Request(QUIT)`. The server
therefore tries to acknowledge a client that is already gone, that send fails,
and the handler ends anyway. That is fine — as long as the failing send does
not kill the process.

**`accept` can be interrupted.** The SIGINT handler is installed without
`SA_RESTART`, so when you press Ctrl+C a blocked `accept` returns `-1` with
`errno == EINTR`. That is not an error: it is the only moment the accept loop
gets to notice that shutdown was requested. Treat `EINTR` as "go round again",
and anything else as an error worth reporting. Note that whatever you call
between `accept` failing and reading `errno` may overwrite it, which is why
`accept_connection` returns `-1` without printing anything.

## 3. Environment setup

### 3.1 Accept the assignment

Accept Lab 6 here:

<https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/lab-6/accept>

Then clone the repository the accept creates for you. Work in that clone and
push to it; that is what is graded.

### 3.2 Repository layout

```
lab-6/
├── network_channel.h      the channel interface            (given, do not change)
├── network_channel.cpp    the channel                      YOU WRITE
├── finance.cpp            the financial server              YOU WRITE one loop
├── logging.cpp            the logging server                YOU WRITE one loop
├── file.cpp               the file server                   YOU WRITE one loop
├── client.cpp             the user interface                YOU WRITE three lines
├── thread_pool.h/.cpp     your Lab 5 thread pool           (given, complete)
├── signals.h/.cpp         your Lab 4 signal handling       (given, complete)
├── common.h/.cpp          Request, Response, parsing       (given, complete)
├── tests/                 the checks the autograder runs   (given)
└── Makefile
```

Only the five files marked **YOU WRITE** are collected. The autograder replaces
everything else with its own copy, so editing the headers, `common.cpp`,
`signals.cpp`, `thread_pool.cpp`, the `Makefile` or `tests/` changes nothing
about your score.

**That includes `network_channel.h`, and it has a consequence worth stating
plainly.** If you want a helper function of your own, make it a file-scope
`static` function in `network_channel.cpp`, beside the `send_all` and
`recv_all` you were given. Do **not** declare it inside the class: your own
header would have it, the reference header would not, and your
`network_channel.cpp` would fail to compile during grading — costing every
point on the lab for a change that worked perfectly on your machine.

### 3.3 Build and run

```bash
make
```

The three servers and the client are four separate programs, so you need four
terminals. In the first three:

```bash
./finance -p 8000 -m 100 -t 4
./file    -p 8001 -t 4 .txt .cpp
./logging -p 8002 -f system.log -t 4
```

and in the fourth:

```bash
./client --finance-host=localhost --finance-port=8000 \
         --file-host=localhost    --file-port=8001 \
         --logging-host=localhost --logging-port=8002
```

Those are the default ports, so `./client` on its own does the same thing.
Every program takes `-h` and prints its options.

**ZACH 598 is shared, and so are its port numbers.** A port can be claimed by
one program at a time, for the whole machine — so if a classmate on the same
host is already using 8000, your server will not start:

```
Error starting finance server: bind to port 8000 failed: Address already in use
(another process on this machine is already listening there -- start this
server on a different port with -p)
```

Pick three other numbers above 1024 — say `-p 18000`, `18001`, `18002` — and
pass the matching `--finance-port`, `--file-port` and `--logging-port` to the
client. **`SO_REUSEADDR` does not help here.** It lets you re-bind a port that
a *previous* process of your own left in `TIME_WAIT`, which is what stops
"address already in use" after you restart your own server; it never lets two
live listeners share a port.

A server runs until you stop it with Ctrl+C in its terminal. One Ctrl+C is a
graceful shutdown: it stops accepting and then waits for any connected client
to disconnect, which is why it may appear to hang. A second Ctrl+C exits
immediately.

Note two things about the client that surprise people:

- Choosing **0** from the menu sends `QUIT` to each server and exits. It does
  **not** stop the servers; they keep listening for the next client.
- **Downloading a file writes it into your current directory under the same
  name**, so downloading `notes.txt` overwrites your local `notes.txt`. The
  file server keeps its copies in `storage/`.

### 3.4 Test your work

```bash
make test
```

That runs the same checks the autograder runs, out of `tests/`. Two differences
to know about:

- The autograder links the three servers and the client against a **reference**
  `network_channel.o`, so those four rows are judged on their own file. Run
  locally, everything is your own code, so an unfinished channel fails those
  rows too.
- Both report the same eight rows and the same point values.

`make clean` removes the build output. `make distclean` also removes what
running the programs produces: `storage/`, `system.log`, `signals.log`.

### 3.5 The warnings you start with

A fresh clone builds with **six** warnings and no errors:

```
finance.cpp:…: warning: variable ‘thread_count’ set but not used
file.cpp:…:    warning: variable ‘thread_count’ set but not used
logging.cpp:…: warning: variable ‘thread_count’ set but not used
network_channel.cpp:…: warning: ‘bool send_all(…)’ defined but not used
network_channel.cpp:…: warning: ‘int recv_all(…)’ defined but not used
network_channel.cpp:…: warning: ‘bool split_response(…)’ defined but not used
```

All six clear as you fill in the TODOs — `thread_count` is unused until you
create the thread pool, and the three helpers are unused until you call them.
The last three are a useful signal in their own right: if `send_all` is still
"defined but not used" when you think you are finished, you are calling `send`
directly somewhere. The finished lab builds with **no warnings**.

## 4. Walkthrough

### 4.1 The interface you are implementing

```cpp
class NetworkRequestChannel {
public:
    enum Side {SERVER_SIDE, CLIENT_SIDE};

    // ip == "" on the server side means "listen on every interface"
    NetworkRequestChannel(const std::string& ip, int port, Side side);

    // wraps a descriptor that accept() has just returned
    NetworkRequestChannel(int sockfd);

    ~NetworkRequestChannel();

    Response send_request(const Request& req);   // client side
    Request  receive_request();                  // server side
    void     send_response(const Response& resp);// server side

    int         accept_connection();             // listening side
    std::string get_peer_address() const;
    int         get_socket_fd() const;
};
```

**The two connecting constructors throw `std::runtime_error`; they must not
call `exit`.** Every place that builds a channel already sits inside a
`try`/`catch`, and the difference matters: a client that cannot reach the
finance server should still let you log in and use the other two, and a server
that cannot claim its port should say so and exit with a non-zero status rather
than die in the middle of a library call. Close the socket before you throw, or
you leak the descriptor.

`send_request`, `receive_request` and `send_response` do **not** throw. A
network failure there is ordinary. Report it: `send_request` returns an
unsuccessful `Response` whose `message` says what happened, and
`send_response` prints the reason and returns.

### 4.2 The helpers you are given

At the top of `network_channel.cpp`, already written:

- **`send_all(fd, buf, len)`** — sends exactly `len` bytes, looping, retrying
  on `EINTR`. Returns `false` if the connection failed.
- **`recv_all(fd, buf, len)`** — receives exactly `len` bytes, looping.
  Returns `1`, `0` for end-of-file, or `-1` for an error.
- **`MAX_MESSAGE`** — a ceiling on a declared length. The 4 bytes you read off
  the network are untrusted input; without a ceiling a corrupt header turns
  straight into a multi-gigabyte allocation. Check the length against it before
  you size a buffer.
- **`split_response`** — splits `SUCCESS|BALANCE|DATA|MESSAGE` the way §2.5
  describes.

### 4.3 The life of one request

A deposit, end to end:

1. The client builds `Request(DEPOSIT, user, amount)` and calls
   `send_request`.
2. `send_request` formats `TYPE|USER_ID|AMOUNT|FILENAME|DATA`, sends its length
   as four big-endian bytes, then sends the text.
3. The finance server's handler is sitting in `receive_request`. It reads four
   bytes, learns the length, reads exactly that many, and hands the text to
   `Request::parseRequest`.
4. `handle_client` locks the account, adds the amount, and fills in a
   `Response`.
5. `send_response` formats `SUCCESS|BALANCE|DATA|MESSAGE`, sends its length,
   then sends the text.
6. `send_request`, still waiting, reads the length and then the response, and
   returns it.
7. The client prints `Deposit successful. New balance: …`, and separately asks
   the logging server to record it.

Every arrow in that list is a `send_all` or a `recv_all`.

### 4.4 Running a server on another machine

Nothing in the code is specific to one host. Start a server on one machine,
find its address with `hostname -I`, and point the client at it:

```bash
./client --finance-host=10.0.0.7 --finance-port=8000
```

The client accepts a hostname as well as an address, which is why
`inet_pton` is not enough on its own: a name like `localhost` is not a dotted
quad, so `inet_pton` fails and the code falls back to `gethostbyname`. Note
that `gethostbyname` reports failure through `h_errno`, not `errno`, so
`strerror(errno)` after it prints something unrelated.

## 5. To-do

Point values are listed so you can see where the weight is. Everything is
judged by running your code.

### 5.1 Server-side socket setup (15 points)

In `NetworkRequestChannel`'s `(ip, port, side)` constructor, the
`SERVER_SIDE` branch:

- create the socket,
- set `SO_REUSEADDR`,
- fill in `server_addr` — `AF_INET`, `INADDR_ANY`, and the port in network
  byte order,
- `bind`,
- `listen` with a backlog of **10**.

Throw `std::runtime_error` if any of them fails, and include
`strerror(errno)` so the message says what went wrong. Close the socket first.

### 5.2 Client-side socket setup (15 points)

The `CLIENT_SIDE` branch of the same constructor:

- create the socket,
- fill in `server_addr`,
- turn `ip` into a binary address with `inet_pton`, falling back to
  `gethostbyname` when it is not a dotted quad,
- `connect`.

Throw on failure, here too. Connecting to a port where nothing is listening
fails with `ECONNREFUSED`, and the client is written to carry on without that
server — which only works if you throw rather than exit.

### 5.3 Connection handling (15 points)

- **`accept_connection`** — accept a connection and return the new descriptor.
  Return `-1` on failure and leave `errno` alone; do not print and do not
  throw, for the reasons in §2.7.
- **The `(int fd)` constructor** — record who is on the other end, with
  `getpeername`, into `peer_ip` and `peer_port`. Use `inet_ntop`, not
  `inet_ntoa`: `inet_ntoa` returns a pointer into a single buffer shared by the
  whole process, and several handler threads are naming their clients at once.
  If `getpeername` fails, set `peer_ip` to something readable rather than
  leaving it empty.
- **The destructor** — close the socket. Every accepted connection gets a
  channel, so a channel that does not close leaks one descriptor per client,
  and a server that runs long enough then fails to accept anything at all.

### 5.4 Request/response protocol (15 points)

- **`send_request`** — the length header is already computed for you. Send it,
  send the request, then read the response: four bytes of length, `ntohl`,
  check against `MAX_MESSAGE`, read exactly that many bytes, and
  `split_response`. Return an unsuccessful `Response` for each way it can fail,
  and keep end-of-file, error and success apart.
- **`receive_request`** — the same in reverse, ending at
  `Request::parseRequest`. Return `Request(QUIT)` when the connection ends.
- **`send_response`** — compute the length header, send it, send the text,
  report a failure rather than assuming success.

### 5.5 The three servers (10 points each)

`finance.cpp`, `logging.cpp` and `file.cpp` each have the same hole in `main`,
and the three fixes are nearly identical:

- create a listening `NetworkRequestChannel` on `port`,
- create a `ThreadPool` with `thread_count` threads,
- in the accept loop: accept a connection, and **hand it to the pool** so the
  loop is free to take the next one,
- treat `-1` with `errno == EINTR` as "go round again" (§2.7), and report any
  other error without ending the loop.

Everything else in those files — the request handling, the locking, the
shutdown — is already written.

### 5.6 The client (10 points)

In `client.cpp`, create the three `NetworkRequestChannel`s, one per server,
from the host and port already parsed out of the command line. Each one is
already inside a `try`/`catch` that reports the failure and leaves that channel
null, and the menu already checks for null before using it — so a client whose
channels throw properly still runs with one server missing, and that is part of
what is graded.

## 6. Deliverables

Push `network_channel.cpp`, `finance.cpp`, `logging.cpp`, `file.cpp` and
`client.cpp` to the repository the accept link created:

```bash
git add network_channel.cpp finance.cpp logging.cpp file.cpp client.cpp
git commit -m "Lab 6"
git push
```

Every push is graded, and the last push before the deadline is the one that
counts. Nothing else needs to be submitted.

### 6.1 Mistakes that cost points

| Symptom | Cause |
|---|---|
| A small upload works; a large one is silently truncated and still reports success | one `recv` instead of a loop (§2.4) |
| An uploaded `.cpp` file is cut off at its first logical-or operator | splitting on every delimiter instead of the first four (§2.5) |
| The second client to connect waits for ever | the accept loop calls `handle_client` itself instead of handing it to the pool (§2.6) |
| The client exits as soon as one server is missing | the constructor calls `exit` instead of throwing (§4.1) |
| `Error accepting connection:` repeats forever, or Ctrl+C does nothing | `EINTR` from `accept` treated as a real error, or `errno` read after something else overwrote it (§2.7) |
| The server stops accepting after a few hundred clients | the destructor does not close the socket (§5.3) |
| `send_request` reports success after the server was stopped | `recv_all` returning 0 treated as data (§2.4) |
| Two clients see each other's peer address in the log | `inet_ntoa` instead of `inet_ntop` (§5.3) |
| `bind failed: Address already in use` and `SO_REUSEADDR` did not help | another live listener has the port; pick a different one (§3.3) |

## 7. Getting help

Ask on **Discord**. Office hours are on Canvas. The Canvas inbox is not
monitored.

If you report a problem, say what you ran, what you expected and what happened,
and paste the output rather than describing it.

## Revision history

| Date | Change |
|---|---|
| Tue Nov 3, 2026 | First published for Fall 2026. Rewritten from the Summer 2026 document: the channel now throws instead of exiting, `send_all`/`recv_all` are given, and the byte-stream, delimiter and signal behaviour are documented. |
