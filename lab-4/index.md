---
layout: lab
title: "Lab 4 — Signals"
lab_number: 4
lab_title: "Signals"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
instructor: "David Kebo Houngninou"
released: "Tuesday, October 6, 2026, 9:00 AM CT"
due: "Monday, October 19, 2026, 11:59 PM CT"
released_short: "Tue Oct 6, 2026"
due_short: "Mon Oct 19, 2026, 11:59 PM CT"
description: "Make the banking system answer asynchronous events: handle Ctrl+C, time operations out, notice when a server dies, and protect a transaction from being interrupted."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Objectives

By the end of this lab you will be able to:

- Install signal handlers with `sigaction()`, and say what `SA_RESTART` changes.
- Write a handler that is **async-signal-safe** — and explain why `printf` is not.
- Use `std::atomic` flags to carry information out of a handler.
- Put a time limit on an operation with `alarm()` and `SIGALRM`, and cancel it.
- Notice a child's death with `SIGCHLD` and `waitpid(..., WNOHANG)`.
- Protect a critical section by **blocking** a signal with `sigprocmask()`, and
  explain why blocking is not the same as ignoring.

## 2. Background

### 2.1 What changed since Lab 3

The banking system is the same: one client, three servers, the same menu plus one
new entry. The channel is given back to you — your Lab 3 work is done.

| | Lab 3 | Lab 4 |
| --- | --- | --- |
| The channel | you wrote it, twice | given, FIFO-based, in `channel.cpp` |
| New files | — | `signals.h` and `signals.cpp` |
| What you write | the channel and the client's plumbing | `signals.cpp` and two small changes in `client.cpp` |
| Menu | 7 operations | plus **8. Server Status** |
| Ctrl+C | kills the client | first press asks for a clean shutdown, second forces it |
| A slow server | the client waits for ever | the operation times out and can be retried |
| A dead server | nothing notices | `SIGCHLD` marks it inactive in the registry |
| File server binary | `fileserver` | **`file`** |

### 2.2 What a signal is

A signal is a notification the kernel delivers to a process: `SIGINT` from
Ctrl+C, `SIGALRM` when an `alarm()` expires, `SIGCHLD` when a child exits.
For each signal a process either lets the default happen (for `SIGINT`, die),
ignores it, or runs a **handler** function.

Delivery interrupts whatever the process was doing, runs the handler, and
resumes. That is the whole difficulty: your handler can start between any two
machine instructions of your own program.

### 2.3 What a handler may do

Because a handler can interrupt the main program anywhere, it may call only
functions that are safe to re-enter — **async-signal-safe** functions. POSIX
publishes the list. The ones you need are on it: `write`, `open`, `close`,
`waitpid`, `_exit`, and the `sig*` family.

These are **not** on it, and must not appear in a handler:

| Not safe in a handler | Why |
| --- | --- |
| `printf`, `std::cout` | buffered, and the buffer may be half-updated |
| `std::string`, `std::stringstream`, `new` | they allocate; `malloc` may be mid-update |
| `localtime`, `strftime` | shared internal state |
| `exit` | runs `atexit` handlers and flushes streams; use `_exit` |

Reading and writing an `std::atomic` is safe, which is why the flags in
`signals.h` are atomic rather than plain `bool`.

<aside class="callout callout--warn" aria-labelledby="log-heading">
<h2 class="callout__title" id="log-heading">The logger you are given is not handler-safe</h2>
<p><code>log_signal_event()</code> in <code>signals.cpp</code> is written for you,
and it uses <code>localtime</code>, <code>strftime</code> and
<code>std::string</code> — none of them async-signal-safe. That is fine from
ordinary code, which is where most of the calls are, and wrong from inside a
handler.</p>
<p>So in your three handlers, report the event with <code>write()</code> instead,
to standard output or straight to a file descriptor. The grader accepts either —
it only checks that the handler recorded something — but the reference
implementation uses <code>write()</code> only, and so should yours.</p>
</aside>

### 2.4 Blocking is not ignoring

