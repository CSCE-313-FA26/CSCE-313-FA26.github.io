---
layout: home
title: Activities
heading: "Activities"
description: "Activities for CSCE 313, Fall 2026."
---

{% assign acts = site.pages | where_exp: "p", "p.activity_id" %}
| Activity | Title | Builds on | Time |
| --- | --- | --- | --- |
{% for a in acts -%}
| [Activity {{ a.activity_id }}]({{ a.url | relative_url }}) | {{ a.activity_title }} | {{ a.relates_to }} | {{ a.duration }} |
{% endfor %}
