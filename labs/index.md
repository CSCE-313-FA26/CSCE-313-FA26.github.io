---
layout: home
title: Labs
heading: "Labs"
description: "Lab handouts for CSCE 313, Fall 2026."
---

{% assign labs = site.pages | where_exp: "p", "p.lab_number" | where_exp: "p", "p.listed != false" | sort: "lab_number" %}
{%- comment -%}
Kramdown only makes a <table> when at least one body row exists; guarded so an
empty list cannot render as raw pipe characters.
{%- endcomment -%}
{% if labs.size > 0 %}
| Lab | Title | Released | Due |
| --- | --- | --- | --- |
{% for lab in labs -%}
| [Lab {{ lab.lab_number }}]({{ lab.url | relative_url }}) | {{ lab.lab_title }} | {{ lab.released_short }} | {{ lab.due_short }} |
{% endfor %}
{% endif %}