`sigprocmask(SIG_BLOCK, ...)` adds a signal to the process's mask. A blocked
signal is **held, not lost**: it stays pending, and it is delivered the moment
you unblock it. Ignoring (`SIG_IGN`) throws it away.

That is what makes blocking the right tool around a transaction. The client
blocks `SIGINT` while it talks to a server, so a Ctrl+C arriving mid-exchange
cannot run the handler and set the shutdown flag halfway through. The press is
not lost — the handler runs as soon as the transaction finishes and the client
unblocks.

One consequence worth knowing: ordinary signals do **not** queue. Mash Ctrl+C
five times while a transaction holds `SIGINT` blocked and exactly one `SIGINT`
is pending when you unblock, so the handler runs once. Your "second press forces
an exit" path therefore needs a second press *after* the first was delivered,
not during the same blocked window.

### 2.5 Ctrl+C reaches the whole foreground group

The terminal sends `SIGINT` to **every process in the foreground process
group** — which, by default, is the client *and* the three servers it forked.
The servers install no handlers, so they would all die on the first press, and
the client's shutdown would then be writing `QUIT` into FIFOs nobody is reading.

Two lines of given code prevent that, and both are worth understanding because
they are the kind of thing that is invisible until it bites:

- each child calls `setpgid(0, 0)` before `exec`, putting itself in its own
  process group, so Ctrl+C reaches only the client;
- the client sets `SIGPIPE` to `SIG_IGN`, because writing to a FIFO whose reader
  has exited raises `SIGPIPE`, and its default action would kill the client in
  the middle of its own shutdown, silently. Ignored, the `write` simply fails
  and the channel reports it.

So the sequence you should see is: one Ctrl+C, the client finishes what it is
doing, sends `QUIT` to all three servers, and prints `Shutdown complete.`

## 3. Environment setup

### 3.1 Accept the assignment

