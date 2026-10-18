---
layout: lab
title: "Lab 5 — Thread Pool"
lab_number: 5
lab_title: "Thread Pool"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
instructor: "David Kebo Houngninou"
released: "Tuesday, October 20, 2026, 9:00 AM CT"
due: "Monday, November 2, 2026, 11:59 PM CT"
released_short: "Tue Oct 20, 2026"
due_short: "Mon Nov 2, 2026, 11:59 PM CT"
description: "Build a thread pool — a fixed set of worker threads sharing one task queue — and use it to apply interest to every account at once."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Objectives

By the end of this lab you will be able to:

- Say what a thread pool is, and why it is used instead of one thread per task.
- Start worker threads with `std::thread` and keep them in a container.
- Share a queue between threads safely with `std::mutex`.
- Make a thread **wait** for work with `std::condition_variable` instead of
  spinning on a flag.
- Explain why a condition variable is always used with a predicate, and what a
  spurious wake-up is.
- Shut a pool down without losing work that is already queued.

## 2. Background

### 2.1 What changed since Lab 4

The banking system is the one you already have: one client, three servers,
FIFOs between them, the signal handling from Lab 4 given back to you working.
Two things are new.

`thread_pool.h` and `thread_pool.cpp` are a new pair of files. The header is
written; the three functions in the `.cpp` are yours.

`common.h` has one more request type, `EARN_INTEREST`, and the client has one
more menu item, **9. Update Interest for All Accounts**, restricted to user 0.
Both are written for you. What happens when the finance server receives that
request is yours.

### 2.2 Why a pool, and not a thread per task

Applying interest to every account is a lot of small, independent pieces of
work: account 0 does not care what happens to account 1. That is the shape
that suits concurrency.

The obvious thing — `std::thread` per account — costs a thread creation and a
thread destruction per piece of work, and with ten thousand accounts asks the
kernel for ten thousand threads. A **thread pool** creates a fixed number of
threads once, and feeds them from a queue. The threads are **persistent**:
they outlive any single task. They are **reusable**: when one task finishes
the thread goes back for another instead of exiting.

The cost moves from "per task" to "per pool", and the number of threads stops
depending on the amount of work.

### 2.3 The three pieces of shared state

```cpp
std::vector<std::thread> workers;          // the threads themselves
std::queue<std::function<void()>> tasks;   // work waiting to be done
std::mutex queueMutex;                     // guards tasks (and stop)
std::condition_variable condition;         // "something changed"
bool stop;                                 // no more work will be added
std::atomic<int> activeTasks;              // tasks currently running
```

`tasks` is touched by every worker and by whoever calls `enqueue`. Two threads
calling `push` and `pop` at the same moment corrupt it — this is not a
theoretical risk, `std::queue` has no internal locking at all. Hold
`queueMutex` whenever you look at `tasks` or at `stop`.

`activeTasks` is `std::atomic<int>`, so `++` and `--` on it are safe on their
own without the mutex.

### 2.4 Waiting without spinning

A worker with nothing to do must not sit in a loop asking "is the queue empty
yet?". That burns a whole core to discover nothing. `std::condition_variable`
is how a thread sleeps until somebody says otherwise:

```cpp
std::unique_lock<std::mutex> lock(queueMutex);
condition.wait(lock, [this] { return stop || !tasks.empty(); });
```

`wait` **releases the lock** and sleeps. When another thread calls
`notify_one` or `notify_all`, it wakes, **re-acquires the lock**, and tests the
predicate. If the predicate is false it goes back to sleep.

The predicate is not optional politeness. A condition variable may wake a
thread when nobody notified it — a *spurious wake-up* — and even a real
notification may have been consumed by a different worker before this one got
the lock. The predicate is what turns "I was woken" into "there is actually
work for me".

<aside class="callout callout--note" aria-labelledby="unlock-heading">
<h2 class="callout__title" id="unlock-heading">Release the lock before you run the task</h2>
<p>Take the task out of the queue with the lock held; then let the lock go, and
only then call the task. A worker that keeps <code>queueMutex</code> while the
task runs blocks every other worker from reaching the queue, so the tasks run
one after another. The pool still produces the right answer — which is exactly
why this is worth saying out loud. It is a pool with four threads and the
throughput of one.</p>
</aside>

### 2.5 What `stop` means, and what it does not

`stop` means *no further tasks will be added*. It does not mean *abandon what
is queued*. Everything already in the queue runs to completion, even after
`stop` is set and even though the destructor is what set it.

So a worker returns only when **both** conditions hold: `stop` is true **and**
the queue is empty.

