---
layout: lab
title: "Lab 2 — The Process Abstraction and Creating Processes"
lab_number: 2
lab_title: "The Process Abstraction and Creating Processes"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
instructor: "David Kebo Houngninou"
released: "Tuesday, September 8, 2026, 9:00 AM CT"
due: "Monday, September 21, 2026, 11:59 PM CT"
released_short: "Tue Sep 8, 2026"
due_short: "Mon Sep 21, 2026, 11:59 PM CT"
description: "Build the client of a client-server financial system: fork and exec three server processes, watch what each process inherits, and talk to the servers over a request channel."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Objectives

By the end of this lab you will be able to:

1. Create a child process with `fork()` and tell parent from child by its return value.
2. Replace a child's process image with `execvp()`, passing arguments the way the shell would.
3. Explain what a child inherits from its parent, and what it does not.
4. Observe process isolation directly, by printing the same variables from both processes.
5. Drive a client-server exchange: build a request, send it, and read the response.
6. Shut a system down cleanly, so that no process is left running and no parent waits forever.

Every lab this term builds on one project: a financial management system. This is
where it starts. You write the **client**. The three servers are written for you.

## 2. Background

### 2.1 The client-server model

A **client** handles the user. A **server** owns a resource and answers requests about
it. The client never touches the resource itself; it asks. That buys two things:
the resource lives in one place, and each server can be understood, changed, and
crashed on its own.

This lab has one client and three servers, each owning a different resource.

<figure class="diagram diagram--wide">
<div class="diagram-scroll" tabindex="0" role="group" aria-label="System architecture diagram, scrollable">
<svg viewBox="0 0 760 416" role="img" aria-labelledby="fig1-title" xmlns="http://www.w3.org/2000/svg">
  <title id="fig1-title">Architecture of the lab 2 system: one client process forks three server processes, each owning one resource</title>
  <desc>The client process sits at the bottom. Three arrows labelled RequestChannel run from it to three server processes above: the file server, the logging server and the finance server. Each server has a two-way arrow to the resource it owns: the file server to the storage directory, the logging server to the log file, and the finance server to its array of accounts. The channel names are file, logging and finance.</desc>
  <defs>
    <marker id="f1arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" class="d-arrow"/>
    </marker>
  </defs>

  <rect x="40"  y="25" width="180" height="80" rx="6" class="d-box"/>
  <text x="130" y="47"  text-anchor="middle" class="d-title">storage/</text>
  <text x="130" y="68"  text-anchor="middle" class="d-text--mono">example.log</text>
  <text x="130" y="86"  text-anchor="middle" class="d-text--mono">example_execution.txt</text>

  <rect x="290" y="25" width="180" height="80" rx="6" class="d-box"/>
  <text x="380" y="47"  text-anchor="middle" class="d-title">log file</text>
  <text x="380" y="68"  text-anchor="middle" class="d-text--mono">system.log</text>
  <text x="380" y="86"  text-anchor="middle" class="d-text--sm">survives between runs</text>

  <rect x="540" y="25" width="180" height="80" rx="6" class="d-box"/>
  <text x="630" y="47"  text-anchor="middle" class="d-title">accounts array</text>
  <text x="630" y="68"  text-anchor="middle" class="d-text--mono">accounts[0 .. max]</text>
  <text x="630" y="86"  text-anchor="middle" class="d-text--sm">lost when it exits</text>

  <path d="M 130 108 L 130 162" class="d-edge" marker-start="url(#f1arrow)" marker-end="url(#f1arrow)"/>
  <path d="M 380 108 L 380 162" class="d-edge" marker-start="url(#f1arrow)" marker-end="url(#f1arrow)"/>
  <path d="M 630 108 L 630 162" class="d-edge" marker-start="url(#f1arrow)" marker-end="url(#f1arrow)"/>

  <rect x="40"  y="165" width="180" height="56" rx="6" class="d-box--busy"/>
  <text x="130" y="188" text-anchor="middle" class="d-title">file server</text>
  <text x="130" y="208" text-anchor="middle" class="d-text--mono">./fileserver</text>

  <rect x="290" y="165" width="180" height="56" rx="6" class="d-box--busy"/>
  <text x="380" y="188" text-anchor="middle" class="d-title">logging server</text>
  <text x="380" y="208" text-anchor="middle" class="d-text--mono">./logging</text>

  <rect x="540" y="165" width="180" height="56" rx="6" class="d-box--busy"/>
  <text x="630" y="188" text-anchor="middle" class="d-title">finance server</text>
  <text x="630" y="208" text-anchor="middle" class="d-text--mono">./finance</text>

  <path d="M 340 310 L 150 224" class="d-edge" marker-start="url(#f1arrow)" marker-end="url(#f1arrow)"/>
  <path d="M 380 310 L 380 224" class="d-edge" marker-start="url(#f1arrow)" marker-end="url(#f1arrow)"/>
  <path d="M 420 310 L 610 224" class="d-edge" marker-start="url(#f1arrow)" marker-end="url(#f1arrow)"/>

  <text x="150" y="272" text-anchor="middle" class="d-text--edge">"file"</text>
  <text x="393" y="262" text-anchor="start"  class="d-text--edge">"logging"</text>
  <text x="612" y="272" text-anchor="middle" class="d-text--edge">"finance"</text>
  <text x="380" y="408" text-anchor="middle" class="d-text--sm">three RequestChannels, one per server</text>

  <rect x="290" y="313" width="180" height="56" rx="6" class="d-box--brand"/>
  <text x="380" y="336" text-anchor="middle" class="d-title">client process</text>
  <text x="380" y="356" text-anchor="middle" class="d-text--mono">./client</text>
