---
layout: activity
title: "Activity 2 — Four Bugs in a Client"
activity_id: 2
activity_title: "Four Bugs in a Client"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Lab 2"
listed: false        # reachable by direct link, not shown in the index
duration: "30 minutes"
description: "A client that starts worker programs with fork() and exec() is broken in four places. Find all four and fix them."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. What you are doing

`client.cpp` starts four worker programs with `fork()` and `exec()`, then collects
them. It compiles cleanly and it is wrong in **four** places.

Every one of the four is a mistake people actually make in Lab 2. You are
debugging someone else's client so that next week you can debug your own.

There is no new material here. If you have started Lab 2 Task 1, you have met all
four already.

## 2. Rules

<aside class="callout callout--warn" aria-labelledby="rules-heading">
<h2 class="callout__title" id="rules-heading">No AI. In class. Proctored.</h2>
<p><strong>No artificial intelligence of any kind.</strong> No Codex, no Cursor,
no ChatGPT, no Claude, no Copilot, no Gemini, and no other code-generating or
code-completing assistant. <strong>Turn AI completion off in your editor before
you begin.</strong></p>
<p><strong>This activity is completed in class, under Honorlock.</strong> Work
done outside class does not count.</p>
<p><strong>Your instructor will give you the Honorlock instructions when the
activity is released.</strong> They are not on this page — wait for them, and do
not start the proctored session until you are told to.</p>
</aside>

What you **may** use: the Lab 2 handout, your own Lab 2 work, the `man` pages,
and your lecture notes. You may talk to the person next to you about *ideas*.
The code you submit must be yours.

## 3. Get your repository

1. Sign in to [classroom50.org](https://classroom50.org/) with your GitHub account.
2. Accept the activity:
   <https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/activity-2/accept>.
3. Clone it and build:

```bash
git clone https://github.com/CSCE-313-FA26/<your-activity-2-repository>.git
cd <your-activity-2-repository>
make
```

Only `g++` is needed. There is no `clang` and no LLVM IR in this activity.

<aside class="callout callout--note" aria-labelledby="roster-heading">
<h2 class="callout__title" id="roster-heading">If accepting fails</h2>
<p>If your name is missing from the roster, or you signed in with the wrong GitHub
account, tell the instructor or a TA now — do not create a second account.</p>
</aside>

## 4. What you are given

| Path | What it is |
| --- | --- |
| `client.cpp` | **The only file you change.** All four bugs are here. |
| `worker.cpp` | The program the client starts. **Correct — do not change it.** |
| `Makefile` | Builds both. Do not change it. |

`worker.cpp` stands in for Lab 2's finance, logging and file servers: a separate
program, started with arguments, that reports who it is and then exits with a
status. It reads one flag:

```bash
./worker -n 2        # prints its line, then exits with status 2
```

Read it. It is short, and it tells you exactly what the client has to get right.

## 5. What a correct run looks like

```console
$ make
$ ./client
client pid 4021 starting 4 workers
worker 0 pid 4022 parent 4021
worker 1 pid 4023 parent 4021
worker 2 pid 4024 parent 4021
worker 3 pid 4025 parent 4021
client reaped pid 4022 exit 0
client reaped pid 4023 exit 1
client reaped pid 4024 exit 2
client reaped pid 4025 exit 3
client done, reaped 4
```

Four things have to be true, and each one is a separate bug:

1. The workers **run at all**.
2. There are **exactly four** of them, and the client is still alive to reap them.
3. Each worker is told **its own index** — 0, 1, 2, 3, not the same number four times.
4. The client **reaps every child** — all four, not just the first — and reports
   the status each one exited with.

Your PIDs will differ. **The lines may interleave in a different order** — workers
and the client run at the same time, so a reaped line can appear before another
worker's line. That is normal and not a bug. Only the four things above are checked.

## 6. How to work

Run it first. Do not read for bugs — let the program tell you.

```bash
make
./client
```

Fix the first thing it complains about, run it again, and see what changes. Each
fix makes the next symptom visible. All four are small; none needs more than a
line or two.

<aside class="callout callout--warn" aria-labelledby="dangle-heading">
<h2 class="callout__title" id="dangle-heading">When you build an argument string</h2>
<p>One of the fixes involves passing a number to the worker. Keep the string in a
named variable, the way the starter already does:</p>
<p><code>string idx = to_string(i);</code> &nbsp;then&nbsp; <code>idx.c_str()</code></p>
<p>Writing <code>(char*)to_string(i).c_str()</code> directly inside the array looks
tidier and is <strong>wrong</strong>: the temporary string is destroyed at the end of
that statement, so the pointer you stored is dangling before <code>execvp</code>
ever reads it. It often appears to work, which is what makes it dangerous. The
same trap is waiting in Lab 2.</p>
</aside>

<aside class="callout callout--note" aria-labelledby="exec-heading">
<h2 class="callout__title" id="exec-heading">Two things about <code>exec</code></h2>
<p>A successful <code>execvp</code> <strong>never returns</strong> — the program that
called it is gone, replaced. So any line after it runs only when it
<em>failed</em>, which is why the starter has a <code>perror</code> there.</p>
<p>And <code>execvp</code> replaces <em>whichever process calls it</em>. It does not
care that you meant the child.</p>
</aside>

## 7. Submitting

Commit and push. The autograder runs on every push, so push as often as you like
and read the result.

```bash
git add client.cpp
git commit -m "activity 2"
git push
```

A green check means the checks passed. A red X means they did not — open it and
read the message. Points are awarded per bug fixed, so a partly-fixed client is
worth partial credit.

| What the grader says | What it means |
| --- | --- |
| `does not compile` | Fix the error `g++` prints, then push again |
| `no worker ever ran` | `execvp` could not find the program it was given |
| `the client exec'd itself` | The exec is not guarded — the parent reached it too |
| `produced N worker lines, expected 4` | Some workers never started |
| `worker indices were …` | Each worker must be told its own index |
| `only N of 4 children were reaped` | One `wait()` collects one child |
| `nothing was reaped` | The client never called `wait()` |

## 8. If you finish early

None of this is submitted — it is here if you have time left.

- Delete the `perror`/`exit` pair after `execvp` and give the worker a name that
  does not exist. What does the child do now, and how many workers get reaped?
- Have the worker exit with `200 + index` instead. What does the client report,
  and why is it not what you wrote? (`man 2 wait`, and look at `WEXITSTATUS`.)
- Print something in the client immediately after `fork()` but outside the
  `if (pid == 0)`. How many times does it appear, and from which processes?
- Replace `wait()` with `waitpid()` so the children are reaped **in the order you
  started them**. Does the output become fully deterministic? Which part still is
  not, and why?
