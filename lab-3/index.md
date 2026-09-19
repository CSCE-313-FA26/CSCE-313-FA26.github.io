---
layout: lab
title: "Lab 3 — Interprocess Communication"
lab_number: 3
lab_title: "Interprocess Communication"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
instructor: "David Kebo Houngninou"
released: "Tuesday, September 22, 2026, 9:00 AM CT"
due: "Monday, October 5, 2026, 11:59 PM CT"
released_short: "Tue Sep 22, 2026"
due_short: "Mon Oct 5, 2026, 11:59 PM CT"
description: "Replace the hidden channel from Lab 2 with your own, built twice: once on unnamed pipes and once on named pipes (FIFOs)."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Objectives

By the end of this lab you will be able to:

1. Create unnamed pipes with `pipe()` and use them to connect a parent to its children.
2. Redirect a child's standard input and output onto pipe ends with `dup2()`, so the
   program it `exec`s talks through the pipe without knowing it.
3. Create and open named pipes with `mkfifo()` and `open()`.
4. Explain why every unused pipe end must be closed, and show what goes wrong when one is not.
5. Send fixed-size messages with `read()` and `write()`, and detect when one fails.

In Lab 2 the `RequestChannel` was handed to you, its implementation hidden. **In this
lab you write it** — twice.

## 2. Background

### 2.1 What changed since Lab 2

The banking system is the same: one client, three servers, the same menu and the
same log. What changed is underneath it.

| | Lab 2 | Lab 3 |
| --- | --- | --- |
| The channel | given, hidden in LLVM IR | **yours**, in `channel.cpp` |
| How it is built | one `RequestChannel` class | an abstract `RequestChannel` and two concrete ones: `PipeChannel`, `FIFOChannel` |
| Choosing the kind | — | the client asks first: `1` for pipes, `2` for FIFOs |
| Strings in messages | `std::string` | fixed `char` arrays, so a whole `Request` is one block of bytes |
| A `QUIT` request | server exits without replying | server **replies**, then exits |
| Log file flag | `./logging -f <file>` | `./logging -n <file>` — `-f` now means *use FIFOs* |
| Process-information printing | Task 2 | **gone** — no `print_process_info` in this lab |

You no longer need `clang`: there is no `.ll` file. Plain `g++` builds everything.

### 2.2 Unnamed pipes

`pipe(fds)` gives you two file descriptors: `fds[0]` to read and `fds[1]` to write.
Bytes written into one come out of the other, in order.

A pipe carries data **one way only**. For a request to go one way and a response to
come back, each connection needs **two pipes**. Three servers means six pipes.

A pipe has no name. The only way for another process to use it is to **inherit** it —
so the pipes must exist *before* the `fork()`. Both processes then hold all four
ends, and each closes the two it does not use.