</svg>
</div>
<figcaption>Figure 1 — The client forks and execs all three servers, then talks to each over its own channel. A channel is identified by name, and the name in the client must match the name in the server exactly.</figcaption>
</figure>

Notice what each server owns. The logging server's file **survives** the run; the
finance server's accounts do not, because they live in that process's memory and
die with it. That difference is the whole reason the log file exists.

### 2.2 Requests and responses

Both types are in `common.h`. A **request** carries everything a server might need;
most fields go unused for any given request type.

```cpp
struct Request {
    RequestType type;      // QUIT, DEPOSIT, WITHDRAW, BALANCE,
                           // UPLOAD_FILE, DOWNLOAD_FILE, LOGIN, LOGOUT
    int         user_id;
    double      amount;
    std::string filename;
    std::string data;

    Request(RequestType t, int uid = 0, double amt = 0.0,
            std::string fname = "", std::string d = "");
};
```

Only `type` is required; the rest default. So a quit is just `Request(QUIT)`, and a
balance enquiry is `Request(BALANCE, user_id)`.

A **response** comes back with four fields, and again only some are filled:

```cpp
struct Response {
    bool        success;   // did the server do what was asked?
    double      balance;   // finance server only
    std::string data;      // file contents, on a download
    std::string message;   // short explanation, useful when success is false
};
```

<aside class="callout callout--warn" aria-labelledby="resp-heading">
<h2 class="callout__title" id="resp-heading">A response is not a request</h2>
<p>A <code>Response</code> has no <code>user_id</code>, no <code>amount</code> and no
<code>filename</code>. If you need to know which user or which file a reply refers to,
you already know it: you are the one who asked. Read <code>success</code> first, and
<code>message</code> when it is false.</p>
</aside>

### 2.3 `fork()` and `execvp()`

`fork()` is called once and returns twice, because after it there are two processes.
The return value is the only thing that differs, and it is how each process learns
which one it is:

```cpp
pid_t pid = fork();
if (pid < 0)  { /* fork failed  */ }
if (pid == 0) { /* the child    */ }
if (pid > 0)  { /* the parent   */ }
```

The child is a copy: same code, same variables, same next line to execute. What it
is *not* is the same memory. Change a variable in the child and the parent's copy
does not move. Task 2 has you prove that to yourself.

`execvp()` then throws that copy away and loads a different program into the process:

```cpp
char* args[] = {(char*)"./program", (char*)"arg1", (char*)"arg2", nullptr};
execvp(args[0], args);
perror("execvp");   // only reached if execvp FAILED
exit(1);
```

Two things to hold on to. The array must end with `nullptr`, and `args[0]` is by
convention the program's own name. And a successful `execvp` **never returns** —
there is no longer any code to return to. So any line after it runs only on failure,
which is exactly why the two lines above are there.

<aside class="callout callout--warn" aria-labelledby="dangle-heading">
<h2 class="callout__title" id="dangle-heading">Keep the strings alive</h2>
<p>A temporary <code>std::string</code> dies at the end of the statement that made it,
so this leaves <code>args[2]</code> pointing at freed memory:</p>
<p><code>char* args[] = {..., (char*)std::to_string(n).c_str(), nullptr};</code></p>
<p>Store it in a named variable first, then take <code>.c_str()</code>. It often appears
to work, which is what makes it worth avoiding.</p>
</aside>

### 2.4 The RequestChannel

`channel.h` gives you the whole interface you need:

```cpp
RequestChannel(const std::string process_name, const Side side);
Response send_request(const Request& req);
```

A channel is identified by its **name**. The client and the server must construct it
with the same string, or they are not talking to each other. The names the servers
use are in their source: `"finance"`, `"file"`, `"logging"`. Note the file server's
channel is called `"file"` even though its executable is `./fileserver`.

Each name must be opened exactly once from each side — one `CLIENT_SIDE`, one
`SERVER_SIDE`. Opening the same side twice is undefined behaviour.

You only ever call `send_request`. `receive_request` and `send_response` are the
servers' half of the conversation, and they are already written.

## 3. Environment setup

### 3.1 Accept the assignment

