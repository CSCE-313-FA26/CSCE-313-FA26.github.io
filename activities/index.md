---
layout: home
title: Activities
heading: "Activities"
description: "Activities for CSCE 313, Fall 2026."
---

{% assign acts = site.pages | where_exp: "p", "p.activity_id" | where_exp: "p", "p.listed != false" %}
{%- comment -%}
Kramdown only makes a <table> when the markdown has at least one body row. With
no activities published it would otherwise print the pipe characters as a
paragraph and turn the separator row into em dashes, so the table is emitted
only when there is something to put in it.
{%- endcomment -%}
{% if acts.size > 0 %}
| Activity | Title | Builds on | Time |
| --- | --- | --- | --- |
{% for a in acts -%}
| [Activity {{ a.activity_id }}]({{ a.url | relative_url }}) | {{ a.activity_title }} | {{ a.relates_to }} | {{ a.duration }} |
{% endfor %}
{% endif %}
