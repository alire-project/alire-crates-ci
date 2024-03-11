---
layout: page
---

<style>
.button {
  border: none;
  color: white;
  padding: 16px 32px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  margin: 4px 2px;
  transition-duration: 0.4s;
  background-color: black;
  text-color: white;
  border-radius: 20px;
}
.button:hover {
  background-color: #EE8E4A;
  color: white;
}
.button > h3 {
    padding: 0em;
    margin: 0px;
    font-weight: bold;
}
</style>

## Alire Crates Build Results

This repository contains the test results of building the latest release of every crate in the community index.

Refer to the sections in the header for the various available reports.

(NOTE: the testing pipeline is still being fine-tuned, there are known false positives in these reports.)

{% assign badge_url = "https://img.shields.io/endpoint?url=https://alire.ada.dev/badges/alire-badge.json" %}
<img src="{{badge_url}}" title="Copy image location: {{badge_url}}">
