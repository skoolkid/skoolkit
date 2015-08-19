.. _migrating:

Migrating from SkoolKit 4
=========================
SkoolKit 5 includes some changes that make it incompatible with SkoolKit 4. If
you have developed a disassembly using SkoolKit 4 and find that the SkoolKit
commands no longer work with your control files or `skool` files, or produce
broken output, look through the following sections for tips on how to migrate
your disassembly to SkoolKit 5.

D directives
------------
In SkoolKit 4, the ``D`` directive in a control file could be used to define a
block description or a mid-block comment. In SkoolKit 5, the ``D`` directive
defines block descriptions only; to define a mid-block comment, use the ``N``
directive instead.

Address ranges in control directives
------------------------------------
In SkoolKit 4, the extent of a sub-block directive in a control file could be
specified by an address range; for example::

  B 40000-40009

In SkoolKit 5, address ranges are no longer supported, and this directive must
be rewritten with a length parameter::

  B 40000,10

ASM directives
--------------
In SkoolKit 4, ASM directives could be declared in a control file or a `skool`
file by starting a line with ``; @``; for example, in a control file::

  ; @label:24576=START

and in a `skool` file (or skool file template)::

  ; @label=START

This syntax is no longer supported. In SkoolKit 5, ASM directives must be
declared in a control file by using the ``@`` directive::

  @ 24576 label=START

and in a `skool` file (or skool file template) by starting a line with ``@``::

  @label=START

HTML templates and CSS
----------------------
If you are using any custom :ref:`htmlTemplates` - in particular the full-page
templates or the :ref:`t_anchor` template - or custom CSS, there are some
changes to be aware of.

In SkoolKit 4:

* the default full-page templates use the XHTML 1.0 Strict DOCTYPE
* every full-page template contains its own copy of the page footer
* the ``anchor`` template uses an ``<a>`` element with a ``name`` attribute
* every ``<a>`` element that defines a hyperlink has a ``class="link"``
  attribute

In SkoolKit 5:

* the default full-page templates have been converted to HTML5
* every full-page template uses the :ref:`t_footer` template to format the page
  footer
* the ``anchor`` template uses a ``<span>`` element with an ``id`` attribute
* the ``class="link"`` attribute has been removed from every ``<a>`` element
  that defines a hyperlink

This means that if you are using any custom full-page templates or a custom
``anchor`` template, you should ensure that they are consistent (i.e. produce
valid HTML5 or XHTML 1.0 as required when used in combination).

In addition, if you are using any custom full-page templates, you should either
replace the page footer (the ``<div class="footer">`` element) with a
``{t_footer}`` replacement field, or reinstate the CSS rule for ``div.footer``
from SkoolKit 4::

  div.footer {
    clear: both;
    margin-top: 10px;
    text-align: center;
  }

And finally, if you have defined any custom CSS rules for hyperlinks, you
should remove the 'link' class from the selectors. For example, this CSS rule
from `skoolkit.css` in SkoolKit 4::

  a.link { color: #ffff00; }

has become this in SkoolKit 5::

  a { color: #ffff00; }

skool2asm.py
------------
In SkoolKit 4 and earlier versions, :ref:`skool2asm.py` sported the
``-d/--crlf`` option (to use CR+LF to end lines instead of the system default),
the ``-i/--inst-width`` option (to set the width of the instruction field), and
the ``-t/--tabs`` option (to use tab to indent instructions). These options
have been removed in SkoolKit 5, but their effects can be achieved with the
new ``-P/--set`` option:

+--------------------+-------------------------------+
| SkoolKit 4         | SkoolKit 5                    |
+====================+===============================+
| ``--crlf``         | ``--set crlf=1``              |
+--------------------+-------------------------------+
| ``--inst-width N`` | ``--set instruction-width=N`` |
+--------------------+-------------------------------+
| ``--tabs``         | ``--set tab=1``               |
+--------------------+-------------------------------+

skoolkit4to5.py
---------------
The `skoolkit4to5.py`_ script may be used to convert a control file, `skool`
file, skool file template or CSS file that is compatible with SkoolKit 4 into a
file that will work with SkoolKit 5. For example, to convert `game.skool`::

  $ skoolkit4to5.py game.skool > game5.skool

.. _skoolkit4to5.py: https://github.com/skoolkid/skoolkit/raw/master/utils/skoolkit4to5.py
