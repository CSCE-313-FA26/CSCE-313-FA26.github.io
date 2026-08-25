---
layout: lab
title: "Lab 1 — Debugging with GDB"
lab_number: 1
lab_title: "Debugging with GDB"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
instructor: "David Kebo Houngninou"
released: "Tuesday, August 25, 2026, 9:00 AM CT"
due: "Tuesday, September 8, 2026, 11:59 PM CT"
released_short: "Tue Aug 25, 2026"
due_short: "Tue Sep 8, 2026, 11:59 PM CT"
description: "Use GDB to inspect a running C++ banking system, then find and fix five memory and control-flow defects in it."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Objectives

By the end of this lab you will be able to:

1. Set breakpoints by line, by file and line, and by function name.
2. Inspect object state, memory, and type layout while a program is stopped.
3. Watch a variable and stop the moment it changes.
4. Read a call stack and use it to locate the origin of a crash.
5. Interrupt a running program and take control of it in the debugger.
6. Diagnose and repair uninitialized memory, runaway recursion, buffer
   overflow, memory leaks, and an invalid `delete`.
7. Recognise the Rule of Three: why a class that owns raw memory must define how
   it is created, copied, and destroyed, and what breaks when it does not.
8. Use compiler warnings and AddressSanitizer to find memory faults that a
   debugger alone would not reveal.

## 2. Background

### 2.1 The banking system program

You are given a small C++ banking system: it presents a text menu, and lets you
log in as a numbered user, deposit, withdraw, and view a balance. You are not
asked to add features to it. It exists so that you have a real program with real
state to point a debugger at.

The lab is in two parts, and they use **two different copies** of the program.

| Part | Directory | Its purpose |
| --- | --- | --- |
| Part 1 | `part-1/` | Works correctly. You practise driving GDB on it. |
| Part 2 | `part-2/` | Contains five deliberate defects. You find and fix them. |

The two copies are not identical, and their menus differ. Part 1 offers seven
options and exits on `0`. Part 2 offers six and exits on `6`. Read the menu the
program actually prints rather than assuming.

<aside class="callout callout--note" aria-labelledby="two-programs-heading">
<h2 class="callout__title" id="two-programs-heading">These are separate programs</h2>
<p>Changes you make in <code>part-2/</code> have no effect on <code>part-1/</code>,
and the reverse. Each directory has its own <code>Makefile</code> and builds its
own <code>banking-system</code> executable.</p>
</aside>

### 2.2 GDB command reference

These are the commands used in this lab. The short form is in parentheses.

| Command | What it does |
| --- | --- |
| `gdb ./banking-system` | Start GDB on the executable |
| `run` (`r`) | Start the program |
| `break N` (`b N`) | Break at line `N` of the main source file |
| `break file.cpp:N` | Break at line `N` of a named file |
| `break Class::function` | Break on entry to a method |
| `break file.cpp:function` | Break on a function, named by file |
| `info breakpoints` (`i b`) | List breakpoints |
| `delete N` | Delete breakpoint `N` |
| `continue` (`c`) | Resume until the next stop |
| `next` (`n`) | Run the next line, stepping over calls |
| `step` (`s`) | Run the next line, stepping into calls |
| `finish` | Run until the current function returns |
| `list` | Show source around the current line |
| `print expr` (`p`) | Print a variable or expression |
| `p/x expr` | Print in hexadecimal |
| `ptype T` | Print the definition of a type |
| `whatis expr` | Print the type of an expression |
| `x/NFU addr` | Examine memory: `N` units, format `F`, unit size `U` |
| `watch expr` | Stop when `expr` changes value |
| `backtrace` (`bt`) | Show the call stack |
| `bt full` | Show the call stack with local variables |
| `info locals` | Show locals in the current frame |
| `quit` (`q`) | Leave GDB |

For `x`, the format letter `x` means hexadecimal and `s` means string; the unit
letter `b` means byte and `w` means four-byte word. So `x/24xb &v` reads 24
bytes from `&v` in hex, and `x/6xw &v` reads the same region as six words.

## 3. Environment setup

### 3.1 Accept the assignment

Accept the assignment on classroom50:

<https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/lab-1/accept>

You will need to be signed in. Accepting creates a private repository for you in
the course organization. Clone it:

