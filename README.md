# Brink
> **How long can you survive at the brink of death?**

<p style="text-align: center;">
  ![Brink](https://static.jam.vg/content/1ad/e1/z/1bada.png.320x256.fit.jpg)
</p>

* [Ludum Dare](https://ldjam.com/events/ludum-dare/43/$126370)
* [Itch.io](https://bottersnike.itch.io/brink)

## Installation
### Windows

Download the packaged `zip` from the itch.io page, extract it, and run
`Brink.exe`. There are a bunch of hidden files and folders included in
that zip, so be careful when moving the exe file around.

### Linux

`git clone` this repository or download the zip from the button above.
From there, make sure to be using python3 then
`pip install -r requirements.txt` to grab the extra things we need that
aren't included in the base python install. You need Tkinter to use the
startup dialogue, so you might need to install `python3-tkinter` or
similar if for some reason you don't already have it.

There is no formal installer of the likes for either platform because
at the moment this is just a game for a game jam and that seems
somewhat overkill. Also time constraints.

## System Requirements

To try and squeeze as much performance out of pygame as I could almost
all visible areas are rendered to RAM once. This means we suck up about
300 MB of that, so have that handy. Other than that, you should be fine
on pretty much anything, even this N-series pentium I'm writing this
on.

|              |                                                |
|:------------:|------------------------------------------------|
|      RAM     | ~300 MB                                        |
|      CPU     | Pretty much anything made in the last 10 years |
| Disk Storage | ~17 MB                                         |
