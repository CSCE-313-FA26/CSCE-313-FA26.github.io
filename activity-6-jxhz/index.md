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

<figure class="diagram diagram--wide">
<div class="diagram-scroll" tabindex="0" role="group" aria-label="Figure 1, scrollable">
  <svg viewBox="0 0 760 350" role="img" aria-labelledby="fig1-title" xmlns="http://www.w3.org/2000/svg">
    <title id="fig1-title">The midpoint Riemann sum: six rectangles under the curve 4/(1+x squared) between x equals 0 and x equals 1</title>
    <desc>A falling curve runs from a height of 4 at x equals 0 to a height of 2 at x equals 1. Six rectangles of equal width stand under it, side by side, filling the area. Each rectangle's top edge meets the curve at a dot placed at the middle of that rectangle's base, so the top edge sits above the curve on the left half of the rectangle and below it on the right half. A bracket under the third rectangle is labelled step.</desc>
    <defs>
      <marker id="f1arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" class="d-arrow"/>
      </marker>
    </defs>

    <path d="M 86.0 38.0 L 86.0 292.0" class="d-edge"/>
    <path d="M 86.0 292.0 L 700.0 292.0" class="d-edge"/>
    <path d="M 81.0 292.0 L 86.0 292.0" class="d-edge"/>
    <text x="77.0" y="296.0" text-anchor="end" class="d-text--sm">0</text>
    <path d="M 81.0 236.1 L 86.0 236.1" class="d-edge"/>
    <text x="77.0" y="240.1" text-anchor="end" class="d-text--sm">1</text>
    <path d="M 81.0 180.2 L 86.0 180.2" class="d-edge"/>
    <text x="77.0" y="184.2" text-anchor="end" class="d-text--sm">2</text>
    <path d="M 81.0 124.3 L 86.0 124.3" class="d-edge"/>
    <text x="77.0" y="128.3" text-anchor="end" class="d-text--sm">3</text>
    <path d="M 81.0 68.4 L 86.0 68.4" class="d-edge"/>
    <text x="77.0" y="72.4" text-anchor="end" class="d-text--sm">4</text>
    <rect x="86.0" y="69.9" width="100.0" height="222.1" class="d-box--brand"/>
    <rect x="186.0" y="81.5" width="100.0" height="210.5" class="d-box--brand"/>
    <rect x="286.0" y="101.4" width="100.0" height="190.6" class="d-box--brand"/>
    <rect x="386.0" y="125.1" width="100.0" height="166.9" class="d-box--brand"/>
    <rect x="486.0" y="148.9" width="100.0" height="143.1" class="d-box--brand"/>
    <rect x="586.0" y="170.5" width="100.0" height="121.5" class="d-box--brand"/>
    <path d="M 86.0 68.4 L 91.0 68.4 L 96.0 68.4 L 101.0 68.5 L 106.0 68.6 L 111.0 68.8 L 116.0 68.9 L 121.0 69.1 L 126.0 69.4 L 131.0 69.6 L 136.0 69.9 L 141.0 70.2 L 146.0 70.6 L 151.0 71.0 L 156.0 71.4 L 161.0 71.8 L 166.0 72.3 L 171.0 72.8 L 176.0 73.3 L 181.0 73.8 L 186.0 74.4 L 191.0 75.0 L 196.0 75.6 L 201.0 76.3 L 206.0 77.0 L 211.0 77.7 L 216.0 78.4 L 221.0 79.1 L 226.0 79.9 L 231.0 80.7 L 236.0 81.5 L 241.0 82.4 L 246.0 83.2 L 251.0 84.1 L 256.0 85.0 L 261.0 85.9 L 266.0 86.8 L 271.0 87.8 L 276.0 88.7 L 281.0 89.7 L 286.0 90.7 L 291.0 91.7 L 296.0 92.8 L 301.0 93.8 L 306.0 94.9 L 311.0 95.9 L 316.0 97.0 L 321.0 98.1 L 326.0 99.2 L 331.0 100.3 L 336.0 101.4 L 341.0 102.6 L 346.0 103.7 L 351.0 104.9 L 356.0 106.0 L 361.0 107.2 L 366.0 108.4 L 371.0 109.5 L 376.0 110.7 L 381.0 111.9 L 386.0 113.1 L 391.0 114.3 L 396.0 115.5 L 401.0 116.7 L 406.0 117.9 L 411.0 119.1 L 416.0 120.3 L 421.0 121.5 L 426.0 122.7 L 431.0 123.9 L 436.0 125.1 L 441.0 126.4 L 446.0 127.6 L 451.0 128.8 L 456.0 130.0 L 461.0 131.2 L 466.0 132.4 L 471.0 133.6 L 476.0 134.8 L 481.0 136.0 L 486.0 137.2 L 491.0 138.4 L 496.0 139.5 L 501.0 140.7 L 506.0 141.9 L 511.0 143.1 L 516.0 144.2 L 521.0 145.4 L 526.0 146.6 L 531.0 147.7 L 536.0 148.9 L 541.0 150.0 L 546.0 151.2 L 551.0 152.3 L 556.0 153.4 L 561.0 154.5 L 566.0 155.6 L 571.0 156.7 L 576.0 157.8 L 581.0 158.9 L 586.0 160.0 L 591.0 161.1 L 596.0 162.2 L 601.0 163.2 L 606.0 164.3 L 611.0 165.3 L 616.0 166.4 L 621.0 167.4 L 626.0 168.4 L 631.0 169.5 L 636.0 170.5 L 641.0 171.5 L 646.0 172.5 L 651.0 173.5 L 656.0 174.5 L 661.0 175.4 L 666.0 176.4 L 671.0 177.4 L 676.0 178.3 L 681.0 179.2 L 686.0 180.2" class="d-curve"/>
    <circle cx="136.0" cy="69.9" r="3.5" class="d-dot"/>
    <circle cx="236.0" cy="81.5" r="3.5" class="d-dot"/>
    <circle cx="336.0" cy="101.4" r="3.5" class="d-dot"/>
    <circle cx="436.0" cy="125.1" r="3.5" class="d-dot"/>
    <circle cx="536.0" cy="148.9" r="3.5" class="d-dot"/>
    <circle cx="636.0" cy="170.5" r="3.5" class="d-dot"/>
    <text x="86.0" y="312.0" text-anchor="middle" class="d-text--sm">x = 0</text>
    <text x="686.0" y="312.0" text-anchor="middle" class="d-text--sm">x = 1</text>
    <text x="110.0" y="54.4" text-anchor="start" class="d-text--mono">4 / (1 + x²)</text>
    <path d="M 286.0 324.0 L 386.0 324.0" class="d-edge" marker-start="url(#f1arrow)" marker-end="url(#f1arrow)"/>
    <text x="336.0" y="340.0" text-anchor="middle" class="d-text--edge">step</text>
    <path d="M 476.0 79.1 L 440.0 119.1" class="d-edge--muted"/>
    <text x="480.0" y="77.1" text-anchor="start" class="d-text--sm">height taken at the midpoint</text>
  </svg>