```bash
git clone https://github.com/CSCE-313-FA26/<your-repository>.git
cd <your-repository>
```

### 3.2 Repository layout

| Path | Contents |
| --- | --- |
| `part-1/` | The working program: `main.cpp`, `bank.cpp`, `types.h`, `Makefile` |
| `part-2/` | The defective program: same four files, different contents |
| `deliverables/` | Where your session transcripts go |

### 3.3 Build the program

Build each part from inside its own directory:

```bash
cd part-1
make
```

That runs `g++ -std=c++17 -g main.cpp bank.cpp -o banking-system` and produces
an executable named `banking-system`. The `-g` flag is what puts debugging
symbols in the binary; without it GDB cannot show you source lines or variable
names.

The build should print the compiler command and nothing else. Any warning or
error means something is wrong before you have started debugging — fix it first.

<aside class="callout callout--warn" aria-labelledby="rebuild-heading">
<h2 class="callout__title" id="rebuild-heading">Rebuild after every edit</h2>
<p>GDB runs the executable, not your source. If you edit a file and do not run
<code>make</code> again, you are debugging the previous build and your change
appears to have done nothing — the single most common way to lose an afternoon
on this lab.</p>
<p>The <code>Makefile</code> lists <code>types.h</code> as a prerequisite, so
editing it does trigger a rebuild. If you ever suspect otherwise, settle it with
<code>make clean &amp;&amp; make</code>.</p>
</aside>

### 3.4 The first time you run GDB

On its first `run`, GDB may ask:

```console
This GDB supports auto-downloading debuginfo from the following URLs:
  <https://debuginfod.ubuntu.com>
Enable debuginfod for this session? (y or [n])
```

Answer `n`. You do not need external debug info for this lab, and declining
avoids a slow download. To stop it asking, add `set debuginfod enabled off` to
your `~/.gdbinit`.

### 3.5 Restart GDB between tasks

Each task below assumes a clean session. Leftover breakpoints and watchpoints
from a previous task will change what you see and make your output hard to
grade. Quit with `q` and start GDB again for each task.

### 3.6 Record each task as a transcript

Every task below asks you to save its output. You submit **plain-text
transcripts**, not screenshots. A transcript is easier for you to check before
submitting, it can be searched and diffed, and nothing is lost to a bad crop or
an unreadable font.

Use `script`, which records everything that appears in your terminal — the
program's own output, the commands you type, and GDB's replies:

```bash
script -q deliverables/part-1-task-1.txt
gdb ./banking-system
# ...carry out the task...
(gdb) quit
exit
```

The first command starts recording and the final `exit` stops it. Check the file
before moving on:

```bash
cat deliverables/part-1-task-1.txt
```

<aside class="callout callout--note" aria-labelledby="script-heading">
<h2 class="callout__title" id="script-heading">Two things to know about `script`</h2>
<p>You must run <code>exit</code> at the end, or the file stays incomplete.
And because <code>script</code> records a real terminal, the file may contain a
few stray control characters; that is expected and does not need cleaning up.</p>
</aside>

An alternative, if you prefer GDB to do the recording, captures GDB's side only
— the program's own menus and prompts will be missing, so `script` is the better
choice for this lab:

```console
(gdb) set trace-commands on
(gdb) set logging file deliverables/part-1-task-1.txt
(gdb) set logging enabled on
```

## 4. Walkthrough

This part uses `part-1/`, which works correctly. Work through each task and
capture the output described. Build first:

```bash
cd part-1
make
```

### 4.1 Task 1 — Inspecting an object and its type

Break at the top of the menu loop, then look at the account array.

```console
$ gdb ./banking-system
(gdb) break 35
(gdb) run
(gdb) ptype Account
(gdb) print bank.accounts[0]
```

Line 35 is inside `main`, after `Bank bank;` has been constructed, so `bank` is
in scope. `ptype` prints the structure of the type; `print` prints the value of
one element. A freshly constructed account reads `id = -1`, `balance = 0`,
`active = false`.

Save the transcript as **`part-1-task-1.txt`**.

### 4.2 Task 2 — Several breakpoints, and watching a variable

First set three breakpoints and confirm where they landed.

