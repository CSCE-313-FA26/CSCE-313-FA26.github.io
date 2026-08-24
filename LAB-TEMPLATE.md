---
layout: lab
title: "Lab N — Short Title"          # browser tab and search results
lab_number: N
lab_title: "Short Title"              # rendered as the page H1
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
instructor: "David Kebo Houngninou"
released: "Monday, Month D, YYYY, 9:00 AM CT"
due: "Monday, Month D, YYYY, 11:59 PM CT"
description: "One sentence describing the lab, used for search results and link previews."
---

<!-- =====================================================================
     LAB HANDOUT TEMPLATE
     Copy this file to lab-N/index.md and fill it in.

     Structure is fixed on purpose: students learn where to look once and
     that knowledge carries to every later lab. Sections 1-7 always appear,
     in this order, even when a section is short.

     WHY THIS PAGE AND NOT THE STARTER REPO
       GitHub Classroom copies a starter repo at the moment a student
       accepts. Anything committed there is a snapshot - editing it later
       only changes what future accepters receive. This page has one stable
       URL, so a correction reaches everyone, including early accepters.
       Therefore: the starter repo README is a title plus a link to here.
       Never duplicate steps into it. Anything duplicated can disagree.

     House rules
       - One H1 only; it comes from the front matter, not the body.
       - Sections are H2 and numbered. Subsections are H3 and numbered x.y.
       - Every figure is a <figure> with real alt text AND a <figcaption>.
         Alt describes what is in the image; the caption says what it means.
         They must not be the same sentence.
       - Tables are written as markdown. The build adds column scopes and,
         when a table is too wide for the screen, makes it a keyboard
         reachable scroll region named after the heading above it. So put
         every table under a heading that describes it.
       - Never write "see the image below" or "click the green button":
         position and colour are not available to every reader.
       - Code blocks are fenced and language tagged. Use ```console for
         interactive gdb or shell transcripts, ```cpp for source, ```bash
         for commands the student types.
       - For a warning or an aside, use a callout:
           <aside class="callout callout--warn" aria-labelledby="x-heading">
             <h2 class="callout__title" id="x-heading">Heads up</h2>
             <p>...</p>
           </aside>
         Swap callout--warn for callout--note in the neutral case.
       - Any number a student is told to expect must be reproducible from
         the instructions as written. If a step lets the student choose
         something that changes the number, either pin the choice here or
         state the expectation as an invariant instead of a literal.
       - Deliverable filenames are graded literally, so only require a name
         the student can actually produce. Screenshot tools name their own
         files; ask the student to rename, and say so explicitly.
       - Any change after release adds a row to the revision history.
     ===================================================================== -->

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Objectives

By the end of this lab you will be able to:

1. First capability, phrased as something the student can do.
2. Second capability.

## 2. Background

### 2.1 What you are working with

What the program is and what it does.

### 2.2 Key definitions

| Term | Meaning |
| --- | --- |
| `NAME` | What it means |

## 3. Environment setup

### 3.1 Prerequisites

What must already be installed or configured.

### 3.2 Accept the assignment

Accept the GitHub Classroom assignment, then clone your repository.

```bash
git clone https://github.com/CSCE-313-FA26/<your-repo>.git
cd <your-repo>
```

### 3.3 Build the program

```bash
make
```

### 3.4 Repository layout

| Path | Contents |
| --- | --- |
| `part-1/` | What is here |

## 4. Walkthrough

### 4.1 First guided section

**Step 1.** Do the thing, and say why.

```bash
command here
```

<figure>
  <img src="../assets/lab-N/figN-name.png"
       alt="Describe what is visibly in the screenshot, for a reader who cannot see it.">
  <figcaption>Figure 1 — what this figure is showing and why it matters.</figcaption>
</figure>

## 5. To-do

### Task 1 — Imperative title

What to do, and the reasoning behind it.

## 6. Deliverables

Commit and push all of your changes to your assignment repository. Your
repository must contain:

| # | Path | Description |
| --- | --- | --- |
| 1 | `path/to/file` | What it is |

## 7. Getting help

- **Public questions** — post on the course Discord server. Most setup problems
  have already been answered there.
- **Private questions** — email the instructor or a TA.
- **Office hours and help sessions** — see the syllabus for times.

You may discuss this lab conceptually with classmates. The implementation you
submit must be your own work. See the syllabus for the full collaboration and
academic integrity policy.

## Revision history

Changes made to this handout after release are listed here, newest first.

| Date | Change |
| --- | --- |
| Month D, YYYY | Initial release for Fall 2026. |
