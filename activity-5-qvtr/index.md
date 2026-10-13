---
layout: activity
title: "Activity 5 — Reap Your Children"
activity_id: 5
activity_title: "Reap Your Children"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Lab 4"
listed: false        # reachable by direct link, not shown in the index
duration: "15 minutes"
description: "A parent forks three workers and never collects them, so they pile up as zombies. Install a SIGCHLD handler and reap them."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. What you are doing

`reaper.c` forks three workers and then does five seconds of its own work. The
workers exit after a second — and nobody collects them, so for the rest of the
run they sit in the process table as **zombies**.

Two TODOs fix it: install a `SIGCHLD` handler with `sigaction()`, and reap inside
it with `waitpid(..., WNOHANG)`. That is the same pattern as Lab 4's
`register_servers()` and its `SIGCHLD` handler, in a program small enough to hold
in your head.

Fifteen minutes. Roughly six lines of code.

## 2. Rules

<aside class="callout callout--warn" aria-labelledby="rules-heading">
<h2 class="callout__title" id="rules-heading">No AI. In class. Proctored.</h2>
<p><strong>No artificial intelligence of any kind.</strong> No Codex, no Cursor,
no ChatGPT, no Claude, no Copilot, no Gemini, and no other code-generating or
code-completing assistant. <strong>Turn AI completion off in your editor before
you begin.</strong></p>
<p><strong>This activity is completed in class, under Honorlock.</strong> Work
done outside class does not count.</p>
<p><strong>We will give you the Honorlock instructions when the activity is
released.</strong> They are not on this page — wait for them, and do not start
the proctored session until you are told to.</p>
</aside>

What you **may** use: the Lab 4 handout, your own Lab 4 work, the
[`signals-practice`](https://github.com/CSCE-313-FA26/signals-practice)
examples, the `man` pages, and your notes. You may talk to the person next to you
about *ideas*. The code you submit must be yours.

## 3. Get your repository

1. Sign in to [classroom50.org](https://classroom50.org/) with your GitHub account.
2. Accept the activity:
   <https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/activity-5/accept>.
3. Clone it and build:

```bash
git clone https://github.com/CSCE-313-FA26/<your-activity-5-repository>.git
cd <your-activity-5-repository>
make
```

Plain C, plain `gcc`. A fresh clone builds with **one** warning —
`'on_sigchld' defined but not used` — because nothing has installed the handler
yet. It goes away when you do TODO 1.

`reaper.c` is the only file you change, and the only one that is graded.

## 4. See the problem first

```bash
make
./reaper
```

It prints its work lines and finishes with `parent done, reaped 0 children`.
While it is running, in a second terminal:

```bash
ps --ppid $(pgrep -x reaper) -o pid,stat,comm
```

Three children, every one in state **`Z`**. A child that has exited is not gone:
the kernel keeps its exit status until the parent asks for it, and until then the
entry stays. `reap_all` in `signals-practice` is the same picture with five.

<aside class="callout callout--note" aria-labelledby="queue-heading">
<h2 class="callout__title" id="queue-heading">One signal can stand for several children</h2>
<p>Ordinary signals do not queue. If two children exit close together, the parent
may get <strong>one</strong> <code>SIGCHLD</code> for both — so a handler that
reaps a single child loses the other. That is why the handler reaps in a loop,
and why the loop must not block: <code>WNOHANG</code> makes
<code>waitpid()</code> return 0 rather than wait when nothing is ready.</p>
</aside>

## 5. The two TODOs

**TODO 1, in `main()`.** Install `on_sigchld` as the handler for `SIGCHLD` using
`sigaction()`. Zero the `struct sigaction` first, set `SA_RESTART` so a child's
exit does not break a system call the parent is in the middle of, and
`perror()` + `return 1` if `sigaction()` fails.

**TODO 2, in the handler.** Reap every child that has already exited, without
blocking. `waitpid(-1, &status, WNOHANG)` returns a pid for each one it
collects, `0` when none is ready and `-1` when there are none left. Add 1 to
`reaped` for each child you collect.

Nothing else belongs in a handler — no `printf`, no `malloc`. `reaped` is already
declared `volatile sig_atomic_t` for you, and the parent prints it at the end.

Do not change what the program prints. The checks read those lines.

## 6. What a correct run looks like

```console
$ ./reaper
parent working 1
worker 0 exiting
worker 1 exiting
worker 2 exiting
parent working 2
parent working 3
parent working 4
parent working 5
parent done, reaped 3 children
```

The `worker` lines may come in any order, and may interleave with the work lines
differently from run to run. What must be true is the last line — **3** — and
`ps` showing no `Z` child at any point during the run.

```bash
make test        # the same checks the autograder runs, out of 100
```

## 7. Submitting

```bash
git add reaper.c
git commit -m "activity 5"
git push
```

The autograder runs on every push, so push as often as you like and read the
result. Points are awarded per behaviour, so partial work is worth partial
credit.

| Check | Points |
| --- | --- |
| `reaper.c` compiles | 10 |
| No child is ever left a zombie | 30 |
| All three children reaped — the final line says 3 | 40 |
| The parent still finishes its own five work lines | 20 |

| What the grader says | What it means |
| --- | --- |
| `gcc failed` | Fix the error `gcc` prints, then push again |
| `saw 3 zombie child(ren)` | Nothing is reaping — TODO 1, the handler is not installed |
| `the final line said 0` | The handler is installed but reaps nothing — TODO 2 |
| `the final line said 2 of 3` | The handler reaps once instead of looping |
| `did not exit cleanly within 25 s` | Something in the handler is blocking — check `WNOHANG` |

The grader samples the process list every 150 ms while your program runs, and
reads the lines it prints. It never looks at your source, so any correct way of
reaping scores full marks.

Do not commit the built program — `.gitignore` already excludes it.

## 8. If you finish early

None of this is submitted — it is here if you have time left.

- Drop `SA_RESTART` and run it again. Does `sleep()` still finish each second?
  What would `-EINTR` do to a `read()` in Lab 4?
- Replace `waitpid(-1, &status, WNOHANG)` with `wait(&status)` in the handler.
  It still works here — now make it break, by giving one worker a longer sleep.
- Print `WEXITSTATUS(status)` for each child from the handler with `write()`, not
  `printf`. Why is `printf` the wrong call in a handler, and what does `write()`
  cost you in convenience?
- Remove the handler entirely and reap with a `waitpid` loop after the parent's
  work instead. Which approach lets the parent get on with its work, and which
  one would Lab 4's client need?