## 3. Environment setup

### 3.1 Accept the assignment

1. Sign in to [classroom50.org](https://classroom50.org/) with your GitHub account.
2. Accept Lab 5:
   <https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/lab-5/accept>.
   Your repository is created for you.
3. Clone it:

```bash
git clone https://github.com/CSCE-313-FA26/<your-lab-5-repository>.git
cd <your-lab-5-repository>
```

### 3.2 Repository layout

| Path | What it is | Yours to change? |
| --- | --- | --- |
| `thread_pool.cpp` | the constructor, the destructor and `enqueue` — most of the lab | Yes |
| `finance.cpp` | `applyInterest`, and the `EARN_INTEREST` branch | Yes, the marked spots |
| `thread_pool.h` | the `ThreadPool` class: members and declarations | No |
| `client.cpp` | the menu, including item 9 | No |
| `logging.cpp`, `file.cpp` | the other two servers, complete | No |
| `signals.h`, `signals.cpp` | Lab 4's signal handling, given back working | No |
| `channel.cpp`, `channel.h`, `common.*` | the channel from Lab 3, given back | No |
| `Makefile` | builds `client`, `finance`, `logging`, `file` | No |
| `tests/` | the unit tests and `grade.py` — the same checks the autograder runs | No |

### 3.3 Build and run

```bash
make
./client
```

A fresh clone builds. It prints exactly one warning,

```
finance.cpp: warning: variable ‘numThreads’ set but not used
```

which is true: the `EARN_INTEREST` branch works out how many threads to ask
for and then does nothing with the number, because creating the pool is task
5.4. The warning goes away when you write that line.

The client asks for the maximum account number, a log file name, and the
allowed file extensions, then shows the menu. Menu item **9** is the new one.
It asks how many threads to use and is available only to user 0; every other
user is told so.

<aside class="callout callout--note" aria-labelledby="stale-heading">
<h2 class="callout__title" id="stale-heading">A server from your last run will answer this run's requests</h2>
<p>The three servers are separate processes. If a previous client was killed —
from another terminal, by your editor, or with <kbd>Ctrl</kbd>+<kbd>\</kbd> —
its servers survive it, and they are still holding the other end of
<code>fifo_finance_1</code> and friends. Your next client then talks to
<em>those</em> servers, which have their own, separate set of accounts. The
session does not hang and does not report an error; the balances simply come
back wrong, and shutdown pauses for five seconds and prints
<code>A server did not exit; sending SIGTERM.</code></p>
<p>The client warns you at start-up when it finds FIFOs that an earlier run
left behind. When it does, or whenever a session behaves strangely:</p>
<pre><code>ps -C finance -C logging -C file -o pid,etimes,comm -u "$USER"
pkill -x -u "$USER" finance ; pkill -x -u "$USER" logging ; pkill -x -u "$USER" file
rm -f fifo_*</code></pre>
<p>Keep the <code>-u "$USER"</code>. ZACH 598 machines are shared, and
<code>pkill -x finance</code> on its own kills every <code>finance</code>
running on that machine, including the one belonging to whoever is sitting
next to you. One pattern per <code>pkill</code> as well: it takes a single
pattern and exits with a usage error if you give it more. Never
<code>pkill -f file</code> — <code>-f</code> matches whole command lines, and
nearly every command line contains the word <code>file</code>.</p>
<p>Leftover <code>fifo_*</code> entries on their own are harmless; the leftover
<em>process</em> is what matters. <code>make clean</code> removes the FIFOs but
cannot kill a process.</p>
</aside>

### 3.4 Test your work

```bash
make test
```

That builds everything and runs `tests/grade.py`: three unit tests against
your `ThreadPool`, then a direct test of `applyInterest`, then a whole client
session — scored exactly as the autograder scores it, out of 100. Run it
often. On an untouched clone it reports **0/100** and names what is missing.

Where the toolchain has it, the enqueue test is also run a second time under
**ThreadSanitizer**, which reports a data race whether or not the race
happened to cause any damage on that run. Touching `tasks` without holding
`queueMutex` usually gets away with it on a two-core machine; this is what
catches it anyway. If ThreadSanitizer is not installed the check is skipped,
and nothing is held against you for it.

The one difference: run locally, every part is your code, so a broken
`thread_pool.cpp` fails the two `finance.cpp` rows as well. The autograder
links finance against a reference thread pool, so there each file is judged on
its own.

## 4. Walkthrough

### 4.1 The interface you are implementing

```cpp
ThreadPool(size_t numThreads);               // start the workers
~ThreadPool();                               // finish the work, stop the workers
void enqueue(std::function<void()> task);    // hand over one piece of work
```

That is the whole public surface. A caller creates a pool, throws work at it,
and lets it go out of scope:

```cpp
{
    ThreadPool pool(4);
    for (int i = 0; i < n; i++) {
        pool.enqueue([i]() { do_something(i); });
    }
}   // the destructor runs here, and every task has finished by the time it returns
```

Note what the caller does **not** do: there is no `wait_for_all()`. Waiting is
the destructor's job, which is why section 2.5 matters.

### 4.2 The life of one task

| Step | Who | Holding `queueMutex`? |
| --- | --- | --- |
| `enqueue` pushes the task | the caller's thread | yes |
| `enqueue` notifies | the caller's thread | not required |
| a worker wakes and tests the predicate | a worker | yes |
| the worker pops the task | a worker | yes |
| the worker **runs** the task | a worker | **no** |
| the worker goes back to wait | a worker | yes |

### 4.3 Lambdas, briefly

A task is a `std::function<void()>` — anything callable with no arguments and
no return. A lambda is the convenient way to make one:

```cpp
pool.enqueue([accounts, id]() { applyInterest(accounts[id]); });
```

The list in brackets is the **capture**: the names from the surrounding scope
this lambda keeps a copy of. Capture `id` **by value**. A lambda that captured
the loop variable by reference would read it later, by which time the loop has
moved on and every task would work on the same account.

`accounts` is a pointer, so copying it copies the pointer, not the accounts.
Each task then works on a different element, which is why no two tasks ever
touch the same `Account` and no extra locking is needed inside
`applyInterest`.

### 4.4 What happens when the user presses 9

1. The client checks that user 0 is logged in, asks how many threads to use,
   and sends an `EARN_INTEREST` request with that number in the `amount` field.
2. The finance server reaches the `EARN_INTEREST` branch. The thread count is
   already worked out for you: the request's amount if it is positive, and 2
   otherwise.
3. Your code creates a `ThreadPool` and enqueues one `applyInterest` task per
   account — **every** account, not only the active ones; `applyInterest`
   decides what to do with each.
4. The pool goes out of scope. Its destructor waits for the work.
5. The server sends the response, and the client prints
   `Interest update successful!`.

<aside class="callout callout--note" aria-labelledby="vacuous-heading">
<h2 class="callout__title" id="vacuous-heading">That message is not evidence</h2>
<p>An untouched <code>thread_pool.cpp</code> creates no threads, queues
nothing, and runs nothing — and the client still prints
<code>Interest update successful!</code>, because nothing in the path reports
failure. Check a balance with menu item <strong>4</strong> afterwards. That is
what the autograder does.</p>
</aside>

## 5. To-do

Five tasks, 100 points. Tasks 5.1 to 5.3 are `thread_pool.cpp`; 5.4 and 5.5
are `finance.cpp`. Do them in that order: nothing in `finance.cpp` can be
tested until the pool runs tasks.

### 5.1 The constructor (50 points)

Create `numThreads` worker threads and put them in `workers`. Each worker
loops until the pool is finished, and on every pass:

- waits on `condition` until there is a task **or** `stop` is set,
- returns if `stop` is set and the queue is empty,
- otherwise takes the front task off `tasks`,
- **releases the lock**, then runs the task,
- keeps `activeTasks` correct across the call.

### 5.2 The destructor (20 points)

Set `stop`, wake every worker, and join them all. Work already in the queue
still has to run — see section 2.5. When the destructor returns, nothing from
this pool is still running.

### 5.3 `enqueue` (15 points)

Add the task to the back of `tasks` and let a worker know. Hold `queueMutex`
while you touch the queue. `enqueue` hands the task over and returns; it does
not run the task and it does not wait for a worker to be free.

Notify **after** you push. A worker that is already asleep in
`condition.wait` has no other way of finding out that there is work — and a
pool that happens to be busy hides a missing notification completely, because
a worker that never gets as far as sleeping keeps finding the next task by
itself.

### 5.4 `EARN_INTEREST` in the finance server (10 points)

In the marked branch of `finance.cpp`, create a `ThreadPool` with the thread
count already computed there, and enqueue an `applyInterest` task for every
account from `0` to `max_accounts - 1`. Set a message on the response. If
something throws, the `catch` block is where you report it: set
`resp.success = false`. You do not have to undo accounts that were already
updated.

### 5.5 `applyInterest` (5 points)

Given an `Account&`:

- if the account is **active** and its balance is **positive**, increase the
  balance by 1%;
- otherwise leave it exactly as it is.

An inactive account earns nothing however much it holds, and an overdrawn
account does not grow its debt by 1%.

## 6. Deliverables

Commit and push your work:

```bash
git add thread_pool.cpp finance.cpp
git commit -m "lab 5"
git push
```

Only those two files are graded. `thread_pool.h`, the client, the other
servers, the channel, the `Makefile` and `tests/` are replaced with the
reference copies before grading, so changing them has no effect on your score.
Do not commit the built programs or the run-time output — `.gitignore` already
excludes them.

The autograder runs on every push. Push as often as you like and read the
result.

### 6.1 Mistakes that cost points

| Symptom | Cause |
| --- | --- |
| Balances come back wrong, or shutdown prints `A server did not exit; sending SIGTERM.` | A server from an earlier run is still alive and is answering your requests — see the note in section 3.3 |
| The program aborts with `terminate called without an active exception` | A `std::thread` that was never joined was destroyed. The destructor has to join every worker |
| Tasks never run at all, or only when the pool is busy | `enqueue` pushed the task but never notified, so a worker that had gone to sleep never woke up |
| Tasks run, but only one at a time | The worker is holding `queueMutex` while it runs the task — section 2.4 |
| The program crashes or loses tasks under load | `tasks` was touched without holding `queueMutex` |
| `make test` reports a ThreadSanitizer data race in `enqueue` | Same cause, caught directly: the push has to happen under `queueMutex`, even on the runs where nothing visibly goes wrong |
| The destructor returns but some tasks never ran | `stop` was treated as "abandon the queue" rather than "no more will be added" — section 2.5 |
| The destructor never returns | The workers are waiting on `condition` and were never notified after `stop` was set |
| Every task applies interest to the same account | The lambda captured the loop variable by reference — section 4.3 |
| `Interest update successful!` but no balance changed | Nothing was enqueued; the message is printed either way — section 4.4 |
| Only the logged-in account earned interest | Task 5.4 asks for one task per account, `0` to `max_accounts - 1` |
| An inactive account's balance changed | `applyInterest` must check `active` before it checks the balance |
| The client prints `End of input. Shutting down.` | Its input ran out — you piped a file or a heredoc that did not end with `0` for Exit. Not an error |

## 7. Getting help

Ask on Discord. Bring the exact command you ran and the exact output, not a
description of it. The Canvas inbox is not monitored.

Office hours and TA contact details are in the syllabus.

## Revision history

| Date | Change |
| --- | --- |
| 2026-10-18 | Migrated from the Google Doc to this page. Due date corrected from July 26 (a leftover from a summer offering) to Monday, November 2. GitHub Classroom replaced by classroom50. The code tree, which was labelled `lab-4/` and listed a `test_signals.cpp` that does not exist, was corrected. The FA25 shell tests were replaced by `tests/`, which ships the unit tests and `grade.py` and runs with `make test` — the old `lab5-tests.sh` never printed a score (it added points to a variable it did not track) and wrote its output to fixed paths under `/tmp`, which collide between users on a shared machine. Four defects in the given code were found by running the lab and fixed: a **dangling `to_string(...).c_str()`** passed to `execvp`; **Ctrl+C killed all three servers**, because they shared the client's foreground process group, after which the client's own shutdown wrote to dead FIFOs and printed three broken-pipe errors — each child now calls `setpgid(0, 0)` before `exec` and the client ignores `SIGPIPE`; **the client could hang for ever at shutdown**, because `wait(NULL)` was unbounded and a server left over from an earlier run receives the QUIT meant for this one — the wait is now bounded and falls back to `SIGTERM`; and **menu item 9 printed "Only user 0 can update interest!" while allowing any logged-in user**, which the handout had always described as user 0 only. The client now also warns at start-up when it finds `fifo_*` entries an earlier run left behind: a surviving server answers the new client's requests from its own accounts, so the session completes with wrong balances and no error. A fifth defect, inherited from Lab 1: **the menu loop spun when input ran out**. `clear_input()` clears the end-of-file bit, the next read reaches end of file again immediately, and the menu is reprinted as fast as the machine can manage — measured at 3,092,431 iterations and 717 MB of output in eight seconds, one core at 100% throughout. Closing stdin now shuts the client down. The starter's comment for the destructor said to set `stop` to *false*; it is *true*. The three servers now answer QUIT instead of exiting silently. Run-time output (`*.log`, `fifo_*`, `storage/`, `*_attributes.txt`) is now ignored by `.gitignore`, and `distclean` no longer left `*.d` behind. |
