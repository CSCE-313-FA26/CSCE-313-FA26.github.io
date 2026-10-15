---
layout: exam
title: "Exam 1 — Processes and Signals"
exam_number: 1
exam_title: "Exam 1 — Processes and Signals"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
instructor: "David Kebo Houngninou"
exam_date: "Thursday, October 15, 2026"
exam_window: "8:00 AM – 11:59 PM CT"
exam_duration: "2 hours"
listed: false        # reachable by direct link, not shown on /exams/
description: "The four coding tasks of Exam 1: what to write in each file, what a correct run prints, and how each one is checked."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Description

You are given four C files. Each one is complete except for a few marked
`TODO`s: the `#include`s, `main()`, and every `printf` you need are already
written, and you fill in the lines that do the actual work. Across the four
files that comes to roughly **65 lines of code**.

**You are graded on what your programs do when they are run.** The autograder
compiles each one, runs it, and reads what it prints — nobody reads your source.
So code that looks correct but does not compile, or prints something other than
the line a check is looking for, earns nothing for that check.

Before you push you can run the very same checks yourself, as often as you
like — that is `make test` in section 2.

| Task | File | Points | What it is about |
| --- | --- | --- | --- |
| 1 | `spawn.c` | 20 | `fork`, `exec`, and collecting children |
| 2 | `pipeline.c` | 20 | one pipe, two children, `dup2` |
| 3 | `guard.c` | 30 | blocking a signal around a critical section |
| 4 | `watchdog.c` | 30 | using a signal to put a time limit on a blocking call |

**Tasks 3 and 4 are the signal work and carry 60 of the 100 points.** They are
the material of Lab 4: installing a handler with `sigaction()`, deciding what
`sa_flags` should say, blocking and unblocking, and knowing why a blocking call
came back.

The four tasks are **independent**. A task you cannot finish does not block any
other, so if one fights you, move on and come back.

<aside class="callout callout--warn" aria-labelledby="rules-heading">
<h2 class="callout__title" id="rules-heading">No AI. Honorlock. Two hours.</h2>
<p><strong>No artificial intelligence of any kind.</strong> No Codex, no Cursor,
no ChatGPT, no Claude, no Copilot, no Gemini, and no other code-generating or
code-completing assistant. <strong>Turn AI completion off in your editor before
you begin.</strong></p>
<p>Open notes, open book, open online search. <strong>Honorlock through
Canvas.</strong> Your own work only — do not share code.</p>
<p>You have <strong>two hours</strong> from whenever you start, inside the
8:00 AM – 11:59 PM CT window. <strong>Nothing pushed after 11:59 PM CT is
accepted.</strong></p>
</aside>

The full rules, the window arithmetic and the accommodations are on the
[Exam 1 instructions page](/exam-1-instructions/). This page is the exam itself.

## 2. Setting Up

