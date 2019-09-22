# REND &mdash; minimalistic static site generator

Everything one needs in the single file with ~ 155 lines of Python code.

## How to start?

Fork this repo, add HTML, images, CSS, JavaScript files to it, fill rend.conf, test how everything's working 
commit, push, clone repo on remote server and generate website. Done.

## Filling in rend.conf

The only thing you need to build static website is configuration file called `rend.conf`

Example:
```
# First of all, good news: Python-style comments are allowed!

# This configuration file (always should be called rend.conf) describes two things:
# a) What pages to generate and how
# b) What assets to copy and where

# Page description consists of 4-5 lines, starts with @@ marker and ends with empty line.
# Simple formula: Jinja2 + YAML = HTML
#
# @@
# Jinja2 template file relative path
# YAML file relative path (optional)
# Output HTML filename
#
# Example:
@@
example/helloworld.j2
example/helloworld.yaml
index.html

# You can also copy assets to build folder, starts with >> marker and ends with empty line.
#
# Example:
>>
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
$ python rend.py serve
```

Then open `localhost:9000` in your browser and enjoy your website running.