1. Sign in to [classroom50.org](https://classroom50.org/) with your GitHub account.
2. Accept Lab 4:
   <https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/lab-4/accept>.
   Your repository is created for you.
3. Clone it:

```bash
git clone https://github.com/CSCE-313-FA26/<your-lab-4-repository>.git
cd <your-lab-4-repository>
```

### 3.2 Repository layout

| Path | What it is | Yours to change? |
| --- | --- | --- |
| `signals.cpp` | the handlers, the mask, the timeout — most of the lab | Yes |
| `client.cpp` | register the servers; block around each transaction | Yes, the marked spots |
| `signals.h` | the `SignalHandling` namespace: flags, declarations, `execute_with_timeout` | No |
| `finance.cpp`, `logging.cpp`, `file.cpp` | the three servers, complete | No |
| `channel.cpp`, `channel.h`, `common.*` | the channel from Lab 3, given back | No |
| `Makefile` | builds `client`, `finance`, `logging`, `file` | No |
| `tests/` | the unit tests, and `grade.py` — the same checks the autograder runs | No |

### 3.3 Build and run

```bash
make
./client
```

<aside class="callout callout--note" aria-labelledby="link-heading">
<h2 class="callout__title" id="link-heading">The first <code>make</code> fails, and that is the first task</h2>
<p><code>signals.h</code> declares the three flags <code>extern</code>; nothing
defines them yet. So a fresh clone stops at the linker, naming whichever flag it
reaches first:</p>
<p><code>undefined reference to `SignalHandling::timeout_occurred'</code></p>
<p>Define all three at the top of <code>signals.cpp</code> (task 5.1) and the
build goes through. Until task 5.5 is done you will also see
<code>warning: unused variable ‘server’</code> from the empty loop in
<code>sigchld_handler</code>; it goes away when you use the loop variable.</p>
</aside>

The client asks for the maximum account number, a log file name, and the allowed
file extensions, then shows the menu. Menu item **8** prints the server registry.

### 3.4 Test your work

```bash
make test
```

That builds everything and runs `tests/grade.py`: the unit tests for
`signals.cpp`, then a whole client session, scored exactly as the autograder
scores it, out of 100. Run it often.

The one difference: run locally, every part is your code, so a broken
`signals.cpp` fails the two `client.cpp` rows as well. The autograder links your
client against a reference `signals.o`, so there each file is judged on its own.

## 4. Walkthrough

### 4.1 How one transaction is timed

The client already wraps every operation in two layers, both given to you:

```cpp
bool success = execute_with_timeout([&]() { /* send request, read response */ }, 30);
```

`execute_with_timeout` (in `signals.h`) clears `timeout_occurred`, calls
`alarm(seconds)`, runs the operation, cancels the alarm, and reports failure if
the flag was set meanwhile. `retry_operation` then offers a retry.

None of that works until `SIGALRM` has a handler that sets `timeout_occurred`,
and `alarm()` is armed and cancelled by your `wait_with_timeout` and
`cancel_timeout`.

### 4.2 The time limits already in the client

| Operation | Limit |
| --- | --- |
| Login, logout | 10 s |
| Deposit, withdraw | 30 s |
| View balance | 15 s |
| Upload, download | 60 s |
| `QUIT` to each server at shutdown | 3 s |

### 4.3 The server registry

`register_server(pid, name)`, `is_server_active(name)` and
`print_server_status()` are written for you, over a
`vector<ServerProcess>`. Your part is at the two ends: `client.cpp` calls
`register_server` after each `fork()`, and your `SIGCHLD` handler finds the pid
in that vector and clears its `active` flag.

`SIGCHLD` arrives once for any number of dead children, so reap in a loop:

```cpp
while ((pid = waitpid(-1, &status, WNOHANG)) > 0) { /* ... */ }
```

`WNOHANG` is what keeps the handler from blocking when nothing is left to reap.

### 4.4 Limits worth knowing

- **A timed-out operation is not undone.** The servers finish whatever they have
  received; the timeout only ends the client's waiting. So a deposit that reports
  a timeout can still show up in your balance and in the log. There is no
  rollback, and you are not asked to write one.
- **A handler runs in the client only.** The servers install nothing; killing a
  server is noticed through `SIGCHLD`, not inside the server.
- Run-time output — `signals.log`, your log file, `*_attributes.txt`, `fifo_*`,
  `storage/` — is ignored by `.gitignore`. `make clean` removes it.

## 5. To-do

The points match the autograder. Everything is graded by running your code.

### 5.1 The atomic flags (5 points)

At the top of `signals.cpp`, define the three variables `signals.h` declares:
`shutdown_requested` and `timeout_occurred` as `std::atomic<bool>` starting
`false`, and `child_exited` as `std::atomic<int>` starting `0`.

### 5.2 Install the handlers (15 points)

In `setup_handlers()`, install all three with `sigaction()`:

| Signal | Handler | Flags |
| --- | --- | --- |
| `SIGINT` | `sigint_handler` | none |
| `SIGALRM` | `sigalrm_handler` | none |
| `SIGCHLD` | `sigchld_handler` | `SA_RESTART` |

`SA_RESTART` matters: without it, a child exiting while the client sits in
`read()` makes that `read()` fail with `EINTR`. Check `sigaction`'s return value
and `perror()` on failure.

### 5.3 `SIGINT` — two-stage shutdown (10 points)

First press: set `shutdown_requested` and report it, so the menu loop winds down
after the current operation. Second press: force the process to exit
immediately. Use `write()` for the message and `_exit()` for the exit.

### 5.4 `SIGALRM` — mark the timeout (10 points)

Set `timeout_occurred` and record the event. Nothing else: the waiting code
reads the flag and decides what to do.

### 5.5 `SIGCHLD` — update the registry (10 points)

Reap with `waitpid(-1, &status, WNOHANG)` in a loop. For each pid, count it in
`child_exited`, find it in `server_processes`, clear `active`, and record which
server it was.

### 5.6 Block and unblock (20 points)

`block_signals()` — 10 points — builds a set with `sigemptyset` and
`sigaddset(&set, SIGINT)` and applies it with
`sigprocmask(SIG_BLOCK, &set, NULL)`. `unblock_signals()` — 10 points — does the
same with `SIG_UNBLOCK`. Check the return value and `perror()` on failure.

### 5.7 Timeouts (15 points)

`wait_with_timeout(seconds)` — 10 points — clears `timeout_occurred` and arms
`alarm(seconds)`. Clearing it first matters: a leftover `true` makes the next
operation look like it already timed out. `cancel_timeout()` — 5 points — cancels
a pending alarm with `alarm(0)`.

### 5.8 Register the servers (5 points)

In `client.cpp`, after each `fork()`, the **parent** calls
`register_server(pid, name)` with the names `finance`, `logging` and `file`.
Menu item 8 should then list all three as `ACTIVE`.

### 5.9 Block around every transaction (10 points)

In `client.cpp`, each of the seven operations is marked with a pair of TODOs.
Call `block_signals()` before the operation and `unblock_signals()` after it, so
a Ctrl+C mid-transaction is held until the exchange is finished.

## 6. Deliverables

Commit and push your work:

```bash
git add signals.cpp client.cpp
git commit -m "lab 4"
git push
```

Only those two files are graded. `signals.h`, the servers, the channel, the
`Makefile` and `tests/` are replaced with the reference copies before grading, so
changing them has no effect on your score. Do not commit the built programs or
the run-time output — `.gitignore` already excludes them.

The autograder runs on every push. Push as often as you like and read the result.

### 6.1 Mistakes that cost points

| Symptom | Cause |
| --- | --- |
| `undefined reference to SignalHandling::...` | The flags are not defined yet — task 5.1 |
| Ctrl+C kills the client outright | No `SIGINT` handler installed, so the default action still applies |
| The second Ctrl+C does nothing | The handler must force an exit when the flag is already set |
| Every operation reports a timeout immediately | `wait_with_timeout` did not clear `timeout_occurred` first |
| A dead server still shows `ACTIVE` | The `SIGCHLD` handler does not match the pid in `server_processes`, or the client never registered it |
| The client hangs after a server dies | `waitpid` without `WNOHANG`, or no loop |
| An operation fails with `EINTR` when a server exits | `SA_RESTART` missing on the `SIGCHLD` handler |
| Output from a handler appears garbled or doubled | `printf`/`cout` in a handler — use `write()` |
| The client vanishes during shutdown with no message | A write to a server that already exited; the client ignores `SIGPIPE` for this reason, so check you have not re-enabled it |
| Mashing Ctrl+C during a transaction only shuts down once | Signals do not queue: one `SIGINT` is pending however many times you press (section 2.4) |

## 7. Getting help

Ask on Discord. Bring the exact command you ran and the exact output, not a
description of it. The Canvas inbox is not monitored.

Office hours and TA contact details are in the syllabus.

## Revision history

| Date | Change |
| --- | --- |
| 2026-10-05 | Migrated from the Google Doc to this page. Due date corrected from July 12 (a leftover from a summer offering) to Monday, October 19. GitHub Classroom replaced by classroom50. The unit tests now ship in `tests/` and run with `make test`, replacing a `make privatetest` target that invoked a script present only in the solution. Corrected the code tree, which was labelled `lab3/` and listed a `test_signals.cpp` that does not exist. Fixed two defects in the given code: a dangling `to_string(...).c_str()` passed to `execvp`, and a child process that printed "Parent process before fork". The reference handlers were rewritten to be async-signal-safe — the previous ones called the timestamped logger, and one `write()` was a byte short of its message — and section 2.3 now explains the rule. Run-time output (`signals.log`, `*_attributes.txt`, `fifo_*`, `storage/`) is now ignored by `.gitignore`. Added the time-limit table, the registry walkthrough, and the note that the first `make` fails until the flags are defined. Two further defects were found by running the lab and fixed in the given code: **Ctrl+C killed all three servers**, because they shared the client's foreground process group, after which the client died of `SIGPIPE` writing `QUIT` to dead FIFOs and never completed its own graceful shutdown — each child now calls `setpgid(0, 0)` before `exec` and the client ignores `SIGPIPE` (section 2.5); and **all three child processes printed "Parent process before fork:"** into their attributes files. The starter's handler comments no longer tell you to call the non-signal-safe logger from inside a handler. |