```console
$ gdb ./banking-system
(gdb) break main
(gdb) b 35
(gdb) b bank.cpp:7
(gdb) info breakpoints
```

`bank.cpp:7` is the first line of `Bank::login`, so GDB reports it as
`in Bank::login(int)`. Naming a function by its file and line is useful when a
name is ambiguous or you want a specific overload.

Save the transcript as **`part-1-task-2-1.txt`**.

Now watch the loop control variable and let the program run.

```console
(gdb) run
(gdb) watch running
(gdb) c
```

`running` is the `bool` that keeps the menu loop alive. A watchpoint stops the
program the moment its value changes, reporting the old and new values — so
choosing `Exit` from the menu will stop you at the assignment that ends the
loop, without your having guessed which line that was.

Save the transcript as **`part-1-task-2-2.txt`**.

### 4.3 Task 3 — Stepping and examining memory

Step into a call, look around, and step back out.

```console
$ gdb ./banking-system
(gdb) b 35
(gdb) run
(gdb) step
(gdb) list
(gdb) finish
```

`step` enters `print_menu()`; `list` shows the surrounding source; `finish` runs
to the end of the function and returns you to the caller.

Save the transcript as **`part-1-task-3-1.txt`**.

Now read the same object three different ways to see how it is laid out.

```console
(gdb) x/24xb &bank.accounts[0]
(gdb) x/6xw &bank.accounts[0]
(gdb) print bank.accounts[0]
```

The first reads 24 raw bytes, the second reads the same region as six four-byte
words, and the third asks GDB to interpret those bytes as an `Account`. Compare
them: the field boundaries, the padding the compiler inserted, and the byte
order are all visible in the raw views but hidden by the structured one.

Save the transcript as **`part-1-task-3-2.txt`**.

### 4.4 Task 4 — Reading a call stack

Break on `login`, then drive the program to it through the menu.

```console
$ gdb ./banking-system
(gdb) b bank.cpp:login
(gdb) run
```

At the menu, choose `1` to log in, then enter user ID `0`. GDB stops on entry to
`Bank::login`. Now look at the stack:

```console
(gdb) backtrace
(gdb) bt full
```

`backtrace` shows the chain of calls that got you here — frame `#0` is
`Bank::login`, frame `#1` is the line in `main` that called it. `bt full` adds
the local variables of each frame, so you can see `id`, `choice`, the whole
`bank` object, and `running` in `main`'s frame.

Save the transcript as **`part-1-task-4.txt`**.

### 4.5 Task 5 — Interrupting a running program

So far you have stopped the program at breakpoints you set in advance. This time
you will take control of a program that is already running.

Start it with no breakpoints and log in as user `0`:

```console
$ gdb ./banking-system
(gdb) run
```

At the menu choose `1`, then enter user ID `0`. The program prints
`Logged in as user 0` and returns to the menu.

Now, while it is waiting for your menu choice, press <kbd>Ctrl</kbd>+<kbd>C</kbd>.
That interrupts the program and drops you back to the GDB prompt. Set a
breakpoint and resume:

```console
(gdb) b main.cpp:76
(gdb) c
```

Line 76 is `if (amount > 0) {` in the deposit branch — the line immediately
before the balance is updated. Continuing returns you to the menu prompt you
interrupted. Choose `2` to deposit, and enter `100.00`.

You will stop at line 76. Now watch the balance and step until it changes:

```console
(gdb) watch bank.accounts[0].balance
(gdb) next
```

Keep issuing `next` until the watchpoint fires and reports the old and new
balance. Your transcript must include the watchpoint output — stopping before it
triggers is the most common way to lose points on this task.

Save the transcript as **`part-1-task-5.txt`**.

## 5. To-do

This part uses `part-2/`, which contains five deliberate defects. For each one:
reproduce the failure under GDB, capture the evidence, then fix the source,
rebuild, and confirm the failure is gone.

```bash
cd part-2
make
```

Fix the defects **in the order given**. They compound: until the first is fixed
the program cannot reach the code paths the later tasks exercise.

<aside class="callout callout--warn" aria-labelledby="pin-heading">
<h2 class="callout__title" id="pin-heading">Do not change the constants until you are told to</h2>
<p><code>MAX_TRANSACTIONS</code> ships set to <code>2</code>. Task 3 depends on
that value. Task 4 asks you to raise it to <code>100</code>. If you raise it
early, Task 3 will not reproduce.</p>
</aside>

