This little script starts scrobbling Rdio tracks to Facebook when you begin tapping along. After you stop tapping for awhile (default: 20 min), it turns scrobbling back off. ("Along" is a bit of stretch, since it only really looks for tapping and doesn't check that it's happening at the same beat as the current song. Future work. Well, not really.) It has been tested only on a MacBook Air, but I suspect will work out of the box on other \*nixes.

**note: this guy uses an undocumented Rdio api endpoint discovered
through traffic inspection. uayor + ymmv.**

## Installation

1. Install [PyAudio](http://people.csail.mit.edu/hubert/pyaudio).

2. Find and record two of your Rdio keys. Instructions using Chrome:

Visit your [Rdio external settings page](http://www.rdio.com/settings/external). Right-click somewhere on the page and select "Inspect Element". Click on the "Network" tab. Now click the checkbox labeled "Share the songs you play on Facebook." It should have initiated a call back to Rdio, named "savePref" in the Network box. Click it. You need two values for this script to work, a cookie called 'r' and a form param called '_authorization_key'. The screenshot below should help you locate and record them.

![grabbing keys from rdio](http://i.imgur.com/Ivzeb.png)

## Running

Place rdio.scrobble.py somewhere on your machine, pass it the values you just recorded,
and if you like,  set it to run in the background.

```
python rdio.scrobble.py authkey rcookie &
```

I use it by tapping with my fingernail off the right-hand side of my Air's
keyboard.

## Options

Turn up the tap threshold for a noisier room. The default threshold is
0.005, but you can try other values:

```
python rdio.scrobble.py authkey rcookie --tapthresh 0.01 &
```

Also, you can tell it to turn scrobbling back off after a certain number
of minutes (default: 20 min):

```
python rdio.scrobble.py authkey rcookie --offafter 60 &
```

## Limitations

This script shells out to curl to make the calls to Rdio. I tried
getting the [requests library](http://docs.python-requests.org/en/v1.0.0) to work, but it didn't. And I'm not sure why. It could be as simple as the user-agent string or something more
subtle. If somebody figures this out, please let me know. This
restriction makes me think it won't work out of the box on Windows, but
hey who knows.

## Credits

I leaned **very heavily** on [this Stack Overflow post](http://stackoverflow.com/questions/4160175/detect-tap-with-pyaudio-from-live-mic) to write the tapping detector. Good stuff. Thanks!

## Contributing
Pull requests welcome. Send me bug reports, but I probably will not
actually get to them. ;-)
