<div class="tabs">

{% assign idx = 0 %}

<!-- Find all different distros -->
{% assign distros = '' | split: '' %}
{% for test in site.data.tests %}
  {%- assign distro_as_array = test.distro | split: ',' -%}
  {%- assign distros = distros | concat: distro_as_array | uniq -%}
{% endfor %}

{% for distro in distros %}

{% assign idx = idx | plus: 1 %}

<!-- Extract unique crate names and tests to kept -->
{%- assign crates = '' | split: '' -%}
{%- for test in site.data.tests -%}
  {% if test.distro == distro %}
    {%- assign crate = test.crate | split: ',' -%}
    {%- if include.blacklist and test.status != include.status and test.status != "unavailable" -%}
        {%- assign crates = crates | concat: crate | uniq -%}
    {%- else -%}
        <!-- {{ crate }} blacklisted -->
    {%- endif -%}
    {%- if include.whitelist and test.status == include.status and test.status != "unavailable"
            or include.status == "unavailable" and test.status == "unavailable" -%}
        {%- assign crates = crates | concat: crate | uniq -%}
    {%- else -%}
        <!-- {{ crate }} blacklisted -->
    {%- endif -%}
  {%- endif -%}
{%- endfor -%}

<div class="tab">
  <input type="checkbox" id="plat{{ idx }}" name="platforms">
  <label class="tab-label" for="plat{{ idx }}">
    {% assign platname = distro | replace: ' ', '-' | replace: '.', '-' %}
    {{ distro | replace: '-', ' ' | upcase }} <div class="note">&nbsp;({{ crates.size }} crates)</div>
  </label>
  <div class="tab-content">
    <!-- Add each crate report -->
    {% for crate in crates %}
      <div class="tab">
        <input type="checkbox" id="crate-{{ crate }}-{{platname}}" name="crates-{{platname}}">
        <label class="tab-label" for="crate-{{ crate }}-{{platname}}">{{ crate }}</label>
        {%- for test in site.data.tests -%}
        {%- if test.crate == crate and test.distro == distro -%}
            <div class="tab-content" markdown=1>
### <small>v{{test.version}} compiled with GNAT {{ test.gnat }}</small>
- Status: {{ test.status | upcase }}
- Attempted: {{ test.last_attempt }}
- [Log]({{ "" | relative_url }}/status/{{ test.crate | slice: 0, 2 }}/{{ test.crate }}/{{ test.version }}/{{ test.platform }}/{{ test.distro }}/gnat={{ test.gnat }}/{{test.crate}}-{{test.version}}.yaml.log){:target="_blank"}
</div>
<!-- cant indent or markdown never ends -->
        {%- endif -%}
        {%- endfor -%}
      </div>
    {% endfor %}
  </div>
</div>

{% endfor %}

<!--
<div class="tab">
  <input type="radio" id="rd3" name="platforms">
  <label for="rd3" class="tab-close">Close others &times;</label>
</div>
-->

</div>