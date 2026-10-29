---
layout: activity
title: "Activity 6 — Parallel Pi"
activity_id: 6
activity_title: "Parallel Pi"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Lab 5"
listed: false        # reachable by direct link, not shown in the index
description: "A program approximates pi by adding up a billion rectangles on one thread. Split the work across threads, and make the shared total safe."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

**Background reading:** <https://dotink.co/posts/pi-by-riemann-sum/> — the method
this program uses, worked through from the beginning. Read it first if the
formula below is unfamiliar.

## 1. Description

You are given a working program that computes **π** to six correct decimal
places. It is correct and it is slow, because it does all of its work on a
single thread.

Your job is to parallelize it in two places, and those two places need
*different* things from you:

- **Section 1** divides a billion rectangles among `NUM_THREADS` threads. Each
  thread writes only to its own slot in the `sum` array, so **no locking is
  needed here at all.**
- **Section 2** adds those partial results into one shared variable, `pi`. Every
  thread writes *the same* variable, so **this one does need locking.**

That contrast is the point of the exercise. Dividing data between threads is
free; sharing one variable between threads costs you a mutex. Knowing which
situation you are in is most of what concurrency is.

**Work in pairs.** Sit with one partner and solve it together, talking through
each step. **Each of you accepts and pushes your own repository**, and each of
you is graded on your own push, so both partners receive a score and neither of
you is blocked if the other has to leave.

## 2. How the Program Approximates π

### 2.1 Where the formula comes from

The derivative of `arctan(x)` is `1 / (1 + x²)`, so integrating that function
from 0 to 1 gives `arctan(1) − arctan(0)`, which is `π/4 − 0`. Multiply through
by 4 and you have an integral whose exact value is π:

> **π = ∫₀¹ 4 / (1 + x²) dx**

Nothing about this is approximate yet. The approximation comes from how the
program evaluates that integral.

### 2.2 Turning the integral into a sum

An integral is the exact area under a curve. The program estimates that area the
way a **Riemann sum** does: slice the interval from 0 to 1 into `n` vertical
strips of equal width, treat each strip as a rectangle, and add up the
rectangles. More strips means thinner rectangles, which hug the curve more
closely, which means a better answer.

Two choices make this concrete:

- **The width of each rectangle** is `step = 1 / n`. In the code, `n` is
  `num_steps`, and it is **1,000,000,000** — a billion rectangles.
- **The height of each rectangle** is the curve's value at the **midpoint** of
  that rectangle's base, not at its left or right edge. For rectangle `i`, the
  midpoint sits at `x = (i + ½) × step`, so the height is `4 / (1 + x²)`.

Using the midpoint matters. A left-edge or right-edge rectangle sits entirely
below or entirely above a curve that is falling, so those errors all lean the
same way and accumulate. A midpoint rectangle overshoots the curve on one half
of its base and undershoots it on the other, and the two errors largely cancel.
That is why a midpoint sum is accurate enough to give six correct digits here.

Add the rectangles up and multiply by their shared width:

> **π ≈ step × Σ 4 / (1 + x²)**, summed over the `n` midpoints `x = (i + ½) × step`

### 2.3 How that maps onto the code

`single_sum_thread` is exactly that sum, and it is already written for you:

```cpp
for (long long int i = id; i < num_steps; i = i + num_threads)
{
    x = (i + 0.5) * step;              // the midpoint of rectangle i
    sum[id][0] += 4.0 / (1.0 + x * x); // its height
}
```

Two details worth noticing:

- **`step` is multiplied in at the very end**, not once per rectangle. Every
  rectangle has the same width, so `Σ (height × step)` equals
  `step × Σ height`. Factoring it out removes a billion multiplications. That
  final multiply is the `sum[id][0] * step` you will write in Section 2.