### 5.1 Task 1 — Uninitialized transaction array

Run the program, log in as user `0`, and deposit `100`. It crashes with a
segmentation fault.

```console
(gdb) run
(gdb) backtrace
```

The backtrace points into `Account::addTransaction`, at the first line that
writes through the `transactions` pointer. Work out why that pointer is not
valid at that moment.

**Fixing this requires a change in more than one place.** The array must be
valid on every path that produces a usable `Account`, and there is more than one
such path in `types.h`. If you fix only the first one you find, the program will
crash in exactly the same way — that is the signal that you have not found them
all.

Save the transcript as **`part-2-task-1.txt`**, showing the crash and the backtrace at the
crash point.

### 5.2 Task 2 — Runaway recursion in login

Log in with user ID `1`. The program dies almost immediately.

First watch the recursion happen. Break on the function and log in as user `1`:

```console
(gdb) break Bank::login
(gdb) run
```

Choose `1` and enter user ID `1`. You stop on entry to `Bank::login`. Continue a
few times and watch the argument:

```console
(gdb) continue
(gdb) continue
(gdb) continue
```

Each stop reports a larger `id` — 1, then 2, then 3 — so the function is calling
itself with a new account each time and never returning.

You will not reach the crash this way: the breakpoint stops execution at every
level, and there are more levels than you could continue through by hand. So
remove the breakpoint and let it run:

```console
(gdb) delete 1
(gdb) continue
```

Now it crashes. The stack is far too large to print in full, so ask for the
oldest frames only:

```console
(gdb) bt -12
```

`bt -12` shows the last twelve frames rather than the first. You will see the
`id` counting *down* toward 1 and finally `main` — the bottom of the recursion,
with tens of thousands of identical frames stacked above it. The exact depth
depends on your machine's stack limit, so do not expect a particular number;
what matters is the repeating frame pattern and that it does not terminate.

Note that logging in as user `0` does not trigger this, which is a clue about
the condition guarding the recursive call.

Save the transcript as **`part-2-task-2.txt`**, showing the `id` climbing at the
breakpoint, the crash after you delete it, and the repeated recursive frames.

### 5.3 Task 3 — Buffer overflow in addTransaction

With Task 1 fixed, deposits work. Deposit repeatedly and the program eventually
dies.

```console
(gdb) break Account::addTransaction
(gdb) run
(gdb) print transactionCount
(gdb) print MAX_TRANSACTIONS
(gdb) continue
```

Print `transactionCount` each time the breakpoint is hit. It starts at `0` and
rises by one per deposit, while `MAX_TRANSACTIONS` stays at `2`.

The **third** deposit is the first one that writes past the end of the array.
Note what it does *not* do: it does not crash, and the program still reports the
deposit as successful. The write silently corrupts memory beyond the array, and
the program only dies later, when that corruption is discovered — typically on
the next allocation. This gap between the mistake and the symptom is the point
of the exercise.

Add the bounds check that prevents the out-of-range write.

Save the transcript as **`part-2-task-3.txt`**, showing the GDB output at the overflow and the
values of `transactionCount` and `MAX_TRANSACTIONS`.

### 5.4 Task 4 — Memory leak in the transaction descriptions

Each `Transaction` holds a `char* description` allocated with `new char[]`.
Nothing ever frees it.

First raise the limit so there is room to observe several transactions:

```cpp
const int MAX_TRANSACTIONS = 100;
```

Then break on `addTransaction` and inspect the transactions as they accumulate:

```console
(gdb) break Account::addTransaction
(gdb) run
(gdb) print transactions[0]
(gdb) print transactions[0].description
(gdb) x/s transactions[0].description
(gdb) continue
```

After three deposits, compare all three descriptions and their addresses:

```console
(gdb) print transactions[0].description
(gdb) print transactions[1].description
(gdb) print transactions[2].description
(gdb) p/x &transactions[0]
(gdb) p/x transactions[0].description
(gdb) p/x transactions[1].description
(gdb) p/x transactions[2].description
(gdb) x/32xb &transactions[0]
```

