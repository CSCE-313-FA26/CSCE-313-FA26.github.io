---
layout: activity
title: "Activity 1 — Watch a Process Split"
activity_id: 1
activity_title: "Watch a Process Split"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Lab 1"
duration: "30 minutes"
description: "Use GDB to watch what fork() returns in each process, then write the fork loop that starts four workers."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. What you are doing

Lab 1 taught you to drive GDB on a program that was standing still. This
activity points those same commands at a program that **splits in two**.

`fork()` is called once and returns twice — once in each process. That sentence
is easy to say and hard to believe until you have watched it happen. Part A puts
a breakpoint just after a `fork()` and has you read the return value in both
processes. Part B then asks you to write a fork loop of your own.

Two parts, about fifteen minutes each.

## 2. Rules

**No artificial intelligence.** You may not use Copilot, ChatGPT, Claude, Gemini
or any other code-generating assistant during this activity. Disable AI code
completion in your editor before you begin. This applies to every student in
every section.

You may read the Lab 1 handout, your own Lab 1 work, the `man` pages, and your
lecture notes. You may talk to the person next to you about *ideas*. The code
you submit must be yours.

## 3. Get your repository

1. Sign in to [classroom50.org](https://classroom50.org/) with your GitHub account.
2. Accept the activity:
   <https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/activity-1/accept>.
   Your repository is created for you.
3. Clone it and build:

```bash
git clone https://github.com/CSCE-313-FA26/<your-activity-repository>.git
cd <your-activity-repository>
make
```

Both programs must compile before you start. If they do not, fix that first —
ask, rather than losing ten minutes to it.

<aside class="callout callout--note" aria-labelledby="roster-heading">
<h2 class="callout__title" id="roster-heading">If accepting fails</h2>
<p>If your name is missing from the roster, or you signed in with the wrong
GitHub account, tell the instructor or a TA now — do not create a second
account.</p>
</aside>

## 4. What you are given

| Path | What it is |
| --- | --- |
| `observe.cpp` | A small, **correct** fork program. Part A debugs it. Do not change it. |
| `spawn.cpp` | Starts four workers. **One TODO — that is your work.** |
| `Makefile` | Builds both, with `-g`, the same way Lab 1 did |
| `deliverables/` | Where your Part A transcript goes |

The loop that reaps the children in `spawn.cpp` is already written. Reaping is
not what this activity is testing, and it would eat the half hour.

## 5. Part A — what does `fork()` return?

`observe.cpp` forks once. Both processes then reach the line marked

```cpp
    if (pid < 0) {              /* <== ACTIVITY: break here (line 17) */
```

Record the whole of Part A as one transcript, the same way you did in Lab 1:

```bash
script -q deliverables/part-a.txt
```

Then run GDB **twice**, without leaving the recording.

**Run 1 — GDB follows the parent.** This is the default.

```console
$ gdb ./observe
(gdb) break 17
(gdb) run
(gdb) print pid
(gdb) print counter
(gdb) continue
(gdb) quit
```

**Run 2 — tell GDB to follow the child instead.**

```console
$ gdb ./observe
(gdb) set follow-fork-mode child
(gdb) break 17
(gdb) run
(gdb) print pid
(gdb) print counter
(gdb) continue
(gdb) quit
```

Then stop the recording:

```bash
exit
```

`print pid` gives you a different answer in the two runs. That difference is the
whole point of the exercise: **the parent is told the child's PID, and the child
is told `0`.** It is the only way each process can know which one it is.

<aside class="callout callout--note" aria-labelledby="counter-heading">
<h2 class="callout__title" id="counter-heading">Why `counter` reads 7 both times</h2>
<p>You stopped <em>before</em> either process changed it. Let the program finish
and the two printed values differ, because each process is working on its own
copy. Neither can see the other's.</p>
</aside>

## 6. Part B — start four workers

Open `spawn.cpp`. There is one `TODO` inside the loop in `main()`. Fill it in so
that each pass forks one child, and each child prints exactly one line:

```
worker <i> pid <its own pid> parent <its parent's pid>
```

and then leaves with `exit(i)`.

Four things are checked, all by running your program:

1. It compiles.
2. Exactly **four** workers run.
3. The indices are 0, 1, 2 and 3, every worker reports a different PID, and every
   worker's parent is the spawner.
4. The spawner reaps four children, with exit codes 0, 1, 2 and 3.

<aside class="callout callout--warn" aria-labelledby="exit-heading">
<h2 class="callout__title" id="exit-heading">The mistake almost everyone makes once</h2>
<p>If the child does not <code>exit()</code>, it carries on round the loop and
forks again — and so do <em>its</em> children. You get fifteen workers instead of
four. If your output is far longer than you expected, this is why.</p>
</aside>

The functions you need are `fork()`, `getpid()`, `getppid()` and `exit()`. You do
not need anything else, and you do not need `exec` — we have not covered it.

## 7. Running it

```bash
make
./spawn
```

Correct output looks like this. Your PIDs will differ, and the lines may
interleave in a different order — that is normal, and not a mistake:

```console
spawner pid 4021 starting 4 workers
worker 0 pid 4022 parent 4021
worker 1 pid 4023 parent 4021
worker 2 pid 4024 parent 4021
worker 3 pid 4025 parent 4021
spawner reaped pid 4022 exit 0
spawner reaped pid 4023 exit 1
spawner reaped pid 4024 exit 2
spawner reaped pid 4025 exit 3
spawner done, reaped 4
```

You are done when you see four workers and `reaped 4`.

## 8. Submitting

Commit and push. The autograder runs on every push, so you can push as often as
you like and read the result.

```bash
git add spawn.cpp deliverables/part-a.txt
git commit -m "activity 1"
git push
```

A green check on your commit means the checks passed. A red X means they did
not — open it and read the message.

| What the grader says | What it means |
| --- | --- |
| `does not compile` | Fix the error `g++` prints, then push again |
| `produced N worker lines, expected 4` | Your child is not calling `exit()` |
| `reaped exit codes were …` | Each child must `exit(i)`, not `exit(0)` |
| `part-a.txt not found` | The transcript is missing, or not in `deliverables/` |
| `does not show GDB following the child` | Run 2 was not recorded, or `follow-fork-mode` was not set |

## 9. If you finish early

None of this is submitted — it is here if you have time left.

- In `spawn.cpp`, print something in the parent immediately after the fork as
  well. Run it several times. Does the parent's line always come before the
  child's? What does that tell you about who runs first?
- In Part A run 2, after the breakpoint hits, type `info inferiors`. GDB is
  holding two processes. What is it telling you about each?
- Delete the `exit(i)` from your child on purpose and count the workers. Predict
  the number before you run it. (It is not sixteen.)
- Change `N_WORKERS` to 1 and step through the fork with `next` instead of
  `continue`. Which process does GDB keep, and which one runs free?
