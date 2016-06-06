.. _extendingSkoolKit:

.. highlight:: python

Extending SkoolKit
==================

Extension modules
-----------------
While creating a disassembly of a game, you may find that SkoolKit's suite of
:ref:`skool macros <skoolMacros>` is inadequate for certain tasks. For example,
the game might have large tile-based sprites that you want to create images of
for the HTML disassembly, and composing long ``#UDGARRAY`` macros for them or
defining a new sprite-building macro with the ``@replace`` directive (see
:ref:`definingMacrosWithReplace`) would be too tedious or impractical. Or you
might want to insert a timestamp somewhere in the ASM disassembly so that you
(or others) can keep track of when your ASM files were written.

One way to solve these problems is to add custom methods that could be called
by a :ref:`call` macro. But where to add the methods? SkoolKit's core
HTML writer and ASM writer classes are skoolkit.skoolhtml.HtmlWriter and
skoolkit.skoolasm.AsmWriter, so you could add the methods to those classes. But
a better way is to subclass HtmlWriter and AsmWriter in a separate extension
module, and add the methods there; then that extension module can be easily
used with different versions of SkoolKit, and shared with other people.

A minimal extension module would look like this::

  from skoolkit.skoolhtml import HtmlWriter
  from skoolkit.skoolasm import AsmWriter

  class GameHtmlWriter(HtmlWriter):
      pass

  class GameAsmWriter(AsmWriter):
      pass

The next step is to get SkoolKit to use the extension module for your game.
First, place the extension module (let's call it `game.py`) in the `skoolkit`
package directory; to locate this directory, run :ref:`skool2html.py` with the
``-p`` option::

  $ skool2html.py -p
  /usr/lib/python2.7/dist-packages/skoolkit

(The package directory may be different on your system.) With `game.py` in
place, add the following line to the :ref:`ref-Config` section of your
disassembly's ref file::

  HtmlWriterClass=skoolkit.game.GameHtmlWriter

If you don't have a ref file yet, create one (ideally named `game.ref`,
assuming the skool file is `game.skool`); if the ref file doesn't have a
``[Config]`` section yet, add one.

Now whenever :ref:`skool2html.py` is run on your skool file (or ref file),
SkoolKit will use the GameHtmlWriter class instead of the core HtmlWriter
class.

To get :ref:`skool2asm.py` to use GameAsmWriter instead of the core AsmWriter
class when it's run on your skool file, add the following :ref:`writer` ASM
directive somewhere after the ``@start`` directive, and before the ``@end``
directive (if there is one)::

  @writer=skoolkit.game.GameAsmWriter

The `skoolkit` package directory is a reasonable place for an extension module,
but it could be placed in another package, or somewhere else as a standalone
module. For example, if you wanted to keep a standalone extension module named
`game.py` in `~/.skoolkit`, you should set the ``HtmlWriterClass`` parameter
thus::

  HtmlWriterClass=~/.skoolkit:game.GameHtmlWriter

and the ``@writer`` directive thus::

  @writer=~/.skoolkit:game.GameAsmWriter

The HTML writer or ASM writer class can also be specified on the command line
by using the ``-W``/``--writer`` option of :ref:`skool2html.py` or
:ref:`skool2asm.py`. For example::

  $ skool2html.py -W ~/.skoolkit:game.GameHtmlWriter game.skool

Specifying the writer class this way will override any ``HtmlWriterClass``
parameter in the ref file or ``@writer`` directive in the skool file.

Note that if the writer class is specified with a blank module path (e.g.
``:game.GameHtmlWriter``), SkoolKit will search for the module in both the
current working directory and the directory containing the skool file or ref
file named on the command line.

#CALL methods
-------------
Implementing a method that can be called by a :ref:`call` macro is done by
adding the method to the HtmlWriter or AsmWriter subclass in the extension
module.

One thing to be aware of when adding a ``#CALL`` method to a subclass of
HtmlWriter is that the method must accept an extra parameter in addition to
those passed from the ``#CALL`` macro itself: `cwd`. This parameter is set to
the current working directory of the file from which the ``#CALL`` macro is
executed, which may be useful if the method needs to provide a hyperlink to
some other part of the disassembly (as in the case where an image is being
created).

