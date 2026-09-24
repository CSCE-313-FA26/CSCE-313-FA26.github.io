---
layout: activity
title: "Activity 4 — Four Bugs in a FIFO Service"
activity_id: 4
activity_title: "Four Bugs in a FIFO Service"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Lab 3"
listed: false        # reachable by direct link, not shown in the index
duration: "30 minutes"
description: "A client and a server that talk over two named pipes are broken in four places. Find all four and fix them."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. What you are doing

Two programs talk over two FIFOs. The client sends a number, the server sends
back its double. Both compile cleanly, and together they are wrong in **four**
places.

Every one of the four is a mistake people actually make in Lab 3 — the same
`mkfifo`, `open`, `read` and `unlink` calls, in a program small enough to hold in
your head. You are debugging this pair so that this week you can debug your own
`FIFOChannel`.

There is no new material here. The lecture examples `fifo-server-1.c` and
`fifo-client-1.c` are where this pair came from.

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

What you **may** use: the Lab 3 handout, your own Lab 3 work, the lecture
examples, the `man` pages, and your notes. You may talk to the person next to you
about *ideas*. The code you submit must be yours.

## 3. Get your repository

1. Sign in to [classroom50.org](https://classroom50.org/) with your GitHub account.
2. Accept the activity:
   <https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/activity-4/accept>.
3. Clone it and build:

```bash
git clone https://github.com/CSCE-313-FA26/<your-activity-4-repository>.git
cd <your-activity-4-repository>
make
```

`make` builds two programs, `server` and `client`, with `gcc`. They are plain C.

## 4. What you are given

| Path | What it is |
| --- | --- |
| `server.c` | **Three** of the four bugs are here. |
| `client.c` | **One** of the four bugs is here. |
| `Makefile` | Builds both. Do not change it. |

Both `.c` files are yours to change. Do not change what either program prints —
the checks read those lines.

The two FIFOs are named `fifo_request` and `fifo_reply`, and the **server**
creates them. Keep those names.

## 5. What a correct run looks like

Two terminals, in the same directory. Start the server first — it is the one that
creates the FIFOs.

```console
$ ./server                          $ ./client
server: waiting for a client
server: 5 -> 10                     client: 5 -> 10
server: 4 -> 8                      client: 4 -> 8
server: 3 -> 6                      client: 3 -> 6
server: 2 -> 4                      client: 2 -> 4
server: 1 -> 2                      client: 1 -> 2
server: asked to quit               client: done
server: done
```

The client sleeps a second between requests, so this takes about five seconds.
After it, `ls` shows **no** `fifo_request` and **no** `fifo_reply`.

Four things have to be true, and each one is a separate bug:

1. The two programs **talk at all** — right now they both just sit there.
2. The server **stops when the client vanishes**, instead of spinning forever.
3. A clean run **removes both FIFOs**.
4. The server **starts even when a FIFO is already there**, as it is after a crash.

Fix them in that order. Until the first one is fixed nothing is exchanged, so the
other three have no symptoms to show you — and the grader cannot see them either.

## 6. How to work

Run it first. Do not read for bugs — let the pair tell you.

```bash
make
./server        # terminal 1
./client        # terminal 2
```

Nothing happens. Neither program prints a request or a reply, and neither exits.
That is the first bug, and section 4.3 of the Lab 3 handout describes it exactly.

<aside class="callout callout--note" aria-labelledby="open-heading">
<h2 class="callout__title" id="open-heading">Opening a FIFO waits for the other side</h2>
<p><code>open</code> on a FIFO for reading blocks until somebody opens it for
writing, and the other way round. So the <em>order</em> in which the two sides
open their two FIFOs is not a detail: if each side is waiting on a different
FIFO, both wait forever and nothing is printed at all.</p>
</aside>

When they are talking, work through the rest by asking what each one does to the
*next* run:

```bash
ls fifo_*            # what did the last run leave behind?
./server             # does it start when those are still there?
```

And, in a third terminal while a session is running:

```bash
kill -9 $(pgrep -x client)    # then watch the server
top -p $(pgrep -x server)     # is it idle, or burning a core?
```

<aside class="callout callout--note" aria-labelledby="eof-heading">
<h2 class="callout__title" id="eof-heading">What <code>read</code> returning 0 means</h2>
<p><code>read</code> returns <strong>0</strong> when every write end is closed —
end of file. It is not an error and not a short read to skip: there will never be
another byte. A loop that goes around again on 0 will go around again for ever.
Lab 3 asks you to turn exactly this case into a <code>FAILURE</code>.</p>
</aside>

All four fixes are small; none needs more than a line or two.

## 7. Submitting

Commit and push. The autograder runs on every push, so push as often as you like
and read the result.

```bash
git add server.c client.c
git commit -m "activity 4"
git push
```

Points are awarded per bug fixed, so a partly-fixed pair is worth partial credit.

| Check | Points |
| --- | --- |
| Both programs compile | 10 |
| The exchange completes with five correct replies | 35 |
| The server stops when the client vanishes | 20 |
| A clean run removes both FIFOs | 20 |
| The server starts when a FIFO is already there | 15 |

| What the grader says | What it means |
| --- | --- |
| `gcc failed` | Fix the error `gcc` prints, then push again |
| `the client printed no replies at all` | The two sides are opening the FIFOs in opposite orders |
| `still running 8 s after the client was killed` | The loop does not stop when `read` returns 0 |
| `left behind: fifo_request, fifo_reply` | Nothing removes the FIFOs |
| `the server quit because fifo_request already existed` | An existing FIFO is not an error |

Do not commit the built programs or the FIFOs — `.gitignore` already excludes them.

## 8. If you finish early

None of this is submitted — it is here if you have time left.

- Start two clients against one server. What does each one get, and why? (This is
  the reason Lab 3 says one FIFO-mode client per directory.)
- Delete the `fflush(stdout)` calls and run the server with its output piped into
  `cat`. Where do the lines go? (You saw this one in `practice-1`.)
- Send a number bigger than the server expects, or send three bytes instead of
  four. What does the server do with a partial message, and what would it take to
  survive one?
- Have the client, not the server, create the FIFOs. What has to change, and what
  happens if both create them?
