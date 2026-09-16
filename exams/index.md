---
layout: home
title: Exams
heading: "Exams"
description: "Exam instructions for CSCE 313, Fall 2026."
---

{% assign exams = site.pages | where_exp: "p", "p.exam_number" | where_exp: "p", "p.listed != false" | sort: "exam_number" %}
{%- comment -%}
Kramdown only makes a <table> when at least one body row exists; guarded so an
empty list cannot render as raw pipe characters.
{%- endcomment -%}
{% if exams.size > 0 %}
| Exam | Title | Released | Due |
| --- | --- | --- | --- |
{% for exam in exams -%}
| [Exam {{ exam.exam_number }}]({{ exam.url | relative_url }}) | {{ exam.exam_title }} | {{ exam.released_short }} | {{ exam.due_short }} |
{% endfor %}
{% endif %}