</div>
<figcaption>Figure 1 — Six rectangles standing in for the area under 4/(1 + x²). The program uses a billion of them instead of six; the thinner they get, the less of the curve they miss, and the closer the total gets to π.</figcaption>
</figure>

Using the midpoint matters. On a falling curve, a left-edge rectangle takes its
height from the highest point of its base, so it sits entirely **above** the
curve and is always too big; a right-edge rectangle takes the lowest point and
is always too small. Either way every rectangle's error carries the same sign,
and a billion of them accumulate. A midpoint rectangle is too **short** over the
left half of its base and too **tall** over the right half, so its two errors
have opposite signs and very largely cancel inside each rectangle, before they
are ever added up. That is why a midpoint sum gives six correct digits here.

<figure class="diagram diagram--wide">
<div class="diagram-scroll" tabindex="0" role="group" aria-label="Figure 2, scrollable">
  <svg viewBox="0 0 760 330" role="img" aria-labelledby="fig2-title" xmlns="http://www.w3.org/2000/svg">
    <title id="fig2-title">Three ways to pick a rectangle's height, with the resulting error shaded in each case</title>
    <desc>Three panels each show the same short falling section of curve with a horizontal line across it marking the top of a rectangle. In the left panel the line is level with the curve's left end and the whole gap between line and curve is shaded as excess. In the right panel the line is level with the curve's right end and the whole gap is shaded as shortfall. In the middle panel the line meets the curve at the centre, so there is a shortfall wedge on the left and an excess wedge on the right, and the two wedges are of similar size.</desc>
    <path d="M 40.0 89.0 L 226.0 89.0 L 226.0 215.0 L 223.7 213.5 L 221.3 211.9 L 219.0 210.4 L 216.7 208.9 L 214.4 207.3 L 212.1 205.8 L 209.7 204.2 L 207.4 202.7 L 205.1 201.1 L 202.8 199.6 L 200.4 198.0 L 198.1 196.4 L 195.8 194.9 L 193.4 193.3 L 191.1 191.7 L 188.8 190.1 L 186.5 188.6 L 184.2 187.0 L 181.8 185.4 L 179.5 183.8 L 177.2 182.2 L 174.9 180.6 L 172.5 179.0 L 170.2 177.4 L 167.9 175.8 L 165.5 174.2 L 163.2 172.6 L 160.9 171.0 L 158.6 169.4 L 156.2 167.8 L 153.9 166.2 L 151.6 164.6 L 149.3 163.0 L 147.0 161.4 L 144.6 159.8 L 142.3 158.2 L 140.0 156.6 L 137.6 154.9 L 135.3 153.3 L 133.0 151.7 L 130.7 150.1 L 128.4 148.5 L 126.0 146.9 L 123.7 145.3 L 121.4 143.7 L 119.1 142.1 L 116.7 140.4 L 114.4 138.8 L 112.1 137.2 L 109.7 135.6 L 107.4 134.0 L 105.1 132.4 L 102.8 130.8 L 100.5 129.2 L 98.1 127.6 L 95.8 126.0 L 93.5 124.5 L 91.2 122.9 L 88.8 121.3 L 86.5 119.7 L 84.2 118.1 L 81.8 116.5 L 79.5 115.0 L 77.2 113.4 L 74.9 111.8 L 72.5 110.3 L 70.2 108.7 L 67.9 107.2 L 65.6 105.6 L 63.2 104.1 L 60.9 102.6 L 58.6 101.0 L 56.3 99.5 L 54.0 98.0 L 51.6 96.5 L 49.3 95.0 L 47.0 93.5 L 44.6 92.0 L 42.3 90.5 L 40.0 89.0 Z" class="d-fill--over"/>
    <path d="M 40.0 89.0 L 226.0 89.0" class="d-edge"/>
    <path d="M 40.0 89.0 L 42.3 90.5 L 44.6 92.0 L 47.0 93.5 L 49.3 95.0 L 51.6 96.5 L 54.0 98.0 L 56.3 99.5 L 58.6 101.0 L 60.9 102.6 L 63.2 104.1 L 65.6 105.6 L 67.9 107.2 L 70.2 108.7 L 72.5 110.3 L 74.9 111.8 L 77.2 113.4 L 79.5 115.0 L 81.8 116.5 L 84.2 118.1 L 86.5 119.7 L 88.8 121.3 L 91.2 122.9 L 93.5 124.5 L 95.8 126.0 L 98.1 127.6 L 100.5 129.2 L 102.8 130.8 L 105.1 132.4 L 107.4 134.0 L 109.7 135.6 L 112.1 137.2 L 114.4 138.8 L 116.7 140.4 L 119.1 142.1 L 121.4 143.7 L 123.7 145.3 L 126.0 146.9 L 128.4 148.5 L 130.7 150.1 L 133.0 151.7 L 135.3 153.3 L 137.6 154.9 L 140.0 156.6 L 142.3 158.2 L 144.6 159.8 L 147.0 161.4 L 149.3 163.0 L 151.6 164.6 L 153.9 166.2 L 156.2 167.8 L 158.6 169.4 L 160.9 171.0 L 163.2 172.6 L 165.5 174.2 L 167.9 175.8 L 170.2 177.4 L 172.5 179.0 L 174.9 180.6 L 177.2 182.2 L 179.5 183.8 L 181.8 185.4 L 184.2 187.0 L 186.5 188.6 L 188.8 190.1 L 191.1 191.7 L 193.4 193.3 L 195.8 194.9 L 198.1 196.4 L 200.4 198.0 L 202.8 199.6 L 205.1 201.1 L 207.4 202.7 L 209.7 204.2 L 212.1 205.8 L 214.4 207.3 L 216.7 208.9 L 219.0 210.4 L 221.3 211.9 L 223.7 213.5 L 226.0 215.0" class="d-curve"/>
    <circle cx="40.0" cy="89.0" r="3.5" class="d-dot"/>
    <path d="M 40.0 89.0 L 40.0 232.0" class="d-edge--muted"/>
    <path d="M 226.0 89.0 L 226.0 232.0" class="d-edge--muted"/>
    <text x="133.0" y="52" text-anchor="middle" class="d-title">left edge</text>
    <text x="133.0" y="258" text-anchor="middle" class="d-text--sm">always too big</text>
    <text x="133.0" y="276" text-anchor="middle" class="d-text--sm">every bit of it above the curve</text>
    <path d="M 284.0 151.7 L 377.0 151.7 L 377.0 151.7 L 374.7 150.1 L 372.4 148.5 L 370.0 146.9 L 367.7 145.3 L 365.4 143.7 L 363.1 142.1 L 360.7 140.4 L 358.4 138.8 L 356.1 137.2 L 353.8 135.6 L 351.4 134.0 L 349.1 132.4 L 346.8 130.8 L 344.4 129.2 L 342.1 127.6 L 339.8 126.0 L 337.5 124.5 L 335.1 122.9 L 332.8 121.3 L 330.5 119.7 L 328.2 118.1 L 325.9 116.5 L 323.5 115.0 L 321.2 113.4 L 318.9 111.8 L 316.6 110.3 L 314.2 108.7 L 311.9 107.2 L 309.6 105.6 L 307.2 104.1 L 304.9 102.6 L 302.6 101.0 L 300.3 99.5 L 297.9 98.0 L 295.6 96.5 L 293.3 95.0 L 291.0 93.5 L 288.6 92.0 L 286.3 90.5 L 284.0 89.0 Z" class="d-fill--under"/>
    <path d="M 377.0 151.7 L 470.0 151.7 L 470.0 215.0 L 467.7 213.5 L 465.3 211.9 L 463.0 210.4 L 460.7 208.9 L 458.4 207.3 L 456.1 205.8 L 453.7 204.2 L 451.4 202.7 L 449.1 201.1 L 446.8 199.6 L 444.4 198.0 L 442.1 196.4 L 439.8 194.9 L 437.4 193.3 L 435.1 191.7 L 432.8 190.1 L 430.5 188.6 L 428.1 187.0 L 425.8 185.4 L 423.5 183.8 L 421.2 182.2 L 418.9 180.6 L 416.5 179.0 L 414.2 177.4 L 411.9 175.8 L 409.5 174.2 L 407.2 172.6 L 404.9 171.0 L 402.6 169.4 L 400.2 167.8 L 397.9 166.2 L 395.6 164.6 L 393.3 163.0 L 391.0 161.4 L 388.6 159.8 L 386.3 158.2 L 384.0 156.6 L 381.6 154.9 L 379.3 153.3 L 377.0 151.7 Z" class="d-fill--over"/>
    <path d="M 284.0 151.7 L 470.0 151.7" class="d-edge"/>
    <path d="M 284.0 89.0 L 286.3 90.5 L 288.6 92.0 L 291.0 93.5 L 293.3 95.0 L 295.6 96.5 L 297.9 98.0 L 300.3 99.5 L 302.6 101.0 L 304.9 102.6 L 307.2 104.1 L 309.6 105.6 L 311.9 107.2 L 314.2 108.7 L 316.6 110.3 L 318.9 111.8 L 321.2 113.4 L 323.5 115.0 L 325.9 116.5 L 328.2 118.1 L 330.5 119.7 L 332.8 121.3 L 335.1 122.9 L 337.5 124.5 L 339.8 126.0 L 342.1 127.6 L 344.4 129.2 L 346.8 130.8 L 349.1 132.4 L 351.4 134.0 L 353.8 135.6 L 356.1 137.2 L 358.4 138.8 L 360.7 140.4 L 363.1 142.1 L 365.4 143.7 L 367.7 145.3 L 370.0 146.9 L 372.4 148.5 L 374.7 150.1 L 377.0 151.7 L 379.3 153.3 L 381.6 154.9 L 384.0 156.6 L 386.3 158.2 L 388.6 159.8 L 391.0 161.4 L 393.3 163.0 L 395.6 164.6 L 397.9 166.2 L 400.2 167.8 L 402.6 169.4 L 404.9 171.0 L 407.2 172.6 L 409.5 174.2 L 411.9 175.8 L 414.2 177.4 L 416.5 179.0 L 418.9 180.6 L 421.2 182.2 L 423.5 183.8 L 425.8 185.4 L 428.1 187.0 L 430.5 188.6 L 432.8 190.1 L 435.1 191.7 L 437.4 193.3 L 439.8 194.9 L 442.1 196.4 L 444.4 198.0 L 446.8 199.6 L 449.1 201.1 L 451.4 202.7 L 453.7 204.2 L 456.1 205.8 L 458.4 207.3 L 460.7 208.9 L 463.0 210.4 L 465.3 211.9 L 467.7 213.5 L 470.0 215.0" class="d-curve"/>
    <circle cx="377.0" cy="151.7" r="3.5" class="d-dot"/>
    <path d="M 284.0 151.7 L 284.0 232.0" class="d-edge--muted"/>
    <path d="M 470.0 151.7 L 470.0 232.0" class="d-edge--muted"/>
    <text x="377.0" y="52" text-anchor="middle" class="d-title">midpoint</text>
    <text x="377.0" y="258" text-anchor="middle" class="d-text">errors cancel</text>
    <text x="377.0" y="276" text-anchor="middle" class="d-text--sm">under on the left, over on the right</text>
    <path d="M 528.0 215.0 L 714.0 215.0 L 714.0 215.0 L 711.7 213.5 L 709.3 211.9 L 707.0 210.4 L 704.7 208.9 L 702.4 207.3 L 700.0 205.8 L 697.7 204.2 L 695.4 202.7 L 693.1 201.1 L 690.8 199.6 L 688.4 198.0 L 686.1 196.4 L 683.8 194.9 L 681.5 193.3 L 679.1 191.7 L 676.8 190.1 L 674.5 188.6 L 672.1 187.0 L 669.8 185.4 L 667.5 183.8 L 665.2 182.2 L 662.9 180.6 L 660.5 179.0 L 658.2 177.4 L 655.9 175.8 L 653.5 174.2 L 651.2 172.6 L 648.9 171.0 L 646.6 169.4 L 644.2 167.8 L 641.9 166.2 L 639.6 164.6 L 637.3 163.0 L 635.0 161.4 L 632.6 159.8 L 630.3 158.2 L 628.0 156.6 L 625.6 154.9 L 623.3 153.3 L 621.0 151.7 L 618.7 150.1 L 616.4 148.5 L 614.0 146.9 L 611.7 145.3 L 609.4 143.7 L 607.1 142.1 L 604.7 140.4 L 602.4 138.8 L 600.1 137.2 L 597.8 135.6 L 595.4 134.0 L 593.1 132.4 L 590.8 130.8 L 588.5 129.2 L 586.1 127.6 L 583.8 126.0 L 581.5 124.5 L 579.1 122.9 L 576.8 121.3 L 574.5 119.7 L 572.2 118.1 L 569.9 116.5 L 567.5 115.0 L 565.2 113.4 L 562.9 111.8 L 560.5 110.3 L 558.2 108.7 L 555.9 107.2 L 553.6 105.6 L 551.2 104.1 L 548.9 102.6 L 546.6 101.0 L 544.3 99.5 L 542.0 98.0 L 539.6 96.5 L 537.3 95.0 L 535.0 93.5 L 532.6 92.0 L 530.3 90.5 L 528.0 89.0 Z" class="d-fill--under"/>
    <path d="M 528.0 215.0 L 714.0 215.0" class="d-edge"/>
    <path d="M 528.0 89.0 L 530.3 90.5 L 532.6 92.0 L 535.0 93.5 L 537.3 95.0 L 539.6 96.5 L 542.0 98.0 L 544.3 99.5 L 546.6 101.0 L 548.9 102.6 L 551.2 104.1 L 553.6 105.6 L 555.9 107.2 L 558.2 108.7 L 560.5 110.3 L 562.9 111.8 L 565.2 113.4 L 567.5 115.0 L 569.9 116.5 L 572.2 118.1 L 574.5 119.7 L 576.8 121.3 L 579.1 122.9 L 581.5 124.5 L 583.8 126.0 L 586.1 127.6 L 588.5 129.2 L 590.8 130.8 L 593.1 132.4 L 595.4 134.0 L 597.8 135.6 L 600.1 137.2 L 602.4 138.8 L 604.7 140.4 L 607.1 142.1 L 609.4 143.7 L 611.7 145.3 L 614.0 146.9 L 616.4 148.5 L 618.7 150.1 L 621.0 151.7 L 623.3 153.3 L 625.6 154.9 L 628.0 156.6 L 630.3 158.2 L 632.6 159.8 L 635.0 161.4 L 637.3 163.0 L 639.6 164.6 L 641.9 166.2 L 644.2 167.8 L 646.6 169.4 L 648.9 171.0 L 651.2 172.6 L 653.5 174.2 L 655.9 175.8 L 658.2 177.4 L 660.5 179.0 L 662.9 180.6 L 665.2 182.2 L 667.5 183.8 L 669.8 185.4 L 672.1 187.0 L 674.5 188.6 L 676.8 190.1 L 679.1 191.7 L 681.5 193.3 L 683.8 194.9 L 686.1 196.4 L 688.4 198.0 L 690.8 199.6 L 693.1 201.1 L 695.4 202.7 L 697.7 204.2 L 700.0 205.8 L 702.4 207.3 L 704.7 208.9 L 707.0 210.4 L 709.3 211.9 L 711.7 213.5 L 714.0 215.0" class="d-curve"/>
    <circle cx="714.0" cy="215.0" r="3.5" class="d-dot"/>
    <path d="M 528.0 215.0 L 528.0 232.0" class="d-edge--muted"/>
    <path d="M 714.0 215.0 L 714.0 232.0" class="d-edge--muted"/>
    <text x="621.0" y="52" text-anchor="middle" class="d-title">right edge</text>
    <text x="621.0" y="258" text-anchor="middle" class="d-text--sm">always too small</text>
    <text x="621.0" y="276" text-anchor="middle" class="d-text--sm">every bit of it below the curve</text>
    <rect x="300" y="296" width="13" height="11" class="d-fill--under"/>
    <text x="319" y="306" class="d-text--sm">rectangle too short</text>
    <rect x="470" y="296" width="13" height="11" class="d-fill--over"/>
    <text x="489" y="306" class="d-text--sm">rectangle too tall</text>
  </svg>
