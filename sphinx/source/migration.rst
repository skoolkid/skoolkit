.. _migrating:

Migrating from SkoolKit 5
=========================
SkoolKit 6 includes some changes that make it incompatible with SkoolKit 5. If
you have developed a disassembly using SkoolKit 5 and find that the SkoolKit
commands no longer work with your control files or skool files, or produce
broken output, look through the following sections for tips on how to migrate
your disassembly to SkoolKit 6.

#BUG, #FACT, #POKE
------------------
The ``#BUG``, ``#FACT`` and ``#POKE`` macros are no longer supported in
SkoolKit 6. However, they can be brought back into service by using suitable
:ref:`replace` directives to convert them into equivalent :ref:`LINK` macros.
For example::

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
