import pyaudio
import struct
import math
from subprocess import call
import argparse

parser = argparse.ArgumentParser(description='scrobbles rdio to facebook when you start tapping along; turns off after you stop for a while')
parser.add_argument('authkey', help='auth key needed for rdio. see https://github.com/compsocial/rdio-tap-scrobble for setup instructions.')
parser.add_argument('rcookie', help='cookie needed for rdio. see https://github.com/compsocial/rdio-tap-scrobble for setup instructions.')
parser.add_argument('--tapthresh', metavar='float', type=float, dest='tapthresh', default=0.005, help='turn this up for a noisier room. 0.005 is default.')
parser.add_argument('--offafter', metavar='min', type=int, dest='offafter', default=20, help='after this many minutes of no tapping, turn scrobbling back off.')

args = parser.parse_args()
authkey = args.authkey
rcookie = args.rcookie

INITIAL_TAP_THRESHOLD = args.tapthresh # originally 0.01
FORMAT = pyaudio.paInt16
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 2
RATE = 44100
INPUT_BLOCK_TIME = 0.02
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
MAX_TAP_BLOCKS = 0.15/INPUT_BLOCK_TIME
BLOCK_LISTEN_TIME = 1000
MIN_TIME_TAP_THRESHOLD = 5
STRING_TAP_THRESHOLD = 6 # how wide the cluster has to be
TIME_TAP_THRESHOLD = 10
DISINTERESTED_THRESHOLD = 3*args.offafter

def get_rms( block ):
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )

    sum_squares = 0.0
    for sample in shorts:
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n

    return math.sqrt( sum_squares / count )

class Tap(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.tap_threshold = INITIAL_TAP_THRESHOLD
        self.noisycount = MAX_TAP_BLOCKS+1
        self.quietcount = 0
        self.errorcount = 0
        self.quietrun = 0
        self.quietruns = []

    def reset(self):
        self.noisycount = MAX_TAP_BLOCKS+1
        self.quietcount = 0
        self.errorcount = 0
        self.quietrun = 0
        self.quietruns = []

    def stop(self):
        self.stream.close()

    def find_input_device(self):
        device_index = None
        for i in range( self.pa.get_device_count() ):
            devinfo = self.pa.get_device_info_by_index(i)
            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    device_index = i
                    return device_index
        return device_index

    def open_mic_stream( self ):
        device_index = self.find_input_device()

        stream = self.pa.open(format = FORMAT,
                              channels = CHANNELS,
                              rate = RATE,
                              input = True,
                              input_device_index = device_index,
                              frames_per_buffer = INPUT_FRAMES_PER_BLOCK)
        return stream

    def listen(self):
        try:
            block = self.stream.read(INPUT_FRAMES_PER_BLOCK)
        except IOError, e:
            self.errorcount += 1
            # print( "(%d) Error recording: %s"%(self.errorcount,e) )
            self.noisycount = 1
            return

        amplitude = get_rms(block)
        if amplitude > self.tap_threshold:
            # noisy block
            self.quietcount = 0
            self.noisycount += 1
            self.quietrun += 1
        else:
            # quiet block.
            if 1 <= self.noisycount <= MAX_TAP_BLOCKS:
                # print self.quietrun
                self.quietruns.append(self.quietrun)
                self.quietrun = 0
            else:
                self.quietrun += 1
            self.noisycount = 0
            self.quietcount += 1

    def interQuietTimes(self): return self.quietruns

if __name__ == "__main__":
    tap = Tap()
    nottappings = 0
    scrobbling = False

    while True: 
        # listen for a while; default is 20 sec
        for i in range(BLOCK_LISTEN_TIME):
            tap.listen()

        q = tap.interQuietTimes()
        q.sort()
        q = [z for z in q if z > MIN_TIME_TAP_THRESHOLD]

        # am i tapping?
        istap = False
        lq = len(q)
        if lq >= STRING_TAP_THRESHOLD:
            for i in range(lq):
                if i < lq-STRING_TAP_THRESHOLD:
                    if q[i+STRING_TAP_THRESHOLD]-q[i] < TIME_TAP_THRESHOLD:
                        istap = True

        if istap:
            # print "found you tapping"
            nottappings = 0
            if not scrobbling:
                cmd = "curl -d 'prefs=%7B%22fbScrobble%22%3Atrue%7D&extras=*.WEB&method=savePref&_authorization_key="+authkey+"&v=20121006' --cookie 'r="+rcookie+"' -H 'Content-Type: application/x-www-form-urlencoded' http://www.rdio.com/api/1/savePref"
                call(cmd, shell=True)
                scrobbling = True
        else:
            # print "didn't find you tapping"
            nottappings += 1
            if scrobbling and nottappings > DISINTERESTED_THRESHOLD:
                cmd = "curl -d 'prefs=%7B%22fbScrobble%22%3Afalse%7D&extras=*.WEB&method=savePref&_authorization_key="+authkey+"&v=20121006' --cookie 'r="+rcookie+"' -H 'Content-Type: application/x-www-form-urlencoded' http://www.rdio.com/api/1/savePref"
                call(cmd, shell=True)
                scrobbling = False

        tap.reset()