</div>
<figcaption>Figure 2 — Why the midpoint is worth the trouble. An edge rule's error always carries the same sign, so it accumulates across a billion rectangles. The midpoint rule's two errors have opposite signs inside every single rectangle, so they cancel before they are ever added up.</figcaption>
</figure>

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

<figure class="diagram diagram--wide">
<div class="diagram-scroll" tabindex="0" role="group" aria-label="Figure 3, scrollable">
  <svg viewBox="0 0 760 330" role="img" aria-labelledby="fig3-title" xmlns="http://www.w3.org/2000/svg">
    <title id="fig3-title">Section 1 gives every other rectangle to a different thread, and each thread accumulates into its own slot</title>
    <desc>A row of eight numbered rectangles runs across the top, alternately shaded. Dashed lines run from the even-numbered ones down into a box labelled thread 0 and from the odd-numbered ones into a box labelled thread 1. An arrow runs from each thread box into its own accumulator, sum index 0 and sum index 1 respectively, so the two paths never meet.</desc>
    <defs>
      <marker id="f3arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" class="d-arrow"/>
      </marker>
    </defs>

    <rect x="48" y="54" width="66" height="44" rx="5" class="d-box--brand"/>
    <text x="81" y="82" text-anchor="middle" class="d-text--mono">i=0</text>
    <rect x="122" y="54" width="66" height="44" rx="5" class="d-box--busy"/>
    <text x="155" y="82" text-anchor="middle" class="d-text--mono">i=1</text>
    <rect x="196" y="54" width="66" height="44" rx="5" class="d-box--brand"/>
    <text x="229" y="82" text-anchor="middle" class="d-text--mono">i=2</text>
    <rect x="270" y="54" width="66" height="44" rx="5" class="d-box--busy"/>
    <text x="303" y="82" text-anchor="middle" class="d-text--mono">i=3</text>
    <rect x="344" y="54" width="66" height="44" rx="5" class="d-box--brand"/>
    <text x="377" y="82" text-anchor="middle" class="d-text--mono">i=4</text>
    <rect x="418" y="54" width="66" height="44" rx="5" class="d-box--busy"/>
    <text x="451" y="82" text-anchor="middle" class="d-text--mono">i=5</text>
    <rect x="492" y="54" width="66" height="44" rx="5" class="d-box--brand"/>
    <text x="525" y="82" text-anchor="middle" class="d-text--mono">i=6</text>
    <rect x="566" y="54" width="66" height="44" rx="5" class="d-box--busy"/>
    <text x="599" y="82" text-anchor="middle" class="d-text--mono">i=7</text>
    <text x="650" y="82" text-anchor="start" class="d-text--sm">…</text>
    <text x="740" y="36" text-anchor="end" class="d-text--sm">one billion rectangles in total</text>
    <text x="48" y="36" text-anchor="start" class="d-title">the rectangles, in order</text>
    <rect x="30" y="170" width="300" height="52" rx="6" class="d-box--brand"/>
    <text x="180" y="201" text-anchor="middle" class="d-text--mono">thread 0  —  i = 0, 2, 4, 6 …</text>
    <rect x="370" y="170" width="300" height="52" rx="6" class="d-box--busy"/>
    <text x="520" y="201" text-anchor="middle" class="d-text--mono">thread 1  —  i = 1, 3, 5, 7 …</text>
    <path d="M 81 100 L 180 168" class="d-edge--muted"/>
    <path d="M 155 100 L 520 168" class="d-edge--muted"/>
    <path d="M 229 100 L 180 168" class="d-edge--muted"/>
    <path d="M 303 100 L 520 168" class="d-edge--muted"/>
    <path d="M 377 100 L 180 168" class="d-edge--muted"/>
    <path d="M 451 100 L 520 168" class="d-edge--muted"/>
    <path d="M 525 100 L 180 168" class="d-edge--muted"/>
    <path d="M 599 100 L 520 168" class="d-edge--muted"/>
    <path d="M 180 224 L 180 262" class="d-edge" marker-end="url(#f3arrow)"/>
    <rect x="105" y="264" width="150" height="40" rx="5" class="d-box--brand"/>
    <text x="180" y="289" text-anchor="middle" class="d-text--mono">sum[0][0]</text>
    <path d="M 520 224 L 520 262" class="d-edge" marker-end="url(#f3arrow)"/>
    <rect x="445" y="264" width="150" height="40" rx="5" class="d-box--busy"/>
    <text x="520" y="289" text-anchor="middle" class="d-text--mono">sum[1][0]</text>
    <text x="350" y="322" text-anchor="middle" class="d-text--sm">each thread writes only its own slot — no mutex needed</text>
  </svg>