1. Accept the exam on [classroom50.org](https://classroom50.org/), then clone
   your repository.
2. Build and test:

```bash
make        # your four programs, plus the three given ones
make test   # the same checks the autograder runs, out of 100
```

A fresh clone builds with **four warnings**: `unused variable 'fd'` in
`pipeline.c`, and three "defined but not used" for the handlers in `guard.c` and
`watchdog.c`. They are the TODOs talking to you, and they go away as you fill
them in.

Every `printf` you need is already written in each file. **Do not change the
wording of the output** — the checks read those lines.

### Given to you — do not edit

| File | What it does |
| --- | --- |
| `worker.c` | prints `worker <i> pid <pid> parent <ppid>`, exits with status `<i>` |
| `emit.c` | writes five lines to standard output |
| `count.c` | counts lines on standard input, prints `count <n>` at end of file |

These, the `Makefile` and `tests/` are replaced with the reference copies before
grading, so editing them changes nothing.

## 3. The Tasks

Each task below says three things: **what to write**, **what a correct run
prints**, and **how it is checked**. The TODO comments in the file say the same
thing in more detail.

### 3.1 Task 1 — `spawn.c` (20 points)

**What to write.** Start `N_WORKERS` copies of `./worker` with `fork()` and
`exec`, each told its own index. Then collect every one of them and report the
status it exited with.

**A correct run prints** the start line, four `worker …` lines in any order,
four `reaped …` lines, and the total:

```console
spawn pid 2000 starting 4 workers
worker 0 pid 2001 parent 2000
worker 1 pid 2002 parent 2000
worker 2 pid 2003 parent 2000
worker 3 pid 2004 parent 2000
reaped pid 2001 status 0
reaped pid 2002 status 1
reaped pid 2003 status 2
reaped pid 2004 status 3
spawn done, reaped 4
```

**How it is checked.** Two separate rows:

| | Points |
| --- | --- |
| Each worker ran with its own index and reports **spawn's own pid** as its parent | 12 |
| Every child was reaped, and the status reported is the one the worker chose — not the raw value `waitpid()` writes | 8 |

### 3.2 Task 2 — `pipeline.c` (20 points)

**What to write.** Do by hand what the shell does for `./emit | ./count`: one
pipe, two children, each with the right end wired to the right standard stream,
and every descriptor nobody needs closed.

**A correct run prints exactly one line, then exits:**

```console
count 5
```

**How it is checked.** `count 5` appears and the program exits on its own, for
the full 20. If the plumbing works but the program never finishes, a write end
is still open somewhere and `./count` never sees end of file — that earns **12
of 20**, because the `dup2` and the `exec` demonstrably worked.

### 3.3 Task 3 — `guard.c` (30 points)

**What to write.** Install the two handlers with `sigaction()`. Block `SIGINT` —
only `SIGINT` — while the critical section runs, unblock it afterwards, then arm
a one-second alarm and wait for it.

**While grading, a `SIGINT` is sent 200 ms in — during the critical section,
which lasts 400 ms.** A correct program therefore prints, in this order:

```console
critical 1
critical 2
interrupted
alarm fired
```

`interrupted` appearing **after** `critical 2` is the whole point: a blocked
signal is held, not lost, and it is delivered the moment you unblock it.

**How it is checked.** Two separate rows:

| | Points |
| --- | --- |
| `interrupted` appears, and only after `critical 2` | 20 |
| The alarm fires and the program exits on its own | 10 |

### 3.4 Task 4 — `watchdog.c` (30 points)

**What to write.** A `read()` that never returns is a hung program. Give it a
deadline: install a `SIGALRM` handler, arm an alarm, and then tell the two
outcomes apart — the data arrived, or the alarm interrupted the read.

**The pipe, the `fork()` and the child are already written for you.** Your work
is the three TODOs: the handler, the alarm, and a `read()` that knows why it
came back.

The grader runs your program **both ways**, passing the argument itself:

```console
$ ./watchdog fast        # the child answers after 0.3 s
got hello
done

$ ./watchdog slow        # the child never answers
timed out
done
```

Either way the program must print `done` and exit. **It must never hang.**

**The one subtlety, and it is the point of the task:** do *not* set
`SA_RESTART` on this handler. With `SA_RESTART`, the kernel resumes the
interrupted `read()` and your program waits for ever. Without it, `read()`
returns `-1` with `errno` set to `EINTR`, which is how you learn the deadline
passed.

**How it is checked.** Two separate rows:

| | Points |
| --- | --- |
| `./watchdog fast` reads the answer and reports `got hello` | 10 |
| `./watchdog slow` reports `timed out` and still exits cleanly | 20 |

## 4. Submitting

```bash
git add spawn.c pipeline.c guard.c watchdog.c
git commit -m "exam 1"
git push
```

Push as you go rather than all at the end: a push that fails at 11:58 PM is not
a submission. The autograder runs on every push and you can read its result in
the Actions tab and in the release it creates.

Do not commit the built programs — `.gitignore` already excludes them.

## 5. Mistakes That Cost Points

| Symptom | Cause |
| --- | --- |
| `worker` reports a parent that is not `spawn`'s pid | The `exec` is not guarded by `if (pid == 0)`, so the parent replaced itself |
| `reaped … status 256` or similar | Use `WEXITSTATUS()` on what `waitpid()` writes, not the raw value |
| `pipeline` never finishes | A write end of the pipe is still open — the parent must close both after forking |
| `interrupted` printed before `critical 2` | `SIGINT` was not blocked around the critical section |
| `watchdog slow` hangs for ever | No alarm was armed, or the handler was installed with `SA_RESTART` |
| `watchdog slow` dies with "Alarm clock" | The alarm fired with no handler installed, so the default action killed the program |
| Nothing graded after a push | Check the Actions tab on your repository for the run |

## 6. Getting Help

During the exam: **no help with the exam content.** If something is broken —
the repository will not clone, Actions will not run — message on Discord and say
it is Exam 1.

Office hours and TA contact details are in the syllabus.
