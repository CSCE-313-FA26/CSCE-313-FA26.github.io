---
layout: activity
title: "Activity 6 — Parallel Pi"
activity_id: 6
activity_title: "Parallel Pi"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Lab 5"
listed: false        # reachable by direct link, not shown in the index
duration: "20 minutes"
description: "A program approximates pi with a Riemann sum, one rectangle at a time, on a single thread. Split the work across threads and make the shared total safe."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. What you are doing

A program approximates **π** by cutting the area under a curve into a billion
thin rectangles and adding them up. It works, and it is slow, because it does
everything on one thread.

You will parallelize it in two places:

- **Section 1** splits the billion rectangles across `NUM_THREADS` threads.
  Each thread owns its own slot in `sum[][]`, so nothing needs locking here.
- **Section 2** adds those partial sums into one shared `pi`. Every thread
  writes the *same* variable, so this one does need locking.

That contrast is the whole point of the exercise: **partition the data and you
need no synchronisation; share one variable and you do.**

**Work in pairs.** Sit with one partner and solve it together, talking through
each step. **Each of you accepts and pushes your own repository**, and each of
you is graded on your own push — so both partners get a score, and neither of
you is stuck if the other has to leave.

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

What you **may** use: the Lab 5 handout, your own Lab 5 work, your notes, the
`man` pages, and [cppreference](https://en.cppreference.com/) for `std::thread`
and `std::mutex`. You are working in a pair, so talking to your partner about
the code is expected. The code you push must be code the two of you wrote.

## 3. The maths, in one paragraph

You do not need to do any calculus here, but you should know what the program is
computing so the output means something to you.

The area under the curve `4 / (1 + x*x)` between `x = 0` and `x = 1` is exactly
π. That is the whole trick — integrating that one function over that one
interval gives `4 * arctan(1)`, which is π.

```
          1
         /       4
  pi =  |   ----------- dx
         /   1 + x * x
        0
```

The program approximates that integral with a **midpoint Riemann sum**: it cuts
`[0, 1]` into `num_steps` rectangles of width `step`, evaluates the height
`4 / (1 + x²)` at the **midpoint** of each one, adds the heights up, and
multiplies by `step` at the end. More rectangles means a closer answer; the
starter uses a billion of them, which is why Section 1 takes a few seconds.

If you want the longer version, it is written up here:
<https://dotink.co/posts/pi-by-riemann-sum/>.

## 4. Get your repository

1. Sign in to [classroom50.org](https://classroom50.org/) with your GitHub account.
2. Accept the activity:
   <https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/activity-6/accept>.
3. Clone it and build:

```bash
git clone https://github.com/CSCE-313-FA26/<your-activity-6-repository>.git
cd <your-activity-6-repository>
make
```

C++17, plain `g++`. A fresh clone **builds clean, with no warnings**. The build
uses `-Wall -Wextra` and AddressSanitizer, so keep it warning-free as you go.

You change **`main.h`** and **`main.cpp`**, and those are the only two files
graded. The `makefile` is replaced by the grader, so editing it changes nothing.

## 5. See the problem first

Run it before you change anything:

```bash
./main
```

```
Number of threads: 2
Cache padding for coherency: 64 bytes
---
Pi approximation: 0.000000
Time to complete part 1: 0.000001 seconds
Time to complete part 2: 2.000324 seconds
```

Two things to notice, and they are the two things you are going to fix:

- **`Pi approximation: 0.000000`.** Section 1 is empty, so no partial sum is
  ever computed and `sum[][]` is still all zeroes.
- **Part 2 takes 2 seconds.** The serial loop calls `sleep(1)` once per thread's
  worth of work, one after another. Two sleeps that *wait for each other* take
  two seconds. Two sleeps that *overlap* take one.

## 6. The four TODOs

They are numbered in the files. Do them in order — TODO 3 is the one that makes
π correct, and it is worth starting there.

| TODO | File | What it is |
| --- | --- | --- |
| 1 | `main.h` | Declare the synchronisation primitive Section 2 needs |
| 2 | `main.h` | Write `pi_sum_thread` — its parameters and its body |
| 3 | `main.cpp` | Section 1: run `single_sum_thread` on `NUM_THREADS` threads |
| 4 | `main.cpp` | Section 2: replace the serial loop with threads |

Three things that are easy to get wrong:

1. **Join every thread before the section ends.** If you read `sum[][]` or `pi`
   before the threads that write them have finished, you read a half-finished
   answer. This is the same mistake as a `ThreadPool` destructor that does not
   join.
2. **`pi` must be *shared*, not copied.** Every thread has to update the one
   `pi` in `main`, so pass it by pointer or by reference. A thread that updates
   its own copy changes nothing.
3. **Keep `sleep(1)` outside the critical section.** Lock, update `pi`, unlock,
   *then* sleep. If you hold the mutex across the sleep, the threads queue up
   waiting for it and part 2 takes 2 seconds again — you will have written
   threaded code that performs exactly like the serial loop.

## 7. What a correct run looks like

```
Number of threads: 2
Cache padding for coherency: 64 bytes
---
Pi approximation: 3.141593
Time to complete part 1: 4.190991 seconds
Time to complete part 2: 1.000955 seconds
```

`Pi approximation: 3.141593` and **part 2 at about one second** are the two
numbers that matter. Part 1's time depends on the machine and on how loaded it
is, so do not expect to match the number above — expect it to be a few seconds.

## 8. Submitting

```bash
git add main.h main.cpp
git commit -m "activity 6"
git push
```

The autograder runs on every push, so push as often as you like and read the
result. Points are awarded per behaviour, so partial work is worth partial
credit — a correct Section 1 on its own is worth 55.

| Check | Points |
| --- | --- |
| Builds with no errors | 10 |
| Section 1 computes the partial sums on real threads | 25 |
| π is correct | 20 |
| Section 2 runs the reduction concurrently | 25 |
| The shared `pi` update is free of data races | 20 |

| What the grader says | What it means |
| --- | --- |
| `g++ failed` | Fix the error `g++` prints, then push again |
| `never had more than 1 thread(s) running` | Section 1 is still empty — TODO 3 |
| `printed 0.000000` | Same thing: no partial sum was ever written |
| `threads were created but the work was not split` | You called `single_sum_thread` directly instead of handing it to a `std::thread` |
| `saw at most 1 thread(s) during the ... sleeping` | Section 2 is still the serial loop — TODO 4 |
| `took 2.02 s ... instead of about 1 s` | The mutex is held across `sleep(1)` — move the sleep out |
| `ThreadSanitizer found a data race` | TODO 1 and 2: the `pi` update needs a mutex |

**Nothing is graded by reading your source.** A threaded version and a serial
version print the same π, so the grader measures *behaviour* instead: it samples
the thread count and the CPU use in `/proc` while your program runs, times the
sleeping phase from outside, and re-runs your code under ThreadSanitizer to look
for the race. Any correct way of threading it scores full marks.

Do not commit the built program — `.gitignore` already excludes it.

## 9. If you finish early

None of this is submitted — it is here if you have time left.

- Raise `NUM_THREADS` to 4 and run it again. Part 1 should get faster up to the
  number of cores you have and then stop improving. Why?
- `PAD` exists to stop two threads' partial sums sharing a cache line. Set
  `PAD` to 1 and time part 1 again. The answer stays correct — only the speed
  changes. That is **false sharing**.
- Replace `mtx.lock()` / `mtx.unlock()` with `lock_guard<mutex>` in a scope of
  its own. It is shorter, and it still unlocks if the critical section throws.
- Make `pi` a `std::atomic<double>` and drop the mutex entirely. Does part 2
  still take one second?
