Templates
=========

This documents describes templates structure.

base.html
---------

Base template for all other templates. It adds the following parts to the page:

* common css and js.
* busy indicator which is appears on all ajax requests.
* message dialog.

It provides the same blocks as bootstap's base.html
(see http://pythonhosted.org/Flask-Bootstrap/basic-usage.html for more info)
and the following blocks:

* subtitle - title block.
* content_class - class for the container div.

base_page.html
--------------

**base.html -> base_page.html**

Base template for pages with *content panel*.
Content panel is a panel with drop shadow effect which consist of 3 main parts:
header, content, footer. Header is consist of content and navigation bar.
This template adds the following parts to the page:

* content panel
* express navigation bar
* common js

It provides the following blocks:

* header_row - content panel header block.
* navbar_class - additional class for the navigation bar.
  Typical usage is to hide it with *hidden* calss.
* navbar_header_class - additional class for the navigation bar header.
  Typical usage is to add class *no-button* to hide navigation bar toggle button.
* nav_brand - left side navigation bar block. Typical usage is add back button.
* navbar_collapse - block with whole navigation bar (which contains top_menu).
* top_menu - header menu block.
* panel_content - panel content block.
* footer - footer block (by default contains div with class *footer-space*).
* page_script - page scripts inside *$(document).ready()* block.
* express_bar_anchor - id of the element on which show express bar.

Needs the following vars:

* back_url - express bar back url.
