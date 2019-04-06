# REND &mdash; minimalistic static site generator

Everything one needs in the single file with ~ 175 lines of Python code.

## Filling in rend.conf

The only thing you need to build static website is configuration file called `rend.conf`.

Example:
```
example/helloworld.j2
exanple/helloworld.yaml
index.html

->
example/pretty_kitty.jpg
example/ugly_doggy.jpg
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

