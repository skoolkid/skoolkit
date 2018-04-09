Parsing, rendering, and modes
=============================
The following subsections explain at a high level the two phases involved in
transforming a skool file (and its related ref files, if any exist) into HTML
or ASM format by using :ref:`skool2html.py` or :ref:`skool2asm.py`: parsing and
rendering.

Parsing
-------
In the first phase, the skool file is parsed. Parsing a skool file entails
reading each line of the file, and processing any relevant
:ref:`ASM directives <asmDirectives>` that are found along the way.

After an ASM directive has been processed, it is discarded, so that it cannot
be 'seen' during the rendering phase. The purpose of the ASM directives is to
transform the skool file into something suitable for rendering (in either HTML
or ASM format) later on.

Whether a particular ASM directive is processed depends on the mode in which
the parsing is being done: HTML mode or ASM mode.

HTML mode
^^^^^^^^^
HTML mode is used when the target output format is HTML, as is the case when
running `skool2html.py`. In HTML mode, some ASM directives are ignored because
they are irrelevant to the purpose of creating the HTML version of the
disassembly. The only ASM directives that are processed in HTML mode are the
following:

* :ref:`assemble`
* :ref:`defb`
* :ref:`defs`
* :ref:`defw`
* :ref:`asm-if`
* :ref:`keep`
* :ref:`label`
* :ref:`remote`
* :ref:`replace`
* :ref:`bfixBlockDirectives`
* :ref:`isubBlockDirectives`
* :ref:`ofixBlockDirectives`
* :ref:`rfixBlockDirectives`
* :ref:`rsubBlockDirectives`
* :ref:`ssubBlockDirectives`

The reason that the block directives are processed is that they may define two
different versions of a section of code or data: first, a version to include in
the output if the corresponding ASM mode (:ref:`@bfix <bfixMode>`,
:ref:`@isub <isubMode>`, :ref:`@ofix <ofixMode>`, :ref:`@rfix <rfixMode>`,
:ref:`@rsub <rsubMode>`, :ref:`@ssub <ssubMode>`) is in effect; and second, a
version to include in the output if the corresponding ASM mode is not in
effect - which will always be the case when parsing in HTML mode.

For example::

  @bfix-begin
   32459 CP 26  ; This is a bug; it should be 'CP 27'
  @bfix+else
         CP 27  ;
  @bfix+end

This instance of a ``@bfix`` block directive defines two versions of a section
of code. The first version (between ``@bfix-begin`` and ``@bfix+else``) will be
included in the HTML output, and the second version (between ``@bfix+else`` and
``@bfix+end``) will be omitted.

ASM mode
^^^^^^^^
ASM mode is used when the target output format is ASM, as is the case when
running `skool2asm.py`. In ASM mode, all ASM directives are processed.

Rendering
---------
In the second phase, the skool file (stripped of all its ASM directives during
the parsing phase) is 'rendered' - as either HTML or ASM, depending on the
mode.

HTML mode
^^^^^^^^^
HTML mode is used to render the skool file (and its related ref file, if one
exists) as a bunch of HTML files. During rendering, any
:ref:`skool macros <skoolMacros>` found along the way are expanded to the
required HTML markup.

ASM mode
^^^^^^^^
ASM mode is used to render the skool file as a single, assembler-ready ASM
file. During rendering, any :ref:`skool macros <skoolMacros>` found along the
way are expanded to some appropriate plain text.
