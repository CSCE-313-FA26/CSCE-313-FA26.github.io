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

Accept the assignment on GitHub Classroom:

<https://classroom.github.com/a/oMsgpTTQ>

Classroom creates a private repository for you in the course organization. Clone
it:

```bash
git clone https://github.com/CSCE-313-FA26/<your-repository>.git
cd <your-repository>
```

### 3.2 Repository layout

| Path | Contents |
| --- | --- |
| `part-1/` | The working program: `main.cpp`, `bank.cpp`, `types.h`, `Makefile` |
| `part-2/` | The defective program: same four files, different contents |
| `deliverables/` | Where your screenshots go |

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
appears to have done nothing. When in doubt,
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

Save this output as **`part-1-task-1.png`**.

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

Save this output as **`part-1-task-2-1.png`**.

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

Save this output as **`part-1-task-2-2.png`**.

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

Save this output as **`part-1-task-3-1.png`**.

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

Save this output as **`part-1-task-3-2.png`**.

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

Save this output as **`part-1-task-4.png`**.

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
balance. Your screenshot must include the watchpoint output — stopping before it
triggers is the most common way to lose points on this task.

Save this output as **`part-1-task-5.png`**.

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

Save as **`part-2-task-1.png`**, showing the crash and the backtrace at the
crash point.

### 5.2 Task 2 — Runaway recursion in login

Log in with user ID `1`. The program dies almost immediately.

```console
(gdb) break Bank::login
(gdb) run
```

Continue past the breakpoint several times and watch the argument change, then
look at the stack:

```console
(gdb) backtrace full
```

The stack is thousands of frames of the same function, each one calling itself
with a different account ID. The exact depth reached before the stack runs out
depends on your machine's stack limit, so do not expect a particular number —
what matters is the repeating frame pattern and that it does not terminate.

Note that logging in as user `0` does not trigger this, which is a clue about
the condition guarding the recursive call.

Save as **`part-2-task-2.png`**, showing the crash and the repeated recursive
frames.

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

Save as **`part-2-task-3.png`**, showing the GDB output at the overflow and the
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
(gdb) x/32x &transactions[0]
```

Every description sits at its own address, and none of those allocations is ever
released. Fix the ownership: whatever allocates must also free, and the array of
transactions itself needs releasing too.

Save as **`part-2-task-4.png`**, showing the several transaction descriptions and
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
that message in your screenshot.</p>
</aside>

Save as **`part-2-task-5.png`**, showing the abort and the examination of
`current_account`.

## 6. Deliverables

Commit and push everything to your assignment repository. Screenshots go in the
`deliverables/` directory, named **exactly** as listed — they are checked by
name, and a mis-named file is a missing file.

Screenshot tools do not name files this way on their own. Take the screenshot,
then rename it before committing.

| # | Path | Contents |
| --- | --- | --- |
| 1 | `deliverables/part-1-task-1.png` | Task 1 — `ptype` and the first account |
| 2 | `deliverables/part-1-task-2-1.png` | Task 2 — the three breakpoints |
| 3 | `deliverables/part-1-task-2-2.png` | Task 2 — the watchpoint firing |
| 4 | `deliverables/part-1-task-3-1.png` | Task 3 — step, list, finish |
| 5 | `deliverables/part-1-task-3-2.png` | Task 3 — the three views of memory |
| 6 | `deliverables/part-1-task-4.png` | Task 4 — backtrace and `bt full` |
| 7 | `deliverables/part-1-task-5.png` | Task 5 — interrupt and watchpoint output |
| 8 | `deliverables/part-2-task-1.png` | Part 2 Task 1 — crash and backtrace |
| 9 | `deliverables/part-2-task-2.png` | Part 2 Task 2 — recursive frames |
| 10 | `deliverables/part-2-task-3.png` | Part 2 Task 3 — overflow and counters |
| 11 | `deliverables/part-2-task-4.png` | Part 2 Task 4 — descriptions and memory |
| 12 | `deliverables/part-2-task-5.png` | Part 2 Task 5 — abort and pointer |
| 13 | `part-2/bank.cpp` | Your corrected source |
| 14 | `part-2/types.h` | Your corrected source |

Your corrected `part-2` must build with `make` and run without crashing on the
paths above.

### 6.1 Mistakes that cost points

1. Not restarting GDB between tasks, so stale breakpoints appear in the output.
2. Screenshots not named exactly as the table requires.
3. In Part 1 Task 5, stopping before the watchpoint fires, so the output does
   not show the balance changing.
4. In Part 2 Task 2, not continuing far enough for the backtrace to show the
   recursion.
5. Editing source without rebuilding, so GDB keeps running the old executable.

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
| August 25, 2026 | Initial release for Fall 2026. Migrated from Google Docs. |
