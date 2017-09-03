.. _migrating:

Migrating from SkoolKit 5
=========================
SkoolKit 6 includes some changes that make it incompatible with SkoolKit 5. If
you have developed a disassembly using SkoolKit 5 and find that the SkoolKit
commands no longer work with your skool files or ref files, or produce broken
output, look through the following sections for tips on how to migrate your
disassembly to SkoolKit 6.

#BUG, #FACT, #POKE
------------------
The ``#BUG``, ``#FACT`` and ``#POKE`` macros are not supported in SkoolKit 6.
However, they can be brought back into service by using suitable :ref:`replace`
directives to convert them into equivalent :ref:`LINK` macros. For example::

  @replace=/#BUG(#[a-zA-Z\d$#]+(?![a-zA-Z\d$#(])|(?![#(A-Z]))/#LINK:Bugs\1(bug)
  @replace=/#BUG(?![A-Z])/#LINK:Bugs

The first directive replaces ``#BUG`` macros that have no link text parameter
(as in ``This is a #BUG#bug1.``); it may be omitted if all the ``#BUG`` macros
in your disassembly have a link text parameter. The second directive replaces
``#BUG`` macros that do have a link text parameter.

The corresponding ``@replace`` directives for the ``#FACT`` macro are::

  @replace=/#FACT(#[a-zA-Z\d$#]+(?![a-zA-Z\d$#(])|(?![#(A-Z]))/#LINK:Facts\1(fact)
  @replace=/#FACT(?![A-Z])/#LINK:Facts

And for the ``#POKE`` macro::

  @replace=/#POKE(#[a-zA-Z\d$#]+(?![a-zA-Z\d$#(])|(?![#(A-Z]))/#LINK:Pokes\1(poke)
  @replace=/#POKE(?![A-Z])/#LINK:Pokes

#EREFS, #REFS
-------------
The ``#EREFS`` and ``#REFS`` macros are not supported in SkoolKit 6.

A near equivalent to the ``#EREFS`` macro can be defined by using the
:ref:`replace` directive thus::

  @replace=/#erefs\i/#IF(#neref\1);;the routine#IF(#neref\1>1)(s) at #FOREACH(EREF\1)||n|#Rn|, | and ||;no other routines;;
  @replace=/#neref\i/0#FOREACH(EREF\1)(n,+1)

and used like this::

  ; This entry point is used by #erefs32769.

A near equivalent to the ``#REFS`` macro can be defined by using the
:ref:`replace` directive thus::

  @replace=/#refs\i/#IF(#nref\1);;the routine#IF(#nref\1>1)(s) at #FOREACH(REF\1)||n|#Rn|, | and ||;no other routines;;
  @replace=/#nref\i/0#FOREACH(REF\1)(n,+1)

and used like this::

  ; Used by #refs32768.

[PageContent:\*]
----------------
``[PageContent:*]`` sections are not supported in SkoolKit 6; instead, the
``PageContent`` parameter in the :ref:`page` section should be used.

If you have a ``[PageContent:*]`` section consisting of a single line, then
bring that line into the ``PageContent`` parameter of a corresponding
``[Page:*]`` section. For example::

  [PageContent:MyPage]
  #CALL:myPageContents()

can be replaced by::

  [Page:MyPage]
  PageContent=#CALL:myPageContents()

If you have a ``[PageContent:*]`` section consisting of more than one line,
then add a ``[Page:*]`` section (or update an existing one) with a
``PageContent`` parameter that uses the :ref:`INCLUDE` macro. For example::

  [PageContent:MyOtherPage]
  Line 1.
  Line 2.

can be activated by adding a corresponding ``[Page:*]`` section::

  [Page:MyOtherPage]
  PageContent=#INCLUDE(PageContent:MyOtherPage)

Created
-------
In SkoolKit 5, wherever ``$VERSION`` appeared in the ``Created`` parameter in
the :ref:`ref-Game` section, it was replaced by the version number of SkoolKit.
In SkoolKit 6, this replacement is no longer made; use the :ref:`VERSION` macro
instead.

DefaultAnimationFormat
----------------------
In SkoolKit 5, the ``DefaultAnimationFormat`` parameter in the
:ref:`ref-ImageWriter` section defaulted to the value of the ``DefaultFormat``
parameter (``png`` by default). In SkoolKit 6, ``DefaultAnimationFormat``
defaults to ``gif``.

UDGFilename
-----------
In SkoolKit 5, the ``UDGFilename`` parameter lived in the :ref:`ref-Game`
section. In SkoolKit 6, it has moved to the :ref:`paths` section.

changelog_* templates
---------------------
The ``changelog_entry`` and ``changelog_item_list`` templates have been renamed
:ref:`t_list_entry` and :ref:`t_list_items`. (They are general purpose
templates used not just by the 'Changelog' page, but by any
:ref:`box page <boxpages>` whose ``SectionType`` is ``BulletPoints`` or
``ListItems``.) Accordingly, the ``t_changelog_item_list`` and
``m_changelog_item`` identifiers in those templates have been renamed
``t_list_items`` and ``m_list_item``.

CSS selectors
-------------
The `class` attributes of some HTML elements have changed in SkoolKit 6.

The following table lists the selectors that appeared in the CSS files in
SkoolKit 5, and their replacements in SkoolKit 6.

===================  ==========
SkoolKit 5           SkoolKit 6
===================  ==========
div.changelog        div.list-entry
div.changelog-1      div.list-entry-1
div.changelog-2      div.list-entry-2
div.changelog-desc   div.list-entry-desc
div.changelog-title  div.list-entry-title
ul.changelog         ul.list-entry
===================  ==========

In addition, the 'ul.changelogN' selector (N=1, 2, 3 etc.), which is used in
the stock :ref:`t_list_items` template but is unstyled (i.e. does not appear in
any of the CSS files), has been replaced by 'ul.list-entryN' in SkoolKit 6.

PageHeaders:Asm-t
-----------------
In SkoolKit 5, the default :ref:`header <pageHeaders>` for ``Asm-t`` pages
(disassembly pages for 't' blocks) was 'Data'. In SkoolKit 6, it is 'Messages'.

Titles:Asm-t
------------
In SkoolKit 5, the default :ref:`title <titles>` for ``Asm-t`` pages
(disassembly pages for 't' blocks) was 'Data at'. In SkoolKit 6, it is 'Text
at'.

bin2tap.py -t
-------------
In SkoolKit 5, :ref:`bin2tap.py` had a ``-t/--tapfile`` option for specifying
the output TAP filename. In SkoolKit 6, this option is not supported; instead
the TAP filename should be specified, if necessary, after the input filename.
For example::

  $ bin2tap.py in.bin out.tap

skool2ctl.py -a
---------------
In SkoolKit 5, :ref:`skool2ctl.py` had a ``-a/--no-asm-dirs`` option for
omitting ASM directives from the output. In SkoolKit 6, this option is not
supported; instead, the ``-w/--write`` option now recognises the 'a' identifier
for specifying whether to include ASM directives in the output.

skool2html.py -w
----------------
In SkoolKit 5, the ``-w/--write`` option of :ref:`skool2html.py` recognised the
'B' (Graphic glitches), 'b' (Bugs), 'c' (Changelog), 'p' (Pokes), 't' (Trivia)
and 'y' (Glossary) file identifiers. In SkoolKit 6, these file identifiers are
not supported; instead, the 'P' file identifier should be used along with the
``-P/--pages`` option.

For example, to write only the 'Bugs' and 'Changelog' pages::

  $ skool2html.py --write P --pages Bugs,Changelog game.ref

Udg
---
In SkoolKit 5.4, the :class:`~skoolkit.graphics.Udg` class moved from
skoolkit.skoolhtml to skoolkit.graphics, but was still available in
skoolkit.skoolhtml. In SkoolKit 6, it is no longer available in
skoolkit.skoolhtml.

flip_udgs()
-----------
The :meth:`flip_udgs` method on HtmlWriter has been removed in SkoolKit 6. Use
the :func:`~skoolkit.graphics.flip_udgs` function in skoolkit.graphics instead.

rotate_udgs()
-------------
The :meth:`rotate_udgs` method on HtmlWriter has been removed in SkoolKit 6.
Use the :func:`~skoolkit.graphics.rotate_udgs` function in skoolkit.graphics
instead.

parse_image_params()
--------------------
The :meth:`parse_image_params` method on HtmlWriter has been removed in
SkoolKit 6. Use the :func:`~skoolkit.skoolmacro.parse_image_macro` function
instead.

parse_params()
--------------
The :func:`parse_params` function in skoolkit.skoolmacro has been removed in
SkoolKit 6. Use the :func:`~skoolkit.skoolmacro.parse_ints` and
:func:`~skoolkit.skoolmacro.parse_brackets` functions instead.

skoolkit5to6.py
---------------
The `skoolkit5to6.py`_ script may be used to convert a ref file or CSS file
that is compatible with SkoolKit 5 into a file that will work with SkoolKit 6.
For example, to convert `game.ref`::

  $ skoolkit5to6.py game.ref > game6.ref

.. _skoolkit5to6.py: https://github.com/skoolkid/skoolkit/raw/master/utils/skoolkit5to6.py