<figure class="diagram diagram--wide">
<div class="diagram-scroll" tabindex="0" role="group" aria-label="Two-pipe connection diagram, scrollable">
<svg viewBox="0 0 760 380" role="img" aria-labelledby="f1-title" xmlns="http://www.w3.org/2000/svg">
  <title id="f1-title">One client-server connection built from two unnamed pipes</title>
  <desc>The client is on the left and a server on the right. Pipe 1, along the top, carries requests: the client writes into pipe1 index 1 and the server reads from pipe1 index 0, which it has made its standard input. Pipe 2, along the bottom, carries responses: the server writes into pipe2 index 1, its standard output, and the client reads from pipe2 index 0. The client closes pipe1 index 0 and pipe2 index 1. The server closes pipe1 index 1 and pipe2 index 0. Each process keeps exactly one end of each pipe.</desc>
  <defs>
    <marker id="f1arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" class="d-arrow"/>
    </marker>
  </defs>

  <rect x="30" y="125" width="170" height="140" rx="8" class="d-box--brand"/>
  <text x="115" y="160" text-anchor="middle" class="d-title">client</text>
  <text x="115" y="182" text-anchor="middle" class="d-text--sm">creates both pipes,</text>
  <text x="115" y="198" text-anchor="middle" class="d-text--sm">then forks</text>
  <text x="115" y="232" text-anchor="middle" class="d-text--sm">closes</text>
  <text x="115" y="250" text-anchor="middle" class="d-text--mono">pipe1[0], pipe2[1]</text>

  <rect x="560" y="125" width="170" height="140" rx="8" class="d-box--busy"/>
  <text x="645" y="160" text-anchor="middle" class="d-title">server</text>
  <text x="645" y="182" text-anchor="middle" class="d-text--sm">after exec, sees only</text>
  <text x="645" y="198" text-anchor="middle" class="d-text--sm">stdin and stdout</text>
  <text x="645" y="232" text-anchor="middle" class="d-text--sm">closes</text>
  <text x="645" y="250" text-anchor="middle" class="d-text--mono">pipe1[1], pipe2[0]</text>

  <rect x="300" y="40" width="160" height="46" rx="23" class="d-box--note"/>
  <text x="380" y="68" text-anchor="middle" class="d-title">pipe 1</text>
  <path d="M 115 125 L 115 63 L 296 63" class="d-edge" marker-end="url(#f1arrow)"/>
  <path d="M 460 63 L 645 63 L 645 121" class="d-edge" marker-end="url(#f1arrow)"/>
  <text x="205" y="54" text-anchor="middle" class="d-text--mono">write(pipe1[1])</text>
  <text x="552" y="54" text-anchor="middle" class="d-text--mono">read(pipe1[0])</text>
  <text x="552" y="100" text-anchor="middle" class="d-text--sm">dup2 onto stdin (0)</text>
  <text x="380" y="106" text-anchor="middle" class="d-text--sm">requests</text>

  <rect x="300" y="294" width="160" height="46" rx="23" class="d-box--note"/>
  <text x="380" y="322" text-anchor="middle" class="d-title">pipe 2</text>
  <path d="M 645 265 L 645 317 L 464 317" class="d-edge" marker-end="url(#f1arrow)"/>
  <path d="M 300 317 L 115 317 L 115 269" class="d-edge" marker-end="url(#f1arrow)"/>
  <text x="552" y="338" text-anchor="middle" class="d-text--mono">write(pipe2[1])</text>
  <text x="552" y="296" text-anchor="middle" class="d-text--sm">dup2 onto stdout (1)</text>
  <text x="205" y="338" text-anchor="middle" class="d-text--mono">read(pipe2[0])</text>
  <text x="380" y="284" text-anchor="middle" class="d-text--sm">responses</text>

</svg>
</div>
<figcaption>Figure 1 — One connection is two pipes, one each way. Each process keeps exactly one end of each pipe and closes the other. The server never learns the descriptor numbers: it was handed the pipes as its standard input and output.</figcaption>
</figure>

Reading a pipe **blocks** until there is data. It returns `0` — end of file — only
when **every** write end of that pipe is closed, in **every** process that holds one.

### 2.3 Named pipes (FIFOs)

`mkfifo(name, 0600)` makes a pipe that has a **name in the filesystem**. Any process
that knows the name can `open()` it, related or not, and it stays on disk until
someone removes it.