Every description sits at its own address, and none of those allocations is ever
released. Fix the ownership: whatever allocates must also free, and the array of
transactions itself needs releasing too.

Save the transcript as **`part-2-task-4.txt`**, showing the several transaction descriptions and
the memory examination of the transaction array.

### 5.5 Task 5 — Invalid delete in logout

Log in, then log out. The program aborts, and the C library prints a diagnostic
naming the problem.

```console
(gdb) break Bank::logout
(gdb) run
(gdb) print current_account
(gdb) x/x current_account
```

Compare the value of `current_account` with the address of the accounts array.
`logout()` calls `delete` on that pointer. Ask yourself what allocated the object
it points at, and whether `delete` is entitled to free it.

<aside class="callout callout--note" aria-labelledby="delete-heading">
<h2 class="callout__title" id="delete-heading">Read the abort message</h2>
<p>The exact wording the C library prints tells you which rule was broken, and
it is not the same message you would get for freeing the same pointer twice. Put
that message in your transcript.</p>
</aside>

Save the transcript as **`part-2-task-5.txt`**, showing the abort and the examination of
`current_account`.

### 5.6 Cross-check your work with the compiler

GDB is a microscope: it shows you what a program is doing once you know roughly
where to look. Two other tools work the other way round — they find the problem
and hand you the location. Neither replaces the debugging you just did, but
knowing they exist will save you hours later in this course.

**Ask the compiler about your class design.** From `part-2`, on the code as it
shipped:

```bash
g++ -std=c++17 -Weffc++ -c bank.cpp -o /dev/null
```

Among the warnings you will see:

```console
warning: 'class Account' has pointer data members [-Weffc++]
warning:   but does not declare 'Account(const Account&)' [-Weffc++]
warning: 'Account::transactions' should be initialized in the member
         initialization list [-Weffc++]
```

Those two warnings describe Tasks 1, 4 and 5 between them. They are all the same
underlying problem: **a class that owns raw memory must say what happens when it
is created, copied, and destroyed.** In C++ that expectation has a name — the
*Rule of Three* — and a class with a raw pointer member that declares none of
those three operations is almost always broken in the ways you just debugged.

**Ask the runtime to check every memory access.** Rebuild with
AddressSanitizer and run the program the same way you did in Task 1:

```bash
g++ -std=c++17 -g -fsanitize=address,leak -o banking-asan main.cpp bank.cpp
./banking-asan
```

On the unfixed code, instead of a bare "Segmentation fault" you get the fault
classified and located:

```console
ERROR: AddressSanitizer: SEGV on unknown address 0x000000000000
    #0 ... in Account::addTransaction(double, char const*) types.h:56
```

`0x000000000000` is the giveaway: the program followed a null pointer, which is
exactly the uninitialized `transactions` array from Task 1.

The same build also settles Task 4, which GDB could only ever hint at. Looking
at addresses in the debugger shows you allocations happening; it cannot show you
that they were never released. LeakSanitizer states it outright — run the
program, log in, make two deposits, and exit:

```console
ERROR: LeakSanitizer: detected memory leaks
SUMMARY: AddressSanitizer: N byte(s) leaked in 4 allocation(s).
```

Do not expect a particular byte count: it scales with `MAX_TRANSACTIONS`, which
you changed in Task 4. What matters is that the summary is **present** before
your fix and **absent** after it. That is proof; the address listing in §5.4 is
only evidence.

**Record the leak check.** This one is submitted, because it is the only step
that proves Task 4 rather than suggesting it. Capture a single transcript that
shows LeakSanitizer twice: once on the code **before** your Task 4 fix, and once
**after**, in the same session.

```bash
script -q deliverables/part-2-task-4-leakcheck.txt
# 1. before: build the sanitizer binary with your Task 4 fix reverted
g++ -std=c++17 -g -fsanitize=address,leak -o banking-asan main.cpp bank.cpp
./banking-asan          # log in, deposit twice, exit
# 2. after: restore your fix, rebuild, and run exactly the same steps
g++ -std=c++17 -g -fsanitize=address,leak -o banking-asan main.cpp bank.cpp
./banking-asan          # log in, deposit twice, exit
exit
```

