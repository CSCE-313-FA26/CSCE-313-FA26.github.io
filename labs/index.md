---
layout: home
title: Labs
heading: "Labs"
description: "Lab handouts for CSCE 313, Fall 2026."
---

{% assign labs = site.pages | where_exp: "p", "p.lab_number" | sort: "lab_number" %}
| Lab | Title | Released | Due |
| --- | --- | --- | --- |
{% for lab in labs -%}
| [Lab {{ lab.lab_number }}]({{ lab.url | relative_url }}) | {{ lab.lab_title }} | {{ lab.released_short }} | {{ lab.due_short }} |
{% endfor %}