</div>
<figcaption>Figure 3 — The stride is what makes the work disjoint. No two threads ever touch the same slot, which is why Section 1 needs no mutex — and why the total is identical whatever NUM_THREADS is set to, even though the time is not.</figcaption>
</figure>

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

<figure class="diagram diagram--wide">
<div class="diagram-scroll" tabindex="0" role="group" aria-label="Figure 4, scrollable">
  <svg viewBox="0 0 760 300" role="img" aria-labelledby="fig4-title" xmlns="http://www.w3.org/2000/svg">
    <title id="fig4-title">Section 2 timeline: two sleeps run one after the other take two seconds, two sleeps that overlap take one</title>
    <desc>Two timelines share a scale marked 0, 1 and 2 seconds. On the upper one, labelled serial loop, two blocks each marked sleep of one second sit end to end and the row finishes at the 2 second mark. On the lower one, labelled threaded, the two blocks are stacked vertically and both start at 0, so the row finishes at the 1 second mark.</desc>
    <defs>
      <marker id="f4arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" class="d-arrow"/>
      </marker>
    </defs>

    <text x="20" y="54" class="d-title">serial loop</text>
    <text x="20" y="72" class="d-text--sm">one sleep after</text>
    <text x="20" y="88" class="d-text--sm">the other</text>
    <rect x="150.0" y="46" width="196.0" height="36" rx="4" class="d-box--warn"/>
    <text x="248.0" y="69" text-anchor="middle" class="d-text--mono">sleep(1)</text>
    <rect x="346.0" y="46" width="196.0" height="36" rx="4" class="d-box--warn"/>
    <text x="444.0" y="69" text-anchor="middle" class="d-text--mono">sleep(1)</text>
    <path d="M 150 96 L 566.0 96" class="d-edge"/>
    <path d="M 150.0 96 L 150.0 102" class="d-edge"/>
    <text x="150.0" y="116" text-anchor="middle" class="d-text--sm">0s</text>
    <path d="M 346.0 96 L 346.0 102" class="d-edge"/>
    <text x="346.0" y="116" text-anchor="middle" class="d-text--sm">1s</text>
    <path d="M 542.0 96 L 542.0 102" class="d-edge"/>
    <text x="542.0" y="116" text-anchor="middle" class="d-text--sm">2s</text>
    <text x="576.0" y="134" text-anchor="start" class="d-text">part 2 takes 2.00 s</text>
    <text x="20" y="194" class="d-title">threaded</text>
    <text x="20" y="212" class="d-text--sm">both sleep at</text>
    <text x="20" y="228" class="d-text--sm">the same time</text>
    <rect x="150.0" y="182" width="196.0" height="30" rx="4" class="d-box--brand"/>
    <text x="248.0" y="202" text-anchor="middle" class="d-text--mono">sleep(1)</text>
    <rect x="150.0" y="216" width="196.0" height="30" rx="4" class="d-box--brand"/>
    <text x="248.0" y="236" text-anchor="middle" class="d-text--mono">sleep(1)</text>
    <path d="M 150 250 L 566.0 250" class="d-edge"/>
    <path d="M 150.0 250 L 150.0 256" class="d-edge"/>
    <text x="150.0" y="270" text-anchor="middle" class="d-text--sm">0s</text>
    <path d="M 346.0 250 L 346.0 256" class="d-edge"/>
    <text x="346.0" y="270" text-anchor="middle" class="d-text--sm">1s</text>
    <path d="M 542.0 250 L 542.0 256" class="d-edge"/>
    <text x="542.0" y="270" text-anchor="middle" class="d-text--sm">2s</text>
    <text x="380.0" y="216" text-anchor="start" class="d-text">part 2 takes 1.00 s</text>
    <text x="380.0" y="234" text-anchor="start" class="d-text--sm">however many threads</text>
  </svg>