Opening a FIFO **blocks until the other end is opened too**: an open for reading waits
for a writer, and an open for writing waits for a reader. That rule is what makes
FIFOs easy to deadlock — see [section 4.3](#43-fifo-mode).

Each connection again needs two FIFOs, one each way. Their names are given to you
in the `FIFOChannel` constructor: `fifo_<name>1` and `fifo_<name>2`, created in the
directory you run the client from.

### 2.4 Why closing unused ends is not optional

Every server in this lab stops when it reads end-of-file. It can only ever read
end-of-file if **no process anywhere still holds a write end of its input pipe.**

Pipe descriptors are inherited by every child forked after they were created. So if
the finance server's child keeps the write end of the *logging* server's pipe, and
the client dies, the logging server waits forever for a message from a process that
will never send one.

We measured this on the previous reference solution, which forgot to close them:
killing the client left **all three servers running as orphans**. Closing every
unused end, all three had exited on their own two seconds later. The autograder runs
exactly that experiment on your client — see [section 5.4](#54-task-4--the-client-15-points).

## 3. Environment setup

### 3.1 Accept the assignment

1. Sign in to [classroom50.org](https://classroom50.org/) with your GitHub account.
2. Accept Lab 3:
   <https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/lab-3/accept>.
   Your repository is created for you.
3. Clone it:

```bash
git clone https://github.com/CSCE-313-FA26/<your-lab-3-repository>.git
cd <your-lab-3-repository>
```

<aside class="callout callout--note" aria-labelledby="roster-heading">
<h2 class="callout__title" id="roster-heading">If accepting fails</h2>
<p>If your name is missing from the roster, or you signed in with the wrong GitHub
account, contact the instructor or a TA — do not create a second account.</p>
</aside>

### 3.2 Repository layout

| Path | What it is | Yours to change? |
| --- | --- | --- |
| `channel.cpp` | `RequestChannel`, `PipeChannel`, `FIFOChannel` — all `TODO`s | **Yes** |
| `client.cpp` | Creates the pipes, starts the servers, opens the channels | **Yes** |
| `finance.cpp`, `logging.cpp`, `file.cpp` | The three servers — each needs its channel | **Yes**, the channel only |
| `channel.h` | The three classes' declarations | No |
| `common.h` | `Request`, `Response`, `RequestType`, `IPCType` | No |
| `Makefile` | Builds all four programs | No |
| `tests/` | The unit tests, and `grade.py` — the same checks the autograder runs | No |
| `storage/example_execution.txt` | A complete correct session | — |
| `storage/example.log` | The log that session produced | — |

### 3.3 Build and run

```bash
make
./client
```

The first thing the client asks is which kind of channel to use:

```text
Choose IPC type, 1 for PIPE, 2 for FIFO:
```

After that it is the Lab 2 program: the maximum account number, the log file name,
the allowed extensions, then the menu. `storage/example_execution.txt` is a whole
session, recorded from the reference solution in pipe mode, and `storage/example.log`
is the log it wrote. Your program should produce the same log in **either** mode.

### 3.4 Test your work

```bash
make test
```

That builds everything and runs `tests/grade.py`: every unit test in `tests/`, then
complete sessions in both modes, scored exactly as the autograder scores them, out
of 100. Run it often. It is much faster than pushing and waiting.

The one difference: run locally, every part uses **your** code, so a broken channel
fails the client and server checks too. The autograder runs your client against
reference servers, and your servers against a reference client, so each is graded
on its own. Fix your channel first and the rest follows.

## 4. Walkthrough

### 4.1 What a message is

`Request` and `Response` now hold only numbers and fixed-size `char` arrays. That
means a whole message is one solid block of bytes, and sending it is a single call:

```cpp
cwrite((void*)&req, sizeof(Request));    // the entire Request, as raw bytes
```

and receiving one is the matching `cread` into a `Request` of your own. There is no
parsing: the struct goes in one end and comes out the other.

A read or write that moves **fewer bytes than the whole struct** has failed, even if
it did not return `-1`. A read that returns `0` means end-of-file — the other side
is gone.

A `Request` is 1296 bytes, under the 4096 bytes Linux guarantees a pipe writes in one
piece, so each message goes across whole.

### 4.2 Pipe mode

The client builds all six pipes **before** the first `fork()`, inside the
`if (ipc == PIPE)` block the starter already has. In each child, before `exec`:

- `dup2` the read end of that server's **request** pipe onto **standard input**,
- `dup2` the write end of its **response** pipe onto **standard output**,
- then **close every pipe descriptor** the child inherited — including the other
  servers' pipes. After `dup2` the child no longer needs the originals either.

After the `exec`, the server knows nothing about pipes. It just reads requests from
`STDIN_FILENO` and writes responses to `STDOUT_FILENO`:

```cpp
channel = new PipeChannel(STDIN_FILENO, STDOUT_FILENO);
```

Back in the parent, once all three servers are started, close the child-side ends
(each server's request read end and response write end), then make one
`PipeChannel` per server from the two ends the client keeps.

<aside class="callout callout--warn" aria-labelledby="stdout-heading">
<h2 class="callout__title" id="stdout-heading">In pipe mode, a server's standard output IS the pipe</h2>
<p>Anything a server prints with <code>cout</code> or <code>printf</code> goes down the
response pipe and lands in the middle of the client's next <code>Response</code>. Do
not add debugging prints to <code>stdout</code> in a server. Use
<code>cerr</code> — standard error is not redirected.</p>
</aside>

### 4.3 FIFO mode

The client does not create anything. Each side makes its own `FIFOChannel` with the
same name, and the channel's constructor creates and opens the two FIFOs:

| | client side | server side |
| --- | --- | --- |
| finance | `FIFOChannel("finance", CLIENT_SIDE)` | `FIFOChannel("finance", SERVER_SIDE)` |
| logging | `FIFOChannel("logging", CLIENT_SIDE)` | `FIFOChannel("logging", SERVER_SIDE)` |
| file | `FIFOChannel("file", CLIENT_SIDE)` | `FIFOChannel("file", SERVER_SIDE)` |

**Use exactly these names.** Your client is graded against reference servers that use
them, and your servers against a reference client.

<aside class="callout callout--warn" aria-labelledby="order-heading">
<h2 class="callout__title" id="order-heading">Open the two FIFOs in the same order on both sides</h2>
<p>Each <code>open()</code> waits for the other end. If the server opens
<code>fifo_finance1</code> first while the client opens <code>fifo_finance2</code>
first, each waits for the other forever and nothing is printed at all. We tested
exactly this: reversing the order on one side hangs every FIFO session.</p>
<p>Which FIFO carries requests and which carries responses is your choice. The
<strong>order</strong> is not: open <code>pipe1</code> first on both sides, then
<code>pipe2</code>.</p>
</aside>

### 4.4 Limits worth knowing

- **Uploads larger than 1023 bytes are cut short.** `data` is a 1024-byte array, so
  a bigger file is truncated and the client still prints `File upload successful`.
  Unlike Lab 2 the file server survives it. Test with small files.
- **Only one FIFO-mode client per directory at a time.** The FIFO names are fixed,
  so two FIFO clients started in the same directory would share FIFOs. Pipe mode has
  no such limit.
- **A crashed run can leave `fifo_*` files behind.** `make distclean` removes them.

## 5. To-do

The points match the autograder. Every task is graded by **running** your code.

### 5.1 Task 1 — RequestChannel (25 points)

In `channel.cpp`. Each method is one unit test in `tests/`, worth 5 points.

| Method | Must do | On failure |
| --- | --- | --- |
| `cread(buf, n)` | `read()` up to `n` bytes from `rfd` | return what `read()` returned: `0` at end-of-file, `-1` on error |
| `cwrite(buf, n)` | `write()` `n` bytes to `wfd` | return what `write()` returned |
| `send_request(req)` | `cwrite` the whole `Request`, then `cread` a whole `Response` | return a `Response` whose `success` is `false` |
| `receive_request()` | `cread` a whole `Request` | return `Request(FAILURE)` — for an error **and** for end-of-file |
| `send_response(resp)` | `cwrite` the whole `Response` | return `false` |

Use `cread` and `cwrite` inside the other three — never `read` or `write` directly.

<aside class="callout callout--note" aria-labelledby="failure-heading">
<h2 class="callout__title" id="failure-heading">Why end-of-file must be FAILURE</h2>
<p>A default-constructed <code>Request</code> has type <code>QUIT</code>. Return one
on end-of-file and a server treats a vanished client as a polite goodbye. The
servers' loops already stop cleanly on <code>FAILURE</code>, and your servers rely
on that to exit when the client dies.</p>
</aside>

### 5.2 Task 2 — PipeChannel (25 points)

- The constructor stores the two descriptors it is given.
- The destructor closes both. After it runs, neither may still be open.

Eight checks in `tests/test_pipechannel.cpp`, scored separately. The check that a bad
descriptor makes `send_request` fail only earns its points once `send_request` also
**works** on a good one.

### 5.3 Task 3 — FIFOChannel (25 points)

- `open_pipe(name, mode)` creates the FIFO with `mkfifo(name, 0600)` — it may already
  exist, because the other side can get there first; that is fine — then `open`s it
  with `mode` and returns the descriptor. If the `open` fails, print why and exit.
- The constructor opens the two FIFOs, one for reading and one for writing, in the
  **same order on both sides** — see [section 4.3](#43-fifo-mode).
- The destructor closes both descriptors **and removes both FIFOs** from the
  filesystem.

Eight checks in `tests/test_fifochannel.cpp`, scored separately.

### 5.4 Task 4 — The client (15 points)

In `client.cpp`: create the six pipes, wire each child and close its unused ends,
close the parent's, and create the channels for whichever mode was chosen. At the
end, `delete` all three channels.

| Check | Points |
| --- | --- |
| A complete pipe-mode session produces the right output and log | 3 |
| …and afterwards every server has exited and nothing is left behind | 2 |
| A complete FIFO-mode session produces the right output and log | 3 |
| …and afterwards no server and no `fifo_*` file is left behind | 2 |
| **Unused pipe ends are closed**: kill the client mid-session, and all three servers must exit on their own within 4 seconds | 5 |

The last check is the experiment from [section 2.4](#24-why-closing-unused-ends-is-not-optional).
It first confirms three servers are running and a user is logged in, so a client that
never starts its servers cannot pass it by default.

### 5.5 Task 5 — The servers (10 points)

In each of `finance.cpp`, `logging.cpp` and `file.cpp`, create the channel for the
mode the server was started with:

- pipe mode: `new PipeChannel(STDIN_FILENO, STDOUT_FILENO)`
- FIFO mode: `new FIFOChannel("<finance | logging | file>", RequestChannel::SERVER_SIDE)`

| Check | Points |
| --- | --- |
| All three servers answer correctly in a complete pipe-mode session | 5 |
| All three servers answer correctly in a complete FIFO-mode session | 5 |

## 6. Deliverables

Commit and push your work:

```bash
git add channel.cpp client.cpp finance.cpp logging.cpp file.cpp
git commit -m "lab 3"
git push
```

Only those five files are graded. `channel.h`, `common.h`, the `Makefile` and `tests/`
are replaced with the reference copies before grading, so changing them has no
effect on your score. Do not commit the built programs, log files, or `fifo_*` files —
`.gitignore` already excludes them.

The autograder runs on every push. Push as often as you like and read the result.

### 6.1 Mistakes that cost points

| Symptom | Cause |
| --- | --- |
| Every FIFO session hangs, printing nothing | The two sides open the FIFOs in different orders (section 4.3) |
| Servers keep running after the client is killed | A pipe end was left open — often another server's, inherited by a later child |
| `Response` fields hold garbage in pipe mode | A server printed to standard output, which is the response pipe |
| `fifo_*` files left behind after a clean exit | The destructor does not remove the FIFOs, or the client never `delete`s its channels |
| A server exits the instant it starts, in pipe mode | Its standard input was not redirected — it read end-of-file straight away |
| `receive_request` test fails on end-of-file | `0` from `cread` must become `FAILURE`, not a default `Request` |
| Works locally, fails a FIFO check in the grader | Your channel names differ from `finance`, `logging`, `file` |

## 7. Getting help

Ask on **Discord**. Bring the exact command you ran and the exact output, not a
description of it. The Canvas inbox is not monitored.

Office hours and TA contact details are in the syllabus.

## Revision history

| Date | Change |
| --- | --- |
| 2026-09-19 | Migrated from the Google Doc to this page. Due date corrected from June 28 (a leftover from a summer offering) to Monday, October 5. GitHub Classroom replaced by classroom50. The unit tests, previously hidden, now ship in `tests/` and run with `make test`. Removed claims that the client prints process information and that the tests must stay secret. Corrected the `FIFOChannel` task, which described a pipe constructor taking descriptors. Added the IPC-choice prompt, the QUIT reply, the `-n` log-file flag, the FIFO names and open order, the standard-output warning, the upload limit, and the orphaned-server experiment. The missing `storage/example_execution.txt` and `storage/example.log` were recorded from a real run and added to the starter. The figure was redrawn with the client and server named and each process's closed ends shown. |
