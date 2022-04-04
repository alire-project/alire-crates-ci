---
layout: page
title: Build Times
---

<style>
.test {
    width: 100%;
    font-size: small;
    font-weight: bold;
}
.name {
    text-align: right;
}
.time {
    width: 100%;
    position: relative;
    color: white;
}
.timediv {
    background: LightSteelBlue;
    color: white;
    display: inline;
    font-weight: bold;
    position: absolute;
    top: 0;
}
.timetext {
    color: black;
    text-shadow: 1px 1px white;
    position: absolute;
    top: 0;
}

table, td {
    border: 0px solid;
}

.test a, .test a:hover {
    color: black;
}

</style>

## Build Times

Highest build time of all tests for a crate.

{% assign crates = site.data.crate_names | sort %}

<!-- Find worst time for percent -->
{% assign max_dur = 0.0 %}

{% for test in site.data.tests %}
    {% assign max_dur = test.duration | at_least: max_dur %}
{% endfor %}

<!-- Show each crate -->
<table>
{% for crate in crates %}

    {% assign duration = 0.0 %}
    {% assign duration_log = 0.0 %}

    {% for test in site.data.tests %}
    {% if test.crate == crate %}
        {% assign duration = test.duration | at_least: duration %}
        {% assign duration_log = test.duration_log | at_least: duration_log %}
    {% endif %}
    {% endfor %}

    {% assign width_pct = duration | times: 100.0 | divided_by: max_dur %}

    <!-- compute minutes -->
    {% assign minutes = duration | floor | divided_by: 60 %}
    {% assign minutes_in_seconds = minutes | times: 60 %}
    {% assign seconds = duration | minus: minutes_in_seconds %}

    {% assign dur_txt = "" %}
    {% if minutes > 0 %}
        {% assign dur_txt = dur_txt | append: minutes | append: "' " %}
    {% endif %}
    {% assign sec_txt = seconds | round | append: '"' %}
    {% assign dur_txt = dur_txt | append: sec_txt %}

<tr class="test">
    <td class="name">
        <a href="{{ "" | relative_url }}/crates/{{crate}}.html" target="_blank">{{ crate }}</a>
    </td>
    <td class="time">
        <div class="timediv" style="width:{{ width_pct }}%">
            &nbsp;
        </div>
        <div class="timetext">
            &nbsp;{{ dur_txt }}
        </div>
    </td>
</tr>
{% endfor %}
</table>