</div>
<figcaption>Figure 4 — What Section 2 buys you. The work is identical in both rows; only the waiting is rearranged. This is why part 2 drops to one second and stays there however many threads you add — sleeping parallelises perfectly.</figcaption>
</figure>

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

<figure class="diagram diagram--wide">
<div class="diagram-scroll" tabindex="0" role="group" aria-label="Figure 5, scrollable">
  <svg viewBox="0 0 760 430" role="img" aria-labelledby="fig5-title" xmlns="http://www.w3.org/2000/svg">
    <title id="fig5-title">Memory layout of the sum array at PAD equals 1 and PAD equals 8, against the 64-byte cache line boundary</title>
    <desc>Two rows of sixteen cells each represent consecutive doubles in memory, divided in half by a vertical line marking the boundary between two 64-byte cache lines. In the upper row, labelled PAD equals 1, the two shaded accumulator cells s0 and s1 are adjacent and both fall inside the first cache line. In the lower row, labelled PAD equals 8, s0 is the first cell of the first line and s1 is the first cell of the second line, with seven unused grey padding cells between them.</desc>
    <defs>
      <marker id="f5arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" class="d-arrow"/>
      </marker>
    </defs>

    <text x="28" y="52" class="d-title">both accumulators in ONE cache line</text>
    <text x="358" y="52" class="d-text--mono">PAD = 1</text>
    <rect x="28" y="92" width="44" height="38" class="d-box--brand"/>
    <text x="50" y="116" text-anchor="middle" class="d-text--mono">s0</text>
    <rect x="72" y="92" width="44" height="38" class="d-box--busy"/>
    <text x="94" y="116" text-anchor="middle" class="d-text--mono">s1</text>
    <rect x="116" y="92" width="44" height="38" class="d-box"/>
    <rect x="160" y="92" width="44" height="38" class="d-box"/>
    <rect x="204" y="92" width="44" height="38" class="d-box"/>
    <rect x="248" y="92" width="44" height="38" class="d-box"/>
    <rect x="292" y="92" width="44" height="38" class="d-box"/>
    <rect x="336" y="92" width="44" height="38" class="d-box"/>
    <rect x="380" y="92" width="44" height="38" class="d-box"/>
    <rect x="424" y="92" width="44" height="38" class="d-box"/>
    <rect x="468" y="92" width="44" height="38" class="d-box"/>
    <rect x="512" y="92" width="44" height="38" class="d-box"/>
    <rect x="556" y="92" width="44" height="38" class="d-box"/>
    <rect x="600" y="92" width="44" height="38" class="d-box"/>
    <rect x="644" y="92" width="44" height="38" class="d-box"/>
    <rect x="688" y="92" width="44" height="38" class="d-box"/>
    <path d="M 380 78 L 380 144" class="d-edge"/>
    <text x="204" y="72" text-anchor="middle" class="d-text--edge">cache line 1 — 64 bytes</text>
    <text x="556" y="72" text-anchor="middle" class="d-text--edge">cache line 2 — 64 bytes</text>
    <text x="28" y="164" class="d-text">core 0 and core 1 both write into line 1 — each write invalidates the other’s copy</text>
    <text x="28" y="184" class="d-text--sm">the line ping-pongs between the two caches, hundreds of millions of times: 2.856 s</text>
    <text x="28" y="242" class="d-title">each accumulator in its OWN cache line</text>
    <text x="358" y="242" class="d-text--mono">PAD = 8</text>
    <rect x="28" y="282" width="44" height="38" class="d-box--brand"/>
    <text x="50" y="306" text-anchor="middle" class="d-text--mono">s0</text>
    <rect x="72" y="282" width="44" height="38" class="d-box"/>
    <rect x="116" y="282" width="44" height="38" class="d-box"/>
    <rect x="160" y="282" width="44" height="38" class="d-box"/>
    <rect x="204" y="282" width="44" height="38" class="d-box"/>
    <rect x="248" y="282" width="44" height="38" class="d-box"/>
    <rect x="292" y="282" width="44" height="38" class="d-box"/>
    <rect x="336" y="282" width="44" height="38" class="d-box"/>
    <rect x="380" y="282" width="44" height="38" class="d-box--busy"/>
    <text x="402" y="306" text-anchor="middle" class="d-text--mono">s1</text>
    <rect x="424" y="282" width="44" height="38" class="d-box"/>
    <rect x="468" y="282" width="44" height="38" class="d-box"/>
    <rect x="512" y="282" width="44" height="38" class="d-box"/>
    <rect x="556" y="282" width="44" height="38" class="d-box"/>
    <rect x="600" y="282" width="44" height="38" class="d-box"/>
    <rect x="644" y="282" width="44" height="38" class="d-box"/>
    <rect x="688" y="282" width="44" height="38" class="d-box"/>
    <path d="M 380 268 L 380 334" class="d-edge"/>
    <text x="204" y="262" text-anchor="middle" class="d-text--edge">cache line 1 — 64 bytes</text>
    <text x="556" y="262" text-anchor="middle" class="d-text--edge">cache line 2 — 64 bytes</text>
    <text x="28" y="354" class="d-text">core 0 owns line 1, core 1 owns line 2 — neither write disturbs the other</text>
    <text x="28" y="374" class="d-text--sm">same answer, 39% faster: 2.054 s — the seven grey cells are the padding that buys it</text>
    <text x="28" y="418" class="d-text--sm">s0 = sum[0][0], written only by thread 0.   s1 = sum[1][0], written only by thread 1.   grey = never read or written.</text>
  </svg>
</div>
<figcaption>Figure 5 — The padding is pure waste in memory and pure gain in time. Neither thread ever reads the other's slot, so the contention at PAD = 1 is an accident of address, not a defect in the program — which is exactly why no test catches it.</figcaption>
</figure>

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
