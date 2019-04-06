# REND &mdash; minimalistic static site generator

Everything one needs in the single file with ~ 175 lines of Python code.

## Filling in rend.conf

The only thing you need to build static website is configuration file called `rend.conf`.

Example:
```
# First of all, Python-style comments are allowed

# You need to describe how to generate each page.
# To generate each page REND uses a single Jinja2 template and a single YAML file.
# Works like this: Jinja2 + YAML ---> HTML file ~~~> URL slug
# Each page description consists of 3 or 4 following lines:
# 1) Jinja2 template to use.
# 2) YAML file to use.
# 3) Output HTML file name.
# 4) Optional slug for the page (used by test server).
# Descriptions are separated by empty line.

# E.g.
example/helloworld.j2
example/helloworld.yaml
index.html


# You can also copy assets to build folder.
# Copy section starts by "->" marker, and has a list of all files (or regular expressions) to copy.
->
example/*.jpg
```

## Generating static website

Just run:
```
$ python rend.py
```

And the website is built! All the files will be put into `www` subfolder. 

## Running test server

Just run:
```
$ python rend.py --serve
```

Then open `localhost:9000` in your browser and enjoy your website running.

