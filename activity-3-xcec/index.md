---
layout: activity
title: "Activity 3 — Say the Right Thing to the Right Server"
activity_id: 3
activity_title: "Say the Right Thing to the Right Server"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Lab 2"
listed: false        # reachable by direct link, not shown in the index
duration: "30 minutes"
description: "Two servers, one client. Build the right request for each action, read the response, and make the audit log come out exactly right."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. What you are doing

On Tuesday you got the plumbing right — fork, exec, reap. **All of that is given
to you here.** Both servers are already started and both channels are already
open.

What is left is the conversation. For each action the client has to build the
right `Request`, send it to the right server, read what comes back, and pass the
right part of that answer on to the audit log.

This is Lab 2 Task 3, which is worth 30 of the lab's 100 points and is where
people lose them.

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

What you **may** use: the Lab 2 handout, your own Lab 2 work, the `man` pages,
and your lecture notes. You may talk to the person next to you about *ideas*.
The code you submit must be yours.

## 3. Get your repository

1. Sign in to [classroom50.org](https://classroom50.org/) with your GitHub account.
2. Accept the activity:
   <https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/activity-3/accept>.
3. Clone it and build:

```bash
git clone https://github.com/CSCE-313-FA26/<your-activity-3-repository>.git
cd <your-activity-3-repository>
make
./client
```

Only `g++` is needed.

## 4. What you are given

| Path | What it is |
| --- | --- |
| `client.cpp` | **The only file you change.** Four `TODO`s. |
| `server.cpp` | Both servers, one binary, role chosen by `-r`. Correct — do not change. |
| `channel.h` | The `Request` and `Response` types. **Read this.** |
| `channel.cpp` | How a message crosses a socket. **You never need to open it.** |
| `expected.log` | The audit log your program has to produce |

You only have to read two things: the two structs in `channel.h`, and the
**logger's `switch`** near the bottom of `server.cpp`. That switch is the whole
puzzle — it decides what gets written, and from which field.

There is one binary, `./server`, run twice:

```bash
./server -r bank                  # the account
./server -r logger -f audit.log   # the audit log
```

Both are started for you.

## 5. The shape of every action

Every action is the same two steps. The login is written out in `client.cpp` as
a worked example:

```cpp
Response r = bank.send(Request(LOGIN, USER));
if (r.success) {
    printf("logged in as user %d\n", USER);
    logger.send(Request(LOGIN, USER));
}
```

Ask the bank. Check it worked. Tell the logger.

Notice that **the logger is sent the same `RequestType`**. It does not take a
message string — it works out what to write from the type and the fields you
give it, exactly like Lab 2's logging server.

## 6. What to write

Four `TODO`s in `client.cpp`, in order.

| # | Action | Print on success |
| --- | --- | --- |
| 1 | deposit 500 | `deposit ok, balance now <balance>` |
| 2 | withdraw 200 | `withdrawal ok, balance now <balance>` |
| 3 | check the balance | `balance is <balance>` |
| 4 | log out | `logged out` |

Use the balance **the bank sent back**, not a number you worked out yourself.

<aside class="callout callout--warn" aria-labelledby="balance-heading">
<h2 class="callout__title" id="balance-heading">Read the logger's <code>BALANCE</code> case before you write TODO 3</h2>
<p>A <code>Response</code> has a <code>balance</code> field. A <code>Request</code>
does not. So when you audit the balance check, look at which field the logger
actually prints, and put the bank's answer there.</p>
<p>Get this wrong and the console still looks perfect — only the log is wrong.
That is exactly how it fails in Lab 2, and it is why the log is what gets
graded.</p>
</aside>

## 7. Checking your work

```bash
make check
```

That runs the client and diffs your `audit.log` against `expected.log`. It
prints **MATCH** when you are done:

```
[7]: logged in
[7]: deposited 500
[7]: withdrew 200
[7]: viewed balance: 300
[7]: logged out
```

Run it as often as you like. The log is truncated at the start of every run, so
you never have to clean up between attempts.

## 8. Submitting

```bash
git add client.cpp
git commit -m "activity 3"
git push
```

The autograder runs on every push. Points are awarded per action, so a partly
finished client is worth partial credit.

| What the grader says | What it means |
| --- | --- |
| `does not compile` | Fix the error `g++` prints, then push again |
| `no sign of it` | That action was never sent to either server |
| `the bank was asked, but nothing was audited` | You skipped the `logger.send` |
| `logged "viewed balance: 0"` | TODO 3 — the bank's answer never reached the logger |
| `first difference on line N` | Your log and `expected.log` diverge there |

## 9. If you finish early

None of this is submitted — it is here if you have time left.

- Withdraw more than the balance. What does `r.success` come back as, what does
  the bank put in `message`, and what ends up in the log?
- Delete one `logger.send` and run `make check`. Which line of the diff moves,
  and why does every line after it look wrong too?
- Open `channel.cpp` after all. Find where `QUIT` is treated differently from
  every other request, and work out why the client would hang if it were not.
- The client reaps both servers with `while (wait(nullptr) > 0)`. Swap it for a
  single `wait(nullptr)` and run it a few times. What is left behind?
