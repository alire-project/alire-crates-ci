---
layout: page
title: Crate Status
---

<style>
.name {
    display: inline-block;
    vertical-align: middle;
    font-weight: bold;
}
.letter {
    display: inline-block;
    vertical-align: middle;
    font-weight: bold;
    font-size: 120%;
    color: black;
    padding-left: 0.2em;
    padding-right: 0.2em;
}

.results {
    position: absolute;
    display: inline-block;
    visibility: hidden;
    z-index: 1;
    background: gainsboro;
    padding: 0.3em;
    color: black;
    text-align: left;
    border-radius: 0.3em;
}
.name:hover .results {
  visibility: visible;
}

.results th {
    font-weight: bolder;
    background: white;
}

.results td, .results th {
    padding-left: 0.5em;
    padding-right: 0.5em;
}

.results a {
    color: inherit;
    text-decoration: underline;
}

.noresults tr:nth-child(odd) { background: white; }

</style>

## Crate Status

{% assign prev_letter = "" %}

<center>

{% assign crate_names = site.data.crate_names | sort %}

{% for name in crate_names %}
    {% assign pass = 0 %}
    {% assign miss = 0 %}
    {% assign fail = 0 %}

    {% for test in site.data.tests %}
        {% if test.crate == name %}
            {% case test.status %}
                {% when "unavailable" %}
                {% when "untested" %}
                {% when "missing-dependencies" %}
                    {% assign miss = miss | plus: 1 %}
                {% when "success" %}
                    {% assign pass = pass | plus: 1 %}
                {% else %}
                    {% assign fail = fail | plus: 1 %}
            {% endcase %}
        {% endif %}
    {% endfor %}

    {% if pass == 0 and fail == 0 and miss == 0 %}
        {% assign class = "untested" %}
    {% elsif pass != 0 and fail == 0 %}
        {% assign class = "pass" %}
    {% elsif pass == 0 and fail != 0 %}
        {% assign class = "fail" %}
    {% else %}
        {% assign class = "mixed" %}
    {% endif %}

{% assign curr_letter = name | slice: 0, 1 %}
{% if curr_letter != prev_letter %}
<div class="letter">{{ curr_letter | upcase }}</div>
{% endif %}
{% assign prev_letter = curr_letter %}

<div class="name {{class}}">
    <div class="results">
        <a href="{{ "" | relative_url }}/crates/{{name}}.html" target="_blank">{{ name | upcase }}</a><br>
        ---<br>
        <table>
        <tr><th>Version</th><th>GNAT</th><th>OS</th><th>Distro</th><th>Status</th></tr>
        {% for test in site.data.tests %}
            {% if test.crate == name %}
            <tr>
                <td>{{test.version}}</td>
                <td>{{test.gnat}}</td>
                <td>{{test.platform | capitalize}}</td>
                <td>{{test.distro | capitalize}}</td>
                <td class="{{test.status}}">
                <a target="_blank"
                href="{{ '' | relative_url }}/status/{{ test.crate | slice: 0, 2 }}/{{ test.crate }}/{{ test.version }}/{{ test.platform }}/{{ test.distro }}/gnat={{ test.gnat }}/{{test.crate}}-{{test.version}}.yaml.log"
                >
                {{test.status}}
                </a>
                </td>
            </tr>
            {% endif %}
        {% endfor %}
        </table>
    </div>
    {{ name }}
</div>
{% endfor %}

</center>
