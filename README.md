# RVlyzer: the trivial RISC-V static analyzer
<b>The code contained here is still in a pre-release state, with its quirks, obscurities and dubious design choices. If
you like clean code and ease of use, come back in a couple of weeks...</b>

## Introduction
### What is this?
RVlyzer is a Python 3 library for the representation, low-level manipulation and minimal static analysis of a somewhat
limited subset of RISC-V assembly code. It was born out of need for a larger project involving code transformation, but
contained so much boilerplate code that I thought it needed its own little spot.

Despite its many shortcomings, RVlyzer manages to equip the user with a more-or-less convenient way of dealing with code
in a pythonic way, and its CFG-generating machinery can deal with all those programs that do not need runtime jump
address calculation (maybe one day I will be exploring the magic of SMT solvers and symbolic execution...).

### What can it do?
For now, it can help you to:
- structure statements into proper objects;
- store R-V code inside objects exposing the `MutableSequence` API;
- extract basic blocks and CFGs for (nearly) arbitrary pieces of code;
- map execution flows onto graphs;
- conduct an approximate analysis of register hotness w.r.t. writes.

All graphs are [NetworkX](https://networkx.github.io) graphs, enabling you to apply all of their graph-algorithms
library goodness to a static code analysis context. And visualization, of course.

### Why so RISC-V-specific?
We tested it only on R-V assembly, but sure it can be used with other architectures that follow the same format. Just
don't expect the immediate operands' size constants to be the right ones. That part will be heavily refactored in a
short time anyways, so don't pay too much attention to it.

## Usage
A proper Python package is on its way (cleansing needed first), but for now you can just clone this in the right place
and tell the interpreter where to look for it.

There's no proper way of loading code into this thing. Actually, nearly nothing in here supports the automated parsing
of ASM files. Apart from directly calling constructors, the only alternative is to use the
`rvlyzer.rep.fragments.load_src_from_maps()`, which accepts a list of dictionaries describing statements and routes them
to the appropriate constructors, based on a dictionary record keyed as `role`.

As I said, this code was part of a larger project which has its own 
[funky parser](https://github.com/zoythum/RISC-V-Parser). As soon as I have due time on hand, I am planning to
re-implement that thing and incorporate it in here. It will be easier for all of us, I assure you...

Anyway, the code itself comes with rich docstrings, so all of the details are dealt with there.

### The `base` and `fragments` modules
These two modules deal with the representation of statements and code in a structured, object-oriented way.

Muster your code in there and manipulate it via the familiar "list" interface, supporting single and bulk operations
through indexed access and slices.

### The `graphs` module
This module is able to extrapolate basic blocks and CFGs from code fragments. It does so by reasoning over labels and
jump instructions, so it is pretty naive; nonetheless, it works well with assembly output by an orthodox compiler.

In addition, a fairly basic function that simulates multiple execution paths is provided.

The main limitation of this module is in its reliance over proper code layout. Each basic block is expected to be
delimited by jumps or labels, so control transfers based on literal immediate operands just pass over its head.

Moreover, code in this module works on the assumption that the only jumps that load their addresses from the register
file are procedure returns. Check your code beforehand to see if it contains other uses for these instructions.

### The `heatmaps` module
Where functions dealing with drawing register heat-maps are contained.

A register heat-map is a structures that represents how much time has passed since the last time a certain register has
been written to. Functions contained in this module are able to draw maps of basic blocks or entire execution flows in a
more or less accurate manner.

The only big approximation performed during mapping is related to loops. A practical way of solving this issue without
foraying into higher dimensions hasn't come to my mind, yet.

## Improving this codebase
### (Near) future developments
In the coming days, I am going to transfer more code from the original project's repo. Meanwhile, I'll try to refactor
new and old code, put everything in better shape and try to add some intelligence to the tooling.

After that, if I have to put things into a list:
- properly generate documentation (no one likes reading raw docstrings);
- set up a package;
- try to develop an embedded parser;
- add data-flow tracking to the mix;
- implement a more intelligent CFG extractor;
- let's see how hard symbolic execution can get.

### Contributing (I seriously am in need of help)
As you may have guessed, I am not a professional who writes parsers and code analysis tools, nor I am someone who had to
deal with reverse engineering in the past. I ended up in this spot for purely academic reasons.

Whether you think this library may be of some use to you, or you see an unforgivable mistake that just can't be let to
exists in the open air, feel free to drop me a pull request. I'll integrate it as soon as possible.

## Contributors to the original project
Thanks to:
- [Alessandro Nazzari](https://github.com/zoythum) for relying on this code, helping me test it and providing some
  catalogues;
- [Mattia Iamundo](https://github.com/MattiaIamundo) for the same reasons, plus some pretty-printing code he added.

None of us ever thought that taking up that project would have put such strain on us, neither did the one who proposed
it in the first place, it seems.

At least, we learned something new.