1. Sign in to [classroom50.org](https://classroom50.org/) with your GitHub account.
2. Accept Lab 2:
   <https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/lab-2/accept>.
   Your repository is created for you.
3. Clone it:

```bash
git clone https://github.com/CSCE-313-FA26/<your-lab-2-repository>.git
cd <your-lab-2-repository>
```

<aside class="callout callout--note" aria-labelledby="roster-heading">
<h2 class="callout__title" id="roster-heading">If accepting fails</h2>
<p>If your name is missing from the roster, or you signed in with the wrong GitHub
account, contact the instructor or a TA — do not create a second account.</p>
</aside>

### 3.2 Install clang

The `RequestChannel` implementation ships as LLVM IR, which `clang` assembles:

```bash
sudo apt update
sudo apt install clang
```

You do not need clang for anything else in this lab, and you never edit the IR.

### 3.3 Repository layout

| Path | What it is |
| --- | --- |
| `client.cpp` | **The only file you modify.** Every `TODO` is here. |
| `finance.cpp` | Finance server. Complete — do not modify. |
| `file.cpp` | File server. Complete — do not modify. |
| `logging.cpp` | Logging server. Complete — do not modify. |
| `channel.h` | The `RequestChannel` interface you call |
| `channel.ll`, `channel.ll.arm` | Its implementation, as LLVM IR, for x86-64 and ARM |
| `common.h`, `common.cpp` | `Request`, `Response`, `RequestType` |
| `Makefile` | Builds all four programs |
| `lab2-tests.sh` | The same tests the autograder runs. Run them yourself. |
| `storage/example_execution.txt` | A full session, showing exactly what correct output looks like |
| `storage/example.log` | The log that session should have produced |

### 3.4 Build

```bash
make
```

That produces four executables: `client`, `finance`, `fileserver`, `logging`.

<aside class="callout callout--note" aria-labelledby="arch-heading">
<h2 class="callout__title" id="arch-heading">x86-64, ARM, and which clang you need</h2>
<p>The Makefile reads <code>uname -m</code> and picks <code>channel.ll</code> or
<code>channel.ll.arm</code> by itself. <strong>Do not rename either file.</strong> In
previous semesters students renamed them by hand and had to remember to rename them
back before submitting; forgetting meant failing every test. There is nothing to undo
now.</p>
<p>On <strong>x86-64</strong>, any clang from 18 onwards works, which is what
<code>apt install clang</code> gives you on Ubuntu 24.04.</p>
<p>On <strong>ARM</strong>, <code>channel.ll.arm</code> was generated by a newer
compiler and needs <strong>clang 20 or later</strong>. Ubuntu 24.04's default clang is
18 and will stop with <code>error: expected type</code>. Install a newer one:</p>
<p><code>sudo apt install clang-20</code> — then build with
<code>make CLANG=clang-20</code>.</p>
<p>If that is not available to you, work on a lab machine or any x86-64 Linux box
instead, and tell the instructor.</p>
</aside>

Note the file server's executable is **`fileserver`**, not `file` — `file` is already
a standard Unix command. Its *channel*, however, is named `"file"`. The two are
different things and both spellings are correct in their own place.

### 3.5 Running the servers by hand

The finished client starts the servers itself. While you are still building it, you
can run each one in its own terminal and drive it from a fourth:

```bash
./finance -m 1000            # accounts 0 through 1000
./logging -f system.log      # log to system.log
./fileserver .txt .h         # allow uploads of .txt and .h only
./client
```

This is a debugging aid, not the deliverable. **The autograder fails every test if
the client does not start the servers itself**, so implement Task 1 first.

## 4. Walkthrough

You do not have to read the servers line by line, but you do have to know which
fields each one reads out of your request. These three diagrams are that summary.

### 4.1 The finance server

Started as `./finance -m <max_account_num>`. Accounts `0` through `max_account_num`
inclusive are valid; anything else is refused. Accounts are created on first use with
a balance of zero.

<figure class="diagram diagram--wide">
<div class="diagram-scroll" tabindex="0" role="group" aria-label="Finance server request handling diagram, scrollable">
<svg viewBox="0 0 760 480" role="img" aria-labelledby="fig2-title" xmlns="http://www.w3.org/2000/svg">
  <title id="fig2-title">How the finance server handles one request</title>
  <desc>A request arrives on the finance channel. If its type is QUIT the server calls exit zero and sends no response at all. Otherwise, if the user id is outside zero to max the server replies with success false and the message Invalid account ID. Otherwise it creates the account if needed and branches on request type: DEPOSIT adds the amount to the balance; WITHDRAW subtracts it only if the balance is greater than or equal to the amount, and otherwise fails with Insufficient funds; BALANCE just reports the balance; any other type fails with Unknown RequestType. All four branches then send the response back.</desc>
  <defs>
    <marker id="f2arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" class="d-arrow"/>
    </marker>
  </defs>

  <rect x="250" y="18" width="260" height="44" rx="6" class="d-box--brand"/>
  <text x="380" y="38" text-anchor="middle" class="d-title">receive_request()</text>
  <text x="380" y="55" text-anchor="middle" class="d-text--edge">channel "finance"</text>
  <path d="M 380 62 L 380 92" class="d-edge" marker-end="url(#f2arrow)"/>

  <path d="M 380 94 L 468 124 L 380 154 L 292 124 Z" class="d-box"/>
  <text x="380" y="128" text-anchor="middle" class="d-text--mono">r.type == QUIT ?</text>
  <path d="M 468 124 L 556 124" class="d-edge" marker-end="url(#f2arrow)"/>
  <text x="512" y="117" text-anchor="middle" class="d-text--sm">yes</text>
  <rect x="558" y="100" width="186" height="48" rx="6" class="d-box--warn"/>
  <text x="651" y="120" text-anchor="middle" class="d-text--mono">exit(0)</text>
  <text x="651" y="138" text-anchor="middle" class="d-text--sm">no response is sent</text>

  <path d="M 380 154 L 380 184" class="d-edge" marker-end="url(#f2arrow)"/>
  <text x="391" y="174" text-anchor="start" class="d-text--sm">no</text>

  <path d="M 380 186 L 468 216 L 380 246 L 292 216 Z" class="d-box"/>
  <text x="380" y="213" text-anchor="middle" class="d-text--mono">0 &lt;= r.user_id</text>
  <text x="380" y="228" text-anchor="middle" class="d-text--mono">&lt;= max ?</text>
  <path d="M 468 216 L 556 216" class="d-edge" marker-end="url(#f2arrow)"/>
  <text x="512" y="209" text-anchor="middle" class="d-text--sm">no</text>
  <rect x="558" y="192" width="186" height="48" rx="6" class="d-box--warn"/>
  <text x="651" y="212" text-anchor="middle" class="d-text--mono">success = false</text>
  <text x="651" y="230" text-anchor="middle" class="d-text--sm">"Invalid account ID"</text>

  <path d="M 380 246 L 380 274" class="d-edge" marker-end="url(#f2arrow)"/>
  <text x="391" y="266" text-anchor="start" class="d-text--sm">yes</text>

  <path d="M 100 292 L 660 292" class="d-edge"/>
  <path d="M 380 274 L 380 292" class="d-edge"/>
  <path d="M 100 292 L 100 316" class="d-edge" marker-end="url(#f2arrow)"/>
  <path d="M 287 292 L 287 316" class="d-edge" marker-end="url(#f2arrow)"/>
  <path d="M 473 292 L 473 316" class="d-edge" marker-end="url(#f2arrow)"/>
  <path d="M 660 292 L 660 316" class="d-edge" marker-end="url(#f2arrow)"/>

  <rect x="20" y="318" width="160" height="76" rx="6" class="d-box--busy"/>
  <text x="100" y="338" text-anchor="middle" class="d-title">DEPOSIT</text>
  <text x="100" y="360" text-anchor="middle" class="d-text--mono">balance +=</text>
  <text x="100" y="376" text-anchor="middle" class="d-text--mono">r.amount</text>

  <rect x="207" y="318" width="160" height="76" rx="6" class="d-box--busy"/>
  <text x="287" y="338" text-anchor="middle" class="d-title">WITHDRAW</text>
  <text x="287" y="360" text-anchor="middle" class="d-text--mono">balance &gt;= amount</text>
  <text x="287" y="376" text-anchor="middle" class="d-text--sm">else "Insufficient funds"</text>

  <rect x="393" y="318" width="160" height="76" rx="6" class="d-box--busy"/>
  <text x="473" y="338" text-anchor="middle" class="d-title">BALANCE</text>
  <text x="473" y="360" text-anchor="middle" class="d-text--mono">resp.balance =</text>
  <text x="473" y="376" text-anchor="middle" class="d-text--mono">acc.balance</text>

  <rect x="580" y="318" width="160" height="76" rx="6" class="d-box--warn"/>
  <text x="660" y="338" text-anchor="middle" class="d-title">any other type</text>
  <text x="660" y="360" text-anchor="middle" class="d-text--mono">success = false</text>
  <text x="660" y="376" text-anchor="middle" class="d-text--sm">"Unknown RequestType"</text>

  <path d="M 100 394 L 100 416 L 660 416 L 660 394" class="d-edge"/>
  <path d="M 287 394 L 287 416" class="d-edge"/>
  <path d="M 473 394 L 473 416" class="d-edge"/>
  <path d="M 380 416 L 380 438" class="d-edge" marker-end="url(#f2arrow)"/>
  <rect x="250" y="440" width="260" height="34" rx="6" class="d-box--brand"/>
  <text x="380" y="462" text-anchor="middle" class="d-title">send_response(resp)</text>
</svg>
</div>
<figcaption>Figure 2 — The finance server. Note the two things that catch people out: QUIT returns nothing at all, and a withdrawal of exactly the balance succeeds, because the test is <code>&gt;=</code>.</figcaption>
</figure>

`resp.balance` is set on all three successful operations, so you can print the new
balance straight from the response without asking again.

### 4.2 The file server

Started as `./fileserver <ext_1> ... <ext_n>`. It owns the `storage/` directory.

<figure class="diagram diagram--wide">
<div class="diagram-scroll" tabindex="0" role="group" aria-label="File server request handling diagram, scrollable">
<svg viewBox="-45 0 855 440" role="img" aria-labelledby="fig3-title" xmlns="http://www.w3.org/2000/svg">
  <title id="fig3-title">How the file server handles one request</title>
  <desc>A request arrives on the file channel. QUIT exits immediately with no response. An UPLOAD_FILE request is checked against the allowed extension list, but only if that list is non-empty; a matching or unchecked file is written into the storage directory, and a non-matching one fails with File extension not allowed. A DOWNLOAD_FILE request looks for the named file in the storage directory and, if found, copies its bytes into the response data field, otherwise fails with File not found. Any other type fails. All paths except QUIT send a response.</desc>
  <defs>
    <marker id="f3arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" class="d-arrow"/>
    </marker>
  </defs>

  <rect x="250" y="14" width="260" height="44" rx="6" class="d-box--brand"/>
  <text x="380" y="34" text-anchor="middle" class="d-title">receive_request()</text>
  <text x="380" y="51" text-anchor="middle" class="d-text--edge">channel "file"</text>

  <path d="M 510 36 L 596 36" class="d-edge" marker-end="url(#f3arrow)"/>
  <text x="553" y="29" text-anchor="middle" class="d-text--sm">QUIT</text>
  <rect x="598" y="12" width="150" height="48" rx="6" class="d-box--warn"/>
  <text x="673" y="32" text-anchor="middle" class="d-text--mono">exit(0)</text>
  <text x="673" y="50" text-anchor="middle" class="d-text--sm">no response</text>

  <path d="M 380 58 L 380 78" class="d-edge"/>
  <path d="M 190 78 L 570 78" class="d-edge"/>
  <path d="M 190 78 L 190 102" class="d-edge" marker-end="url(#f3arrow)"/>
  <path d="M 570 78 L 570 102" class="d-edge" marker-end="url(#f3arrow)"/>
  <text x="176" y="96" text-anchor="end" class="d-text--sm">UPLOAD_FILE</text>
  <text x="584" y="96" text-anchor="start" class="d-text--sm">DOWNLOAD_FILE</text>

  <path d="M 190 104 L 300 141 L 190 178 L 80 141 Z" class="d-box"/>
  <text x="190" y="132" text-anchor="middle" class="d-text--sm">extension list empty,</text>
  <text x="190" y="148" text-anchor="middle" class="d-text--sm">or filename matches?</text>

  <path d="M 570 104 L 680 141 L 570 178 L 460 141 Z" class="d-box"/>
  <text x="570" y="132" text-anchor="middle" class="d-text--sm">storage/&lt;filename&gt;</text>
  <text x="570" y="148" text-anchor="middle" class="d-text--sm">exists?</text>

  <path d="M 190 178 L 190 214" class="d-edge" marker-end="url(#f3arrow)"/>
  <text x="199" y="200" text-anchor="start" class="d-text--sm">yes</text>
  <path d="M 80 141 L 40 141 L 40 214" class="d-edge" marker-end="url(#f3arrow)"/>
  <text x="47" y="200" text-anchor="start" class="d-text--sm">no</text>

  <path d="M 570 178 L 570 214" class="d-edge" marker-end="url(#f3arrow)"/>
  <text x="579" y="200" text-anchor="start" class="d-text--sm">yes</text>
  <path d="M 680 141 L 720 141 L 720 214" class="d-edge" marker-end="url(#f3arrow)"/>
  <text x="727" y="200" text-anchor="start" class="d-text--sm">no</text>

  <rect x="120" y="216" width="150" height="66" rx="6" class="d-box--busy"/>
  <text x="195" y="238" text-anchor="middle" class="d-text--sm">write r.data to</text>
  <text x="195" y="255" text-anchor="middle" class="d-text--mono">storage/</text>
  <text x="195" y="272" text-anchor="middle" class="d-text--sm">success = true</text>

  <rect x="-25" y="216" width="130" height="66" rx="6" class="d-box--warn"/>
  <text x="40" y="245" text-anchor="middle" class="d-text--sm">success = false</text>
  <text x="40" y="264" text-anchor="middle" class="d-text--sm">"not allowed"</text>

  <rect x="495" y="216" width="150" height="66" rx="6" class="d-box--busy"/>
  <text x="570" y="238" text-anchor="middle" class="d-text--sm">read the file into</text>
  <text x="570" y="255" text-anchor="middle" class="d-text--mono">resp.data</text>
  <text x="570" y="272" text-anchor="middle" class="d-text--sm">success = true</text>

  <rect x="660" y="216" width="130" height="66" rx="6" class="d-box--warn"/>
  <text x="725" y="245" text-anchor="middle" class="d-text--sm">success = false</text>
  <text x="725" y="264" text-anchor="middle" class="d-text--sm">"File not found"</text>

  <path d="M 40 282 L 40 316 L 725 316 L 725 282" class="d-edge"/>
  <path d="M 195 282 L 195 316" class="d-edge"/>
  <path d="M 570 282 L 570 316" class="d-edge"/>
  <path d="M 380 316 L 380 346" class="d-edge" marker-end="url(#f3arrow)"/>
  <rect x="250" y="348" width="260" height="34" rx="6" class="d-box--brand"/>
  <text x="380" y="370" text-anchor="middle" class="d-title">send_response(resp)</text>

  <text x="380" y="410" text-anchor="middle" class="d-text--sm">The server never writes to your working directory. On a download it returns</text>
  <text x="380" y="424" text-anchor="middle" class="d-text--sm">the bytes, and the client is what saves them to a file.</text>
</svg>
</div>
<figcaption>Figure 3 — The file server. Started with no extension arguments it performs no extension check at all, so every upload is accepted — the opposite of the restriction you might expect.</figcaption>
</figure>

<aside class="callout callout--warn" aria-labelledby="cap-heading">
<h2 class="callout__title" id="cap-heading">Upload small files only — about 1 KB</h2>
<p>A whole request has to fit in a <strong>1024-byte</strong> buffer, and that budget
covers the request type, the user id, the amount, the filename <em>and</em> the file
contents. Roughly a thousand bytes of file.</p>
<p>Go over it and two things happen, neither of them obvious. The upload is silently
truncated, and <strong>the client still prints <code>File upload successful</code></strong>.
Go far enough over and the truncated request no longer parses at all, which the channel
reports as a <code>QUIT</code> — so <strong>the file server exits</strong>, and every
later upload or download does nothing at all, with no error.</p>
<p>The example in <code>storage/example_execution.txt</code> uploads
<code>channel.h</code>, which is 579 bytes. Keep your own test files that small. This is
a limit of the provided channel, not something you can fix in the client.</p>
<p>The same buffer is why a file containing a <code>|</code> character is cut off at the
first one: <code>|</code> is the field separator in the wire format.</p>
</aside>

### 4.3 The logging server

Started as `./logging -f <log_filename>`. It appends one line per request, and the
file survives between runs.

<figure class="diagram">
<div class="diagram-scroll" tabindex="0" role="group" aria-label="Logging server request handling diagram, scrollable">
<svg viewBox="0 0 620 350" role="img" aria-labelledby="fig4-title" xmlns="http://www.w3.org/2000/svg">
  <title id="fig4-title">How the logging server handles one request</title>
  <desc>The logging server waits for a request. If the type is QUIT it calls exit zero immediately, logging nothing and sending nothing back, which is why a quit never appears in the log file. For every other type it appends one line beginning with the user id in square brackets followed by a description of the action, replies with success, and loops back to waiting.</desc>
  <defs>
    <marker id="f4arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" class="d-arrow"/>
    </marker>
  </defs>

  <rect x="200" y="14" width="220" height="42" rx="21" class="d-box--brand"/>
  <text x="310" y="41" text-anchor="middle" class="d-title">waiting for a request</text>
  <path d="M 310 56 L 310 84" class="d-edge" marker-end="url(#f4arrow)"/>

  <path d="M 310 86 L 400 116 L 310 146 L 220 116 Z" class="d-box"/>
  <text x="310" y="120" text-anchor="middle" class="d-text--mono">r.type == QUIT ?</text>

  <path d="M 400 116 L 454 116" class="d-edge" marker-end="url(#f4arrow)"/>
  <text x="427" y="109" text-anchor="middle" class="d-text--sm">yes</text>
  <rect x="456" y="89" width="160" height="54" rx="6" class="d-box--warn"/>
  <text x="536" y="111" text-anchor="middle" class="d-text--mono">exit(0)</text>
  <text x="536" y="131" text-anchor="middle" class="d-text--sm">nothing logged or sent</text>

  <path d="M 310 146 L 310 180" class="d-edge" marker-end="url(#f4arrow)"/>
  <text x="321" y="170" text-anchor="start" class="d-text--sm">no</text>

  <rect x="140" y="182" width="340" height="76" rx="6" class="d-box--busy"/>
  <text x="310" y="204" text-anchor="middle" class="d-text--sm">append one line to the log file:</text>
  <text x="310" y="226" text-anchor="middle" class="d-text--mono">[r.user_id]: &lt;action&gt;</text>
  <text x="310" y="246" text-anchor="middle" class="d-text--sm">the action text depends on r.type</text>

  <path d="M 310 258 L 310 288" class="d-edge" marker-end="url(#f4arrow)"/>
  <rect x="185" y="290" width="250" height="42" rx="6" class="d-box--brand"/>
  <text x="310" y="317" text-anchor="middle" class="d-title">send_response(success)</text>

  <path d="M 185 311 L 100 311 L 100 35 L 196 35" class="d-edge--muted" marker-end="url(#f4arrow)"/>
  <text x="110" y="180" text-anchor="start" class="d-text--sm">loop</text>
</svg>
</div>
<figcaption>Figure 4 — The logging server. A QUIT is the one request it does not log, because it exits before reaching the logging code.</figcaption>
</figure>

Which field the log line uses depends on the request type, and getting this wrong is
the most common way to lose points on Task 3:

| Request | Line written | Field it reads |
| --- | --- | --- |
| `LOGIN` | `[7]: logged in` | `user_id` |
| `LOGOUT` | `[7]: logged out` | `user_id` |
| `DEPOSIT` | `[7]: deposited 500` | `amount` |
| `WITHDRAW` | `[7]: withdrew 200` | `amount` |
| `BALANCE` | `[7]: viewed balance: 300` | **`amount`**, not `balance` |
| `UPLOAD_FILE` | `[7]: uploaded file: channel.h` | `filename` |
| `DOWNLOAD_FILE` | `[7]: downloaded file: example.log` | `filename` |

<aside class="callout callout--warn" aria-labelledby="balance-heading">
<h2 class="callout__title" id="balance-heading">The BALANCE line reads <code>amount</code></h2>
<p>The logging server prints <code>r.amount</code> for a <code>BALANCE</code> request, not
<code>r.balance</code> — a <code>Request</code> has no <code>balance</code> field at all. So
after the finance server tells you the balance, you have to put that number into the
<code>amount</code> field of the request you then send to the logging server. Send a
default-constructed request instead and your log reads <code>viewed balance: 0</code>.</p>
</aside>

### 4.4 The session you are aiming at

`storage/example_execution.txt` is a complete correct run, and `storage/example.log`
is the log it produced:

```
[1]: logged in
[1]: deposited 500
[1]: withdrew 200
[1]: viewed balance: 300
[1]: uploaded file: channel.h
[1]: downloaded file: example.log
[1]: logged out
```

Reproduce that log exactly and Task 3's logging half is done.

## 5. To-do

Everything you write goes in `client.cpp`, at the `TODO` comments. Do the tasks in
this order: nothing else can be tested until Task 1 works.

### 5.1 Task 1 — Run the servers as child processes (45 points)

Start `finance`, `logging` and `fileserver` as children of the client, so that
running `./client` in one terminal brings the whole system up.

For each of the three, at its `TODO`:

1. `fork()`, and check for failure.
2. In the **child only**, run the block already written there — it changes the three
   variables and calls `print_process_info` — and then `execvp` the server.
3. The parent does nothing here and carries on to start the next server.

The command lines are:

```text
./finance   -m <max_account>
./logging   -f <log_file_name>
./fileserver <extension1> <extension2> ...
```

The file server's argument count is not known until run time, so build its `argv`
on the heap. Every array must end with `nullptr`.

<aside class="callout callout--warn" aria-labelledby="indent-heading">
<h2 class="callout__title" id="indent-heading">The block below each TODO is indented, but it is not inside anything</h2>
<p>In the starter, the lines that bump <code>global_var</code> and call
<code>print_process_info</code> are indented as though they sit in an
<code>if</code> block. They do not — there is no <code>if</code> yet. That is your job.
Leave them where they are and put the <code>if (pid == 0) { ... }</code> around them.
If you forget, the <em>parent</em> changes those variables and writes those files, and
every process-info check fails while everything looks superficially fine.</p>
</aside>

### 5.2 Task 2 — Print process details (15 points)

Fill in `print_process_info` so each line carries a real value:

```text
Parent process before fork:
PID: 48120
PPID: 3310
Global variable address: 0x5b1f0a2c4010 value: 100
Stack variable address: 0x7ffd41b2ec44 value: 200
Heap variable address: 0x5b1f0b3d52c0 value: 300
----------------------------------------
```

Use `getpid()` and `getppid()`. Print the **address** and then the **value** for each
of the global, stack and heap variables. Do not change the label strings or the line
order — the tests read these files by line.

This is the part of the lab that shows you the process abstraction directly. Each
child bumps the three variables by a different amount before `exec`, so afterwards
compare `parent_attributes.txt` against the three child files:

- Every child's `PPID` is the parent's `PID`. They really are its children.
- Every child's **values** differ from the parent's, and from each other's.
- Every child's **addresses** are the same as the parent's, or nearly so.

That last one is the point worth sitting with. Two processes report the same address
holding different values, because the address is virtual: each process has its own
mapping from those numbers to physical memory. Nothing is shared, and nothing needed
to be copied until it was written to.

### 5.3 Task 3 — Client-server communication (30 points)

Create the three channels after the servers are running:

```cpp
RequestChannel finance("finance", RequestChannel::CLIENT_SIDE);
RequestChannel file("file",       RequestChannel::CLIENT_SIDE);
RequestChannel logging("logging", RequestChannel::CLIENT_SIDE);
```

Then fill in each menu action. Save every reply into the `resp` variable the starter
already tests, and use `send_request` for all of them.

| Menu action | Send to finance | Send to logging |
| --- | --- | --- |
| Login | — | `LOGIN` |
| Deposit | `DEPOSIT` with `amount` | `DEPOSIT` with the same `amount` |
| Withdraw | `WITHDRAW` with `amount` | `WITHDRAW` with the same `amount` |
| View balance | `BALANCE` | `BALANCE` with the **returned balance** in `amount` |
| Upload file | `UPLOAD_FILE` with `filename` and `data` → **file server** | `UPLOAD_FILE` with `filename` |
| Download file | `DOWNLOAD_FILE` with `filename` → **file server** | `DOWNLOAD_FILE` with `filename` |
| Logout | — | `LOGOUT` |

Every action that succeeds is logged, and only after it succeeded — the audit line
goes inside the `if (resp.success)` branch that is already written for you.

Read every response. A request whose reply you never read leaves the channel out of
step, and the next reply you read will be the wrong one.

### 5.4 Task 4 — Close the channels (10 points)

Before the client returns, send `Request(QUIT)` down **all three** channels.

The client's last act is `while (wait(NULL) > 0);`, which returns only once every
child has exited — and a server exits only when it receives QUIT. So a client that
misses even one QUIT does not crash or complain. It hangs, forever, with no output.
If your program stops responding at exit, this is why.

### 5.5 Test your work

```bash
make test
```

That runs `lab2-tests.sh`, which is the same set of checks the autograder runs, out
of 100. Run it before you push; it is much faster than waiting for the grader.

If the script reports a hang, run the client by hand and compare against
`storage/example_execution.txt`.

## 6. Deliverables

Commit and push your work to your assignment repository:

```bash
git add client.cpp
git commit -m "lab 2"
git push
```

| # | Path | Description |
| --- | --- | --- |
| 1 | `client.cpp` | Your completed client: all four tasks |

That is the whole submission. The programs' output files — `*_attributes.txt`, your
log file, and anything uploaded into `storage/` — are produced when the grader runs
your code, and are deliberately ignored by `.gitignore`. Do not commit them, and do
not commit the built executables.

The autograder runs on every push, so you can push as often as you like and read the
result.

### 6.1 Mistakes that cost points

| Symptom | Cause |
| --- | --- |
| Every test fails at once | The servers are not being started by the client. Task 1 first. |
| Client prints nothing and never exits | A QUIT was not sent to one of the three servers |
| `viewed balance: 0` in the log | The balance was not copied into the request's `amount` field |
| Process info values all equal the parent's | The `if (pid == 0)` block does not wrap the given lines |
| `execvp` "No such file or directory" | The file server is `./fileserver`, not `./file` |
| Log file empty | The logging server was started, but no requests were sent to it |
| Deposits succeed but nothing is logged | The audit request was placed outside the `if (resp.success)` branch |
| Works alone, fails in the grader | You renamed `channel.ll`. Do not — the Makefile picks the right one |
| Uploads and downloads stop doing anything | An earlier upload was over ~1 KB and killed the file server. Restart the client and use a smaller file |
| `error: expected type` from clang | You are on ARM with clang 18. See §3.4 — ARM needs clang 20 |

## 7. Getting help

Ask on **Discord**. Bring the exact command you ran and the exact output, not a
description of it. The Canvas inbox is not monitored.

Office hours and TA contact details are in the syllabus.

## Revision history

| Date | Change |
| --- | --- |
| 2026-09-07 | Migrated from the Google Doc to this page. Due date corrected from June 14 (a leftover from a summer offering) to Monday, September 21. GitHub Classroom replaced by classroom50. `./file` corrected to `./fileserver` throughout. The file server's request types corrected from "three" to two. Figure numbering corrected: the old handout skipped Figure 4. The `Response` field list corrected — it carries `success`, `balance`, `data`, `message`, not `user_id`/`amount`/`filename`. The en dash in `./logging –f` corrected to a hyphen. The `pid_t p = fork()` snippet corrected to use one variable name. Figures 2, 3 and 4 corrected against the server sources: QUIT sends no response, a withdrawal of exactly the balance succeeds, the file server returns bytes rather than moving files, and `r.user_id` is not `r.id`. Added the ARM/x86 note now that the Makefile selects the IR automatically, the `BALANCE` logging warning, and §5.5 on running the tests locally. |