Let's say your sprite-image-creating method will accept two parameters (in
addition to `cwd`): `sprite_id` (the sprite identifier) and  `fname` (the image
filename). The method (let's call it `sprite`) would look something like this::

  from skoolkit.skoolhtml import HtmlWriter

  class GameHtmlWriter(HtmlWriter):
      def sprite(self, cwd, sprite_id, fname):
          img_path = self.image_path(fname)
          if self.need_image(img_path):
              udgs = self.build_sprite(sprite_id)
              self.write_image(img_path, udgs)
          return self.img_element(cwd, img_path)

With this method (and an appropriate implementation of the `build_sprite`
method) in place, it's possible to use a ``#CALL`` macro like this::

  #UDGTABLE
  { #CALL:sprite(3,jumping) }
  { Sprite 3 (jumping) }
  TABLE#

Adding a ``#CALL`` method to the AsmWriter subclass is equally simple. The
timestamp-creating method (let's call it `timestamp`) would look something like
this::

  import time
  from skoolkit.skoolasm import AsmWriter

  class GameAsmWriter(AsmWriter):
      def timestamp(self):
          return time.strftime("%a %d %b %Y %H:%M:%S %Z")

With this method in place, it's possible to use a ``#CALL`` macro like this::

  ; This ASM file was generated on #CALL:timestamp()

Note that if the return value of a ``#CALL`` method contains skool macros, then
they will be expanded.

Skool macros
------------
Another way to add a custom method is to implement it as a skool macro. The
main differences between a skool macro and a ``#CALL`` method are:

* a ``#CALL`` macro's parameters are automatically evaluated and passed to the
  ``#CALL`` method; a skool macro's parameters must be parsed and evaluated
  manually (typically by using one or more of the
  :ref:`macro-parsing utility functions <ext-MacroParsing>`)
* every optional parameter in a skool macro can be assigned a default value if
  omitted; in a ``#CALL`` method, only the optional arguments at the end can be
  assigned default values if omitted, whereas any others are set to `None`
* numeric parameters in a ``#CALL`` macro are automatically converted to
  numbers before being passed to the ``#CALL`` method; no automatic conversion
  is done on the parameters of a skool macro

In summary: a ``#CALL`` method is generally simpler to implement than a skool
macro, but skool macros are more flexible.

Implementing a skool macro is done by adding a method named `expand_macroname`
to the HtmlWriter or AsmWriter subclass in the extension module. So, to
implement a ``#SPRITE`` or ``#TIMESTAMP`` macro, we would add a method named
`expand_sprite` or `expand_timestamp`.

A skool macro method must accept either two or three parameters, depending on
whether it is implemented on a subclass of AsmWriter or HtmlWriter:

* ``text`` -  the text that contains the skool macro
* ``index`` - the index of the character after the last character of the macro
  name (that is, where to start looking for the macro's parameters)
* ``cwd`` - the current working directory of the file from which the macro is
  being executed; this parameter must be supported by skool macro methods on an
  HtmlWriter subclass

A skool macro method must return a 2-tuple of the form ``(end, string)``, where
``end`` is the index of the character after the last character of the macro's
parameter string, and ``string`` is the HTML or text to which the macro will be
expanded. Note that if ``string`` itself contains skool macros, then they will
be expanded.

The `expand_sprite` method on GameHtmlWriter may therefore look something like
this::

  from skoolkit.skoolhtml import HtmlWriter, Frame
  from skoolkit.skoolmacro import parse_image_macro

  class GameHtmlWriter(HtmlWriter):
      # #SPRITEid[{x,y,width,height}](fname)
      def expand_sprite(self, text, index, cwd):
          end, crop_rect, fname, frame, alt, (sprite_id,) = parse_image_macro(text, index, names=['id'])
          udgs = self.build_sprite(sprite_id)
          frames = [Frame(udgs, 2, 0, *crop_rect, name=frame)]
          return end, self.handle_image(frames, fname, cwd, alt)

With this method (and an appropriate implementation of the `build_sprite`
method) in place, the ``#SPRITE`` macro might be used like this::

  #UDGTABLE
  { #SPRITE3(jumping) }
  { Sprite 3 (jumping) }
  TABLE#

The `expand_timestamp` method on GameAsmWriter would look something like this::

  import time
  from skoolkit.skoolasm import AsmWriter

  class GameAsmWriter(AsmWriter):
      def expand_timestamp(self, text, index):
          return index, time.strftime("%a %d %b %Y %H:%M:%S %Z")

.. _ext-MacroParsing:

Parsing skool macros
--------------------
The skoolkit.skoolmacro module provides some utility functions that may be used
to parse the parameters of a skool macro.

.. autofunction:: skoolkit.skoolmacro.parse_ints

   .. versionchanged:: 4.0
      Added the *names* parameter and support for keyword arguments; *index*
      defaults to 0.

   .. versionchanged:: 5.1
      Added support for parameters expressed using arithmetic operators and
      skool macros.

.. autofunction:: skoolkit.skoolmacro.parse_strings

   .. versionadded:: 5.1

.. autofunction:: skoolkit.skoolmacro.parse_brackets

   .. versionadded:: 5.1

.. autofunction:: skoolkit.skoolmacro.parse_image_macro

   .. versionadded:: 5.1

.. note::
   The :func:`parse_params` function in skoolkit.skoolmacro is deprecated since
   version 5.1. Use :func:`~skoolkit.skoolmacro.parse_ints` and
   :func:`~skoolkit.skoolmacro.parse_brackets` instead.

.. note::
   The :meth:`parse_image_params` method on HtmlWriter is deprecated since
   version 5.1. Use :func:`~skoolkit.skoolmacro.parse_image_macro` instead.

Parsing ref files
-----------------
HtmlWriter provides some convenience methods for extracting text and data from
ref files. These methods are described below.

.. automethod:: skoolkit.skoolhtml.HtmlWriter.get_section
.. automethod:: skoolkit.skoolhtml.HtmlWriter.get_sections
.. automethod:: skoolkit.skoolhtml.HtmlWriter.get_dictionary
.. automethod:: skoolkit.skoolhtml.HtmlWriter.get_dictionaries

Memory snapshots
----------------
The `snapshot` attribute on HtmlWriter and AsmWriter is a 65536-element list
that represents the 64K of the Spectrum's memory; it is populated when the
skool file is being parsed.

HtmlWriter also provides some methods for saving and restoring memory
snapshots, which can be useful for temporarily changing graphic data or the
contents of data tables. These methods are described below.

.. automethod:: skoolkit.skoolhtml.HtmlWriter.push_snapshot
.. automethod:: skoolkit.skoolhtml.HtmlWriter.pop_snapshot
.. automethod:: skoolkit.skoolhtml.HtmlWriter.get_snapshot_name

.. _ext-Graphics:

Graphics
--------
If you are going to implement custom image-creating ``#CALL`` methods or skool
macros, you will need to make use of the skoolkit.skoolhtml.Udg class.

The Udg class represents an 8x8 graphic (8 bytes) with a single attribute byte,
and an optional mask.

.. autoclass:: skoolkit.skoolhtml.Udg

A simple ``#INVERSE`` macro that creates an inverse image of a UDG might be
implemented like this::

  from skoolkit.skoolhtml import HtmlWriter, Udg
  from skoolkit.skoolmacro import parse_ints

  class GameHtmlWriter(HtmlWriter):
      # #INVERSEaddress,attr
      def expand_inverse(self, text, index, cwd):
          end, address, attr = parse_ints(text, index, 2)
          img_path = self.image_path('inverse{}_{}'.format(address, attr))
          if self.need_image(img_path):
              udg_data = [b ^ 255 for b in self.snapshot[address:address + 8]]
              udg = Udg(attr, udg_data)
              self.write_image(img_path, [[udg]])
          return end, self.img_element(cwd, img_path)

The Udg class provides two methods for manipulating an 8x8 graphic: `flip` and
`rotate`.

.. automethod:: skoolkit.skoolhtml.Udg.flip
.. automethod:: skoolkit.skoolhtml.Udg.rotate

If you are going to implement ``#CALL`` methods or skool macros that create
animated images, you will need to make use of the skoolkit.skoolhtml.Frame
class.

The Frame class represents a single frame of an animated image.

.. autoclass:: skoolkit.skoolhtml.Frame

   .. versionadded:: 3.6

   .. versionchanged:: 4.0
      The *mask* parameter specifies the type of mask to apply (see
      :ref:`masks`).

   .. versionchanged:: 5.1
      The *udgs* parameter can be a function that returns the array of tiles;
      added the *name* parameter.

HtmlWriter provides the following image-related convenience methods.

.. automethod:: skoolkit.skoolhtml.HtmlWriter.image_path

   .. versionchanged:: 5.1
      Added the *frames* parameter.

.. automethod:: skoolkit.skoolhtml.HtmlWriter.need_image
.. automethod:: skoolkit.skoolhtml.HtmlWriter.write_image

   .. versionchanged:: 4.0
      The *mask* parameter specifies the type of mask to apply (see
      :ref:`masks`).

.. automethod:: skoolkit.skoolhtml.HtmlWriter.img_element
.. automethod:: skoolkit.skoolhtml.HtmlWriter.write_animated_image

   .. versionadded:: 3.6

.. automethod:: skoolkit.skoolhtml.HtmlWriter.handle_image

   .. versionadded:: 5.1

.. automethod:: skoolkit.skoolhtml.HtmlWriter.screenshot
.. automethod:: skoolkit.skoolhtml.HtmlWriter.flip_udgs
.. automethod:: skoolkit.skoolhtml.HtmlWriter.rotate_udgs

HtmlWriter initialisation
-------------------------
If your HtmlWriter subclass needs to perform some initialisation tasks, such as
creating instance variables, or parsing ref file sections, the place to do that
is the `init()` method.

.. automethod:: skoolkit.skoolhtml.HtmlWriter.init

For example::

  from skoolkit.skoolhtml import HtmlWriter

  class GameHtmlWriter(HtmlWriter):
      def init(self):
          # Get character names from the ref file
          self.characters = self.get_dictionary('Characters')