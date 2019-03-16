AntiFormat
==========

This project started as a bunch of patches to [lice project](https://github.com/licenses/lice) which provide with an ability not only to generate files with license headers but also replace and update them in already existed files.
But when I realised that probability of these patches to be applied to lice was rapidly decreasing because I had blurred boundaries of lice I decided to form these patches as a different project.


Overview
--------

In contrast to lice AntiFormat requires the configuration file `.antiformat` for your repository as the file which is placed in this repository:

    variables:
      author: "Artem Yamshanov, me [at] anticode.ninja"
      years: "2019" # set of variables which will be used later
    global: # global configuration which will be inherited by all files configuration
      rstrip: True # remove trailing white-spaces
      header: | # configure common header for all files
          {mpl2_header}
          Copyright {years} {author}
    files:
      "*.py": {} # inherit all parameters from global section for all '*.py' files
    ignore:
    - "tests/*" # exclude 'tests' directory

After this you can run `antiformat` from time to time to bring all your source files to the one consistent appearance.

But there is a fly in the ointment: a set of supported file formats (syntaxes) is predefined licenses are very reduced for now, so I will appreciate feedback in a form of issues with requests of a new format or ready-to-apply PR.


Installation
------------

The project is in proof-of-concept stage, so right now the most preferable way to install AntiFormat is:

    git clone git@github.com:anticodeninja/antiformat.git
    cd antiformat
    pip install -e .
