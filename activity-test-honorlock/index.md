---
layout: activity
title: "Activity Test — Honorlock Launch Check"
activity_id: "Test"
activity_title: "Honorlock Launch Check"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
listed: false        # reachable by direct link, not shown in the index
duration: "5 minutes"
description: "A dry run of the Honorlock launch flow, so the proctoring check is not the thing that goes wrong on exam day."
---

{%- comment -%}
  Everything between this comment and the matching one further down is scoped to
  THIS PAGE ONLY. The <style> and <script> blocks are emitted inside the page
  body, so they are served with this file and no other - nothing here touches
  _layouts/, assets/css/main.css or assets/js/enhance.js, and no other handout
  on the site gains a password field or changes appearance because of it.

  Every selector and every JS identifier is prefixed `hl-` for the same reason:
  if this block is ever copied into a second page, it still collides with
  nothing in the shared stylesheet.

  What Honorlock needs is an <input type="password"> that is present and
  visible when the page loads - that is what its extension looks for when it
  auto-fills the exam password during the launch check. The `id` and `name` are
  both "password" as well, since some integrations key off those instead.

  The form deliberately does NOT gate the content: submitting it acknowledges
  the entry and stops the page from navigating, nothing more. A client-side
  gate on a public GitHub Pages site is readable in View Source, so it would
  promise a protection it cannot deliver. The real password lives in the
  Honorlock exam settings, not in this repository.
{%- endcomment -%}

<style>
  .hl-auth {
    margin: var(--sp-5) 0 var(--sp-6);
    padding: var(--sp-4) var(--sp-5);
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius);
  }

  .hl-auth__title {
    margin: 0 0 var(--sp-1);
    font-size: var(--fs-base);
    font-weight: 600;
    line-height: var(--lh-snug);
  }

  .hl-auth__hint {
    margin: 0 0 var(--sp-4);
    max-width: var(--measure);
    font-size: var(--fs-sm);
    color: var(--text-muted);
  }

  .hl-auth__form {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    gap: var(--sp-3);
  }

  .hl-auth__field {
    display: flex;
    flex-direction: column;
    gap: var(--sp-1);
    flex: 1 1 18rem;
  }

  .hl-auth__label {
    font-size: var(--fs-sm);
    font-weight: 600;
  }

  .hl-auth__input {
    width: 100%;
    padding: var(--sp-2) var(--sp-3);
    font-family: var(--font-sans);
    font-size: var(--fs-base);
    color: var(--text);
    background: var(--bg);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-sm);
  }

  .hl-auth__submit {
    padding: var(--sp-2) var(--sp-5);
    font-family: var(--font-sans);
    font-size: var(--fs-base);
    font-weight: 600;
    color: var(--bg);
    background: var(--brand);
    border: 1px solid var(--brand);
    border-radius: var(--radius-sm);
    cursor: pointer;
  }

  .hl-auth__submit:hover { background: var(--brand-strong); border-color: var(--brand-strong); }

  /* 3:1 focus ring, matching the rest of the site. */
  .hl-auth__input:focus-visible,
  .hl-auth__submit:focus-visible {
    outline: 3px solid var(--focus);
    outline-offset: 2px;
  }

  /* Reserves its own line height so acknowledging the entry does not shift
     the page under the reader. */
  .hl-auth__status {
    margin: var(--sp-3) 0 0;
    min-height: 1.5em;
    font-size: var(--fs-sm);
    color: var(--text-muted);
  }

  .hl-auth__status[data-state="ok"] { color: var(--note); font-weight: 600; }
</style>

<section class="hl-auth" aria-labelledby="hl-auth-title">
  <h2 class="hl-auth__title" id="hl-auth-title">Exam access</h2>
  <p class="hl-auth__hint">Honorlock fills this in for you during the launch
  check. If you are entering it by hand, use the password your proctor gives
  you.</p>

  <form class="hl-auth__form" id="hl-auth-form" autocomplete="off" novalidate>
    <div class="hl-auth__field">
      <label class="hl-auth__label" for="password">Exam password</label>
      <input class="hl-auth__input"
             type="password"
             id="password"
             name="password"
             autocomplete="off"
             autocapitalize="off"
             autocorrect="off"
             spellcheck="false">
    </div>
    <button class="hl-auth__submit" type="submit">Submit</button>
  </form>

  <p class="hl-auth__status" id="hl-auth-status" role="status" aria-live="polite"></p>
</section>

<script>
  /* Scoped to this page. Keeps the form from navigating away and acknowledges
     the entry - it does not check the password, and it does not hide or reveal
     any part of the activity. */
  (function () {
    'use strict';

    var form   = document.getElementById('hl-auth-form');
    var input  = document.getElementById('password');
    var status = document.getElementById('hl-auth-status');
    if (!form || !input || !status) return;

    form.addEventListener('submit', function (event) {
      event.preventDefault();

      if (!input.value) {
        status.removeAttribute('data-state');
        status.textContent = 'Enter the password, then press Submit.';
        input.focus();
        return;
      }

      status.setAttribute('data-state', 'ok');
      status.textContent = 'Password entered. The activity is below.';
    });
  }());
</script>

{%- comment -%} End of the page-scoped block. {%- endcomment -%}

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. What this page is

This is a **test page**, not a graded activity. It exists so that the Honorlock
launch flow can be run start to finish on a handout that looks exactly like a
real one — same layout, same password field, same URL shape — before it matters.

It is not listed on the [activities index](/activities/). The only way to reach
it is the link you were sent.

## 2. Before you start

1. Use Google Chrome. Honorlock's extension does not run anywhere else.
2. Install the Honorlock extension if you have not already.
3. Close every other tab. The launch check will ask you to.

## 3. The launch check

Work through it in order and stop at the first step that does not behave:

1. Launch the exam from Canvas. Honorlock takes over the tab.
2. Complete the identity steps — photo, ID, room scan.
3. When the password step comes up, watch the **Exam access** box at the top of
   this page. The field should fill itself.
4. Press **Submit**. The line under the box should read *Password entered.*

That fourth line is the whole test. If you see it, the password field was found,
filled and submitted, and a real activity behind this same setup will work.

## 4. If something goes wrong

| What you see | What it usually means |
| --- | --- |
| The field stays empty | No password is set on the Honorlock exam, or the extension did not attach — reload and relaunch |
| The extension never starts | You are not in Chrome, or the extension is disabled for this site |
| The page navigates away on Submit | JavaScript is blocked; the form is meant to stay put |
| Nothing appears under the box | The field was submitted while empty |

Report whichever row you landed on — that is what makes the dry run worth
running.

## 5. Notes for the instructor

- The password itself is configured in the **Honorlock exam settings**. It is
  deliberately not stored in this repository, which is public.
- Entering the password does not reveal or hide anything. The activity text is
  served to anyone who opens the URL. Any client-side gate here would be
  readable in View Source, so the field is present for the proctoring
  handshake and makes no security claim beyond it.
- The styling and behaviour above live in this file alone. Copy the block
  between the two comments into another handout to give it the same field.