- **The loop strides by `num_threads`, not by 1.** Thread 0 takes rectangles
  0, 2, 4, …; thread 1 takes 1, 3, 5, …. Every rectangle is still counted
  exactly once, so the total is identical no matter how many threads you use —
  only the time changes. Each thread accumulates into `sum[id][0]`, its own
  slot, which is why Section 1 needs no mutex.

The answer does not depend on the number of threads. Verify that as you go: π
should read `3.141593` at one thread, at two, and at eight.

## 3. What You May Use

The Lab 5 handout, your own Lab 5 work, your notes, the
`man` pages, and [cppreference](https://en.cppreference.com/) for `std::thread`
and `std::mutex`. You are working in a pair, so discussing the code with your
partner is expected. The code you push must be code the two of you wrote.

## 4. Getting Your Repository

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

## 5. Running the Unmodified Program

Run it before changing anything:

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

- **`Pi approximation: 0.000000`.** Section 1 is empty, so no rectangle is ever
  computed and the `sum` array is still all zeroes. The program is adding up
  nothing.
- **Part 2 takes 2 seconds.** The serial loop calls `sleep(1)` once per thread's
  worth of work, one call after another. Two sleeps that *wait for each other*
  take two seconds; two sleeps that *overlap* take one.

## 6. The Four Tasks

They are marked `TODO 1` to `TODO 4` in the files. Do them in order. TODO 3 is
the one that makes π correct, so you will see progress soonest by starting
there, but TODO 1 and 2 are listed first because Section 2 cannot compile
without them.

### TODO 1 — declare the mutex (`main.h`)

One line, at file scope, next to the other globals.

Section 2 will run `pi_sum_thread` on several threads at once, and all of them
add into the same `pi`. A `+=` on a `double` is not one indivisible operation —
it is a load, an add, and a store. Two threads interleaving those steps can each
read the same old value and each write back their own total, and one of the two
contributions is simply lost. A `std::mutex` is what guarantees that one thread
finishes its load-add-store before another begins.

Declare it where every thread can reach it. A mutex local to the function would
give each thread its own, which protects nothing.

### TODO 2 — write `pi_sum_thread` (`main.h`)

The stub has **no parameters** and an empty body. You decide its signature, then
write three lines of real work. It needs four things:

| It needs | Why |
| --- | --- |
| which partial sum to add | so each thread handles a different slot of `sum` |
| the step size | the rectangle width that was factored out of the loop |
| the shared `pi` | **by pointer or by reference, never by value** — a thread that updates its own copy changes nothing the rest of the program can see |
| the `sum` array | to read its own partial result out of |

The body does one multiply and one add — `pi += sum[id][0] * step` — with the
mutex locked around it, and nothing else inside the lock.

**Leave `sleep(1)` outside the critical section.** It is already in the stub, at
the bottom. It stands in for a long-running task, and it is what makes the
difference between serial and parallel visible. If you hold the mutex while you
sleep, the other threads queue up waiting for it, part 2 takes 2 seconds again,
and you will have written threaded code that performs exactly like the serial
loop you replaced. **A critical section should contain the shared update and
nothing else.**

### TODO 3 — thread Section 1 (`main.cpp`)

Run the function you were given, `single_sum_thread`, on `NUM_THREADS` threads
instead of not at all. Three steps:

1. Make a `std::vector<std::thread>` to hold the thread objects. You need to
   keep them somewhere: a `std::thread` you never join and then destroy calls
   `std::terminate` and kills the program.
2. Start one thread per worker, passing each its own `id` from `0` to
   `NUM_THREADS - 1`, along with `nthreads` and `sum`. The `id` is what tells a
   thread which rectangles are its own and which slot to write.
3. **Join every thread before the section ends.** The partial sums are not all
   written until the last thread has finished, so reading `sum` before then
   reads a half-finished answer. This is the same requirement as a `ThreadPool`
   destructor that must join its workers.

No mutex anywhere in this section — each thread owns its slot.

### TODO 4 — thread Section 2 (`main.cpp`)

Replace the serial loop with `NUM_THREADS` threads running the `pi_sum_thread`
you wrote in TODO 2. Same three steps as TODO 3: a vector, a loop that starts
the threads, a loop that joins them.

Two things specific to this section:

- **Delete the serial loop** once your version works. Leaving it in means every
  partial sum is added twice and π comes out around 6.28.
- **The `sleep(1)` is already inside `pi_sum_thread`.** Do not add another one
  here.

Join these threads too. `pi` is not complete until the last one has returned,
and the `printf` that follows reads it.

## 7. Expected Output

```
Number of threads: 2
Cache padding for coherency: 64 bytes
---
Pi approximation: 3.141593
Time to complete part 1: 4.190991 seconds
Time to complete part 2: 1.000955 seconds
```

`Pi approximation: 3.141593` and **part 2 at about one second** are the two
results that matter. Part 1's time depends on the machine and on how many other
people are logged into it, so do not expect to match the number above — expect
it to be a few seconds.

## 8. Cache Lines and False Sharing

This section is not graded and nothing here needs changing. It explains the
strangest line in the program, and it is the reason the `sum` array has a second
dimension that is never used.

### 8.1 Why `sum` is two-dimensional

The array is declared `double sum[NUM_THREADS][PAD]`, with `PAD` set to 8, and
every thread only ever touches `sum[id][0]`. Seven of every eight doubles are
**deliberately wasted**. `sum[NUM_THREADS]` would hold every value the program
actually reads.

That waste buys speed, and to see why you need to know how a CPU reads memory.

### 8.2 Caches move lines, not bytes

A CPU never fetches a single byte from RAM. It fetches a fixed-size block called
a **cache line** — **64 bytes** on every x86-64 machine you will use — and
stores the whole line in its cache. Ask for one `double` and you get the 64-byte
line containing it, which is eight `double`s.

That is what the program's second output line reports:

```
Cache padding for coherency: 64 bytes
```

`PAD * 8` is 8 doubles × 8 bytes = **64 bytes**, exactly one cache line. So
`sum[0]` fills one line and `sum[1]` fills the next, and the two threads'
accumulators land in **different** lines.

### 8.3 Why that matters: cache coherency

Each core has its own cache, so the same line can sit in several caches at once.
The hardware has to keep those copies consistent, and the rule it enforces is
blunt: **when one core writes to a line, every other core's copy of that line is
invalidated.** Any core that wants it again must re-acquire it.

Now put both accumulators in one line, which is what `PAD = 1` does — `sum[0][0]`
and `sum[1][0]` end up 8 bytes apart, comfortably inside the same 64 bytes. The
inner loop of `single_sum_thread` writes its accumulator on **every one of five
hundred million iterations**, so:

1. Core 0 writes `sum[0][0]`. Core 1's copy of the line is invalidated.
2. Core 1 writes `sum[1][0]`. It must re-acquire the line, and now core 0's copy
   is invalidated.
3. Repeat, hundreds of millions of times.

The line ping-pongs between the two caches, and each bounce costs far more than
the arithmetic it is protecting.

### 8.4 Why it is called *false* sharing

Nothing is actually shared. Thread 0 never reads or writes thread 1's
accumulator, and vice versa. There is no race, no missing mutex, and the answer
is correct to the last digit. The two cores are fighting over **the line that
happens to contain both variables**, not over any value either of them uses.
Hence *false* sharing: the contention is an artifact of memory layout, not of
the program's logic.

This is why it is such a nasty class of bug. It never produces a wrong answer,
so no test catches it — it only makes correct code slow, and it is invisible in
the source. `sum[id][0] += …` looks completely private, and it is. The problem
is the address it lands on.

### 8.5 What it costs, measured

Same program, same two threads, same correct answer, only `PAD` changed:

| `PAD` | Layout | Part 1 |
| --- | --- | --- |
| 1 | both accumulators in one cache line | 2.856 s |
| 8 | each accumulator in its own line | 2.054 s |

**A 39% penalty, 1.39× slower**, for a layout difference of 56 unused bytes.

One caveat on reproducing this: the build uses no optimisation, so every `+=`
really is a load and a store to memory. With `-O2` the compiler would likely
keep the accumulator in a register for the whole loop and write it back once,
which hides the effect entirely. False sharing bites hardest on code that
repeatedly writes to memory that other cores also hold.

The general rule: **when threads write to nearby memory, pad the data so each
thread's part gets its own cache line.** Lay out per-thread state so that
threads working independently also *touch memory* independently.

## 9. Measured Results

Three runs of each configuration, median reported, on a 2-core machine.

**Section 2 is exact, and the same on every machine.** `sleep(1)` uses no CPU,
so N sleeps that overlap take one second however many cores you have:

| Threads | Serial loop | Threaded | Speedup |
| --- | --- | --- | --- |
| 2 | 2.0003 s | 1.0004 s | **2.00×** |
| 4 | 4.0005 s | 1.0004 s | **4.00×** |

The spread across runs was 0.2 **milliseconds**. This is why the grader checks
part 2's duration and not part 1's.

**Section 1 is bounded by the number of cores available.** It is real work, so
threads only help while there is a free core to run them on:

| Threads | Part 1 | Speedup |
| --- | --- | --- |
| 1 | 3.875 s | 1.00× |
| 2 | 2.118 s | 1.83× |
| 4 | 1.970 s | 1.97× |
| 8 | 2.023 s | 1.91× |

**Your absolute times will not match these** — they depend on the machine, its
core count and how many other people are using it. What should hold everywhere
is the *shape*: part 1 improves up to roughly the number of cores available and
then flattens, while part 2 drops to one second and stays there. Run `nproc` to
see your core count, and check the shape against it.

Across all of these runs π was `3.141593` every time. Threading changed the
time, never the answer.

## 10. Submitting

```bash
git add main.h main.cpp
git commit -m "activity 6"
git push
```

The autograder runs on every push, so push as often as you like and read the
result. Points are awarded per behaviour, so partial work earns partial credit —
a correct Section 1 on its own is worth 55.

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
| `printed 0.000000` | Same thing: no rectangle was ever computed |
| `threads were created but the work was not split` | You called `single_sum_thread` directly instead of handing it to a `std::thread` |
| `saw at most 1 thread(s) during the ... sleeping` | Section 2 is still the serial loop — TODO 4 |
| `took 2.02 s ... instead of about 1 s` | The mutex is held across `sleep(1)` — move the sleep out |
| `ThreadSanitizer found a data race` | TODO 1 and 2: the `pi` update needs a mutex |

**Nothing is graded by reading your source.** A threaded version and a serial
version print the same π, so the grader measures *behaviour* instead: it samples
the thread count and CPU use in `/proc` while your program runs, times the
sleeping phase from outside, and re-runs your code under ThreadSanitizer to look
for the race. Any correct way of threading it earns full marks.

Do not commit the built program — `.gitignore` already excludes it.

## 11. Optional Extensions

None of this is submitted — it is here if you have time left.

- Raise `NUM_THREADS` to 4 and 8 and time part 1 on *your* machine. Compare the
  point where it flattens against `nproc`. Why does it flatten there, and why
  can 8 threads come out slightly *slower* than 4?
- Set `PAD` to 1 and time part 1 again, then re-read section 8. Confirm the
  answer is still correct and only the time moved.
- Replace `mtx.lock()` / `mtx.unlock()` with `lock_guard<mutex>` in a scope of
  its own. It is shorter, and it still unlocks if the critical section throws.
- Make `pi` a `std::atomic<double>` and drop the mutex entirely. Does part 2
  still take one second?
- Build without the sanitizers (`g++ -std=c++17 -O2 -pthread -o main main.cpp`)
  and time part 1 again. AddressSanitizer roughly doubles it — a fair price for
  what it catches, but worth knowing when you measure.
