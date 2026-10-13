---
layout: exam
title: "Exam 1 — Tasks"
exam_number: 1
exam_title: "Tasks"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
instructor: "David Kebo Houngninou"
exam_date: "Thursday, October 15, 2026"
exam_window: "9:00 AM – 11:59 PM CT"
exam_duration: "2 hours"
listed: false        # reachable by direct link, not shown on /exams/
description: "The four coding tasks and four written questions of Exam 1, with what each one is worth and how it is checked."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Before you start

<aside class="callout callout--warn" aria-labelledby="rules-heading">
<h2 class="callout__title" id="rules-heading">No AI. Honorlock. Two hours.</h2>
<p><strong>No artificial intelligence of any kind.</strong> No Codex, no Cursor,
no ChatGPT, no Claude, no Copilot, no Gemini, and no other code-generating or
code-completing assistant. <strong>Turn AI completion off in your editor before
you begin.</strong></p>
<p>Open notes, open book, open online search. <strong>Honorlock through
Canvas.</strong> Your own work only — do not share code.</p>
<p>You have <strong>two hours</strong> from whenever you start, inside the
9:00 AM – 11:59 PM CT window. <strong>Nothing pushed after 11:59 PM CT is
accepted.</strong></p>
</aside>

The full rules, the window arithmetic and the accommodations are on the
[Exam 1 instructions page](/exam-1-instructions/). This page is the exam itself.

## 2. What you are building, and what it is worth

Four small programs, each **independent** — a task you cannot finish does not
block any other. The autograder scores the code **out of 80**:

| Task | File | Points |
| --- | --- | --- |
| 1. Start four workers and collect them | `spawn.c` | 25 |
| 2. Connect `./emit` to `./count` through one pipe | `pipeline.c` | 25 |
| 3. One message through a FIFO | `fifo_round.c` | 15 |
| 4. A handler, a mask and an alarm | `guard.c` | 15 |

Four written questions in **`answers.md`** are worth the remaining **20 points**
and are marked by hand. **Exam total: 100.**

Each file carries its own instructions in comments, and every `printf` you need
is already written. **Do not change the wording of the output** — the checks
read those lines.

## 3. Setting up

1. Accept the exam on [classroom50.org](https://classroom50.org/), then clone
   your repository.
2. Build and test:

```bash
make        # your four programs, plus the three given ones
make test   # the same checks the autograder runs, out of 80
```

A fresh clone builds with **three warnings** — `unused variable 'fd'`, and the
two handlers in `guard.c` "defined but not used". They are the TODOs talking to
you, and they go away as you fill them in.

### Given to you — do not edit

| File | What it does |
| --- | --- |
| `worker.c` | prints `worker <i> pid <pid> parent <ppid>`, exits with status `<i>` |
| `emit.c` | writes five lines to standard output |
| `count.c` | counts lines on standard input, prints `count <n>` at end of file |

These, the `Makefile` and `tests/` are replaced with the reference copies before
grading, so editing them changes nothing.

## 4. The coding tasks

### 4.1 Task 1 — `spawn.c` (25 points)

Start `N_WORKERS` copies of `./worker` with `fork()` and `exec`, each told its
own index, then collect every one of them and report the status it exited with.

A correct run prints the start line, four `worker …` lines in any order, four
`reaped pid … status …` lines, and `spawn done, reaped 4`:

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

**Checked:** each worker ran with its own index and reports **spawn's own pid**
as its parent (15); every child was reaped and the status reported is the one
the worker chose, not the raw value `waitpid()` gives you (10).

### 4.2 Task 2 — `pipeline.c` (25 points)

Do by hand what the shell does for `./emit | ./count`: one pipe, two children,
each with the right end wired to the right standard stream, and every descriptor
nobody needs closed.

A correct run prints exactly one line and exits:

```console
count 5
```

**Checked:** `count 5` appears and the program exits on its own (25). If the
plumbing works but the program never finishes, a write end is still open
somewhere and `./count` never sees end of file — partial credit (15).

### 4.3 Task 3 — `fifo_round.c` (15 points)

Create the FIFO `exam_fifo`, have the child write `ping` through it, have the
parent read it and print `got ping`, and leave no FIFO behind.

```console
got ping
```

**Checked:** the message arrives (10); `exam_fifo` is gone when the program
exits (5).

### 4.4 Task 4 — `guard.c` (15 points)

Install the two handlers with `sigaction()`, block `SIGINT` while the critical
section runs, unblock it afterwards, then arm a one-second alarm and wait for it.

**While grading, a `SIGINT` is sent 200 ms in — during the critical section,
which lasts 400 ms.** A correct program therefore prints, in this order:

```console
critical 1
critical 2
interrupted
alarm fired
```

`interrupted` after `critical 2` is the whole point: a blocked signal is held,
not lost, and it arrives when you unblock it.

**Checked:** `interrupted` appears only after `critical 2` (10); the alarm fires
and the program exits (5).

## 5. The written questions — `answers.md` (20 points)

Four questions, 5 points each, marked by hand. Two or three sentences each is
plenty — a precise short answer scores better than a vague long one.

1. **Context switching.** What does the kernel save and restore when it switches
   the CPU between processes, and why is a context switch not free?
2. **Across `fork()` and `exec()`.** Two things a child inherits from its parent,
   one thing that differs; then one thing `exec()` replaces and one that survives.
3. **File descriptors and the file system.** After `fork()`, what exactly do
   parent and child share through the same open file — and what happens to a
   file's data if one process `unlink()`s its name while the other still has it
   open?
4. **Zombies and orphans.** Define each, and name the call or mechanism that
   stops each from being a problem.

**A blank template scores zero.** Answer these even if your code is unfinished —
they are 20 of the 100 points and they need no compiler.

## 6. Submitting

```bash
git add spawn.c pipeline.c fifo_round.c guard.c answers.md
git commit -m "exam 1"
git push
```

Push as you go rather than all at the end: a push that fails at 11:58 PM is not
a submission. The autograder runs on every push and you can read its result.

Do not commit the built programs or `exam_fifo` — `.gitignore` already excludes
them.

### Mistakes that cost points

| Symptom | Cause |
| --- | --- |
| `worker` reports a parent that is not `spawn`'s pid | The `exec` is not guarded by `if (pid == 0)`, so the parent replaced itself |
| `reaped … status 256` or similar | Use `WEXITSTATUS()` on what `waitpid()` writes, not the raw value |
| `pipeline` never finishes | A write end of the pipe is still open — the parent must close both after forking |
| `fifo_round` hangs with no output | Opening a FIFO blocks until the other end is open too; check which side opens which |
| `exam_fifo` still there afterwards | `unlink()` it before the program exits |
| `interrupted` printed before `critical 2` | `SIGINT` was not blocked around the critical section |
| Nothing graded after a push | Check the Actions tab on your repository for the run |

## 7. Getting help

During the exam: **no help with the exam content.** If something is broken —
the repository will not clone, Actions will not run — message on Discord and say
it is Exam 1.

Office hours and TA contact details are in the syllabus.

## Revision history

| Date | Change |
| --- | --- |
| 2026-10-13 | Written for Exam 1, Thursday October 15. |