The transcript must show the leak summary present in the first run and gone in
the second. Nothing else in this section is submitted — the `-Weffc++` and
AddressSanitizer parts are here because they will find more bugs in your own
code, faster, than any amount of stepping.

## 6. Deliverables

Commit and push everything to your assignment repository. Transcripts go in the
`deliverables/` directory, named **exactly** as listed — they are checked by
name, and a mis-named file is a missing file.

If you record straight into `deliverables/` as shown in §3.6, the names are
already right. Check them with `ls deliverables/` before you push.

| # | Path | Contents |
| --- | --- | --- |
| 1 | `deliverables/part-1-task-1.txt` | Task 1 — `ptype` and the first account |
| 2 | `deliverables/part-1-task-2-1.txt` | Task 2 — the three breakpoints |
| 3 | `deliverables/part-1-task-2-2.txt` | Task 2 — the watchpoint firing |
| 4 | `deliverables/part-1-task-3-1.txt` | Task 3 — step, list, finish |
| 5 | `deliverables/part-1-task-3-2.txt` | Task 3 — the three views of memory |
| 6 | `deliverables/part-1-task-4.txt` | Task 4 — backtrace and `bt full` |
| 7 | `deliverables/part-1-task-5.txt` | Task 5 — interrupt and watchpoint output |
| 8 | `deliverables/part-2-task-1.txt` | Part 2 Task 1 — crash and backtrace |
| 9 | `deliverables/part-2-task-2.txt` | Part 2 Task 2 — recursive frames |
| 10 | `deliverables/part-2-task-3.txt` | Part 2 Task 3 — overflow and counters |
| 11 | `deliverables/part-2-task-4.txt` | Part 2 Task 4 — descriptions and memory |
| 12 | `deliverables/part-2-task-5.txt` | Part 2 Task 5 — abort and pointer |
| 13 | `deliverables/part-2-task-4-leakcheck.txt` | LeakSanitizer before and after the Task 4 fix (§5.6) |
| 14 | `part-2/bank.cpp` | Your corrected source |
| 15 | `part-2/types.h` | Your corrected source |

Your corrected `part-2` must build with `make` and run without crashing on the
paths above. Before pushing, confirm it from a clean state:

```bash
cd part-2
make clean && make
```

### 6.1 Mistakes that cost points

1. Not restarting GDB between tasks, so stale breakpoints appear in the output.
2. Transcripts not named exactly as the table requires.
3. Forgetting to run `exit` at the end of a `script` session, which leaves the
   transcript truncated. Always `cat` the file before you push it.
4. In Part 1 Task 5, stopping before the watchpoint fires, so the output does
   not show the balance changing.
5. In Part 2 Task 2, not continuing far enough for the backtrace to show the
   recursion.
6. Editing source without rebuilding, so GDB keeps running the old executable.

## 7. Getting help

- **Public questions** — post on the course Discord server. Most setup problems
  have already been answered there.
- **Private questions** — email the instructor at
  [davidkebo@tamu.edu](mailto:davidkebo@tamu.edu).
- **Office hours and help sessions** — see the syllabus for times.

Do not send questions through the Canvas inbox; it is not monitored.

You may discuss this lab conceptually with classmates. The implementation you
submit must be your own work. See the syllabus for the full collaboration and
academic integrity policy.

## Revision history

Changes made to this handout after release are listed here, newest first.

| Date | Change |
| --- | --- |
| August 25, 2026 | §3.1 now carries the classroom50 assignment link. |
| August 25, 2026 | Corrected §5.2: with a breakpoint set the program never reaches the crash, so the task now deletes the breakpoint before continuing, and uses `bt -12` to show the oldest frames. |
| August 25, 2026 | Added a graded leak-check transcript (§5.6, deliverable 13). Reduced `MAX_ACCOUNTS` in part-2 so the program uses ~42 MB rather than ~394 MB; Task 2 is unaffected. |
| August 25, 2026 | Deliverables are now plain-text transcripts rather than screenshots (§3.6, §6). Added §5.6 on `-Weffc++` and AddressSanitizer. Setup now points at classroom50. Corrected `x/32x` to `x/32xb` in §5.4, which reads 32 bytes rather than 32 words. |
| August 25, 2026 | Initial release for Fall 2026. Migrated from Google Docs. |
