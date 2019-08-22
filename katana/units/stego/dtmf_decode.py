import math
import struct
import traceback
import wave

from katana import units
from katana.units import NotApplicable


class DTMFdetector(object):

    def __init__(self):

        self.sample_index = 0
        self.sample_count = 0
        self.q1 = [0, 0, 0, 0, 0, 0, 0, 0]
        self.q2 = [0, 0, 0, 0, 0, 0, 0, 0]
        self.r = [0, 0, 0, 0, 0, 0, 0, 0]
        self.characters = []
        self.charStr = ""
        self.charStr = ""
        self.sample_count = 0
        self.MAX_BINS = 8
        self.GOERTZEL_N = 92
        self.SAMPLING_RATE = 8000
        self.freqs = [697, 770, 852, 941, 1209, 1336, 1477, 1633]
        self.coefs = [0, 0, 0, 0, 0, 0, 0, 0]

        self.reset()

        self.calc_coeffs()

    def reset(self):
        pass

    def post_testing(self):
        row = 0
        col = 0
        see_digit = 0
        peak_count = 0
        max_index = 0
        maxval = 0.0
        t = 0
        i = 0
        msg = "none"

        row_col_ascii_codes = [["1", "2", "3", "A"], ["4", "5", "6", "B"], ["7", "8", "9", "C"], ["*", "0", "#", "D"]]

        for i in range(4):
            if self.r[i] > maxval:
                maxval = self.r[i]
                row = i

        col = 4
        maxval = 0
        for i in range(4, 8):
            if self.r[i] > maxval:
                maxval = self.r[i]
                col = i

        if self.r[row] < 4.0e5:
            msg = "energy not enough"
        elif self.r[col] < 4.0e5:
            msg = "energy not enough"
        else:
            see_digit = True

            if self.r[col] > self.r[row]:
                max_index = col
                if self.r[row] < (self.r[col] * 0.398):
                    see_digit = False

            else:
                max_index = row
                if self.r[col] < (self.r[row] * 0.158):
                    see_digit = False

            if self.r[max_index] > 1.0e9:
                t = self.r[max_index] * 0.158
            else:
                t = self.r[max_index] * 0.010

            peak_count = 0

            for i in range(8):
                if self.r[i] > t:
                    peak_count += 1
            if peak_count > 2:
                see_digit = False

            if see_digit:
                self.characters.append(
                    (row_col_ascii_codes[row][col - 4], float(self.sample_index) / float(self.SAMPLING_RATE)))

    def clean_up_processing(self):
        MIN_CONSECUTIVE = 2
        MAX_GAP = 0.0500

        currentCount = 0
        lastChar = ""
        lastTime = 0
        charIndex = -1

        for i in self.characters:

            charIndex += 1
            currentChar = i[0]
            currentTime = i[1]
            timeDelta = currentTime - lastTime

            if lastChar == currentChar:
                currentCount += 1
            else:

                if len(self.characters) > (charIndex + 2):
                    if (self.characters[charIndex + 1][0] == lastChar) and (
                            self.characters[charIndex + 2][0] == lastChar):
                        # forget this every happened
                        lastTime = currentTime
                        continue

                if currentCount >= MIN_CONSECUTIVE:
                    self.charStr += lastChar
                    currentCount = 1
                    lastChar = currentChar
                    lastTime = currentTime
                    continue

            if timeDelta > MAX_GAP:
                # so de we have enough counts for this to be valid?
                if (currentCount - 1) >= MIN_CONSECUTIVE:
                    self.charStr += lastChar
                currentCount = 1

            lastChar = currentChar
            lastTime = currentTime

        if currentCount >= MIN_CONSECUTIVE:
            self.charStr += lastChar

    def goertzel(self, sample):
        q0 = 0
        i = 0

        self.sample_count += 1
        self.sample_index += 1

        for i in range(self.MAX_BINS):
            q0 = self.coefs[i] * self.q1[i] - self.q2[i] + sample
            self.q2[i] = self.q1[i]
            self.q1[i] = q0

        if self.sample_count == self.GOERTZEL_N:
            for i in range(self.MAX_BINS):
                self.r[i] = (self.q1[i] * self.q1[i]) + (self.q2[i] * self.q2[i]) - (
                        self.coefs[i] * self.q1[i] * self.q2[i])
                self.q1[i] = 0
                self.q2[i] = 0
            self.post_testing()

    def calc_coeffs(self):
        for n in range(self.MAX_BINS):
            self.coefs[n] = 2.0 * math.cos(2.0 * math.pi * self.freqs[n] / self.SAMPLING_RATE)

    def check(self, filename):

        given = wave.open(filename)
        struct.unpack("h", given.readframes(1))
        given.close()

    def getDTMFfromWAV(self, filename):

        self.reset()  # reset the current state of the detector

        given = wave.open(filename)
        totalFrames = given.getnframes()
        count = 0

        while totalFrames != count:
            raw = given.readframes(1)
            (sample,) = struct.unpack("h", raw)
            self.goertzel(sample)
            count += 1

        given.close()

        self.clean_up_processing()
        return self.charStr


class Unit(units.FileUnit):
    PRIORITY = 30

    def __init__(self, katana, target, keywords=None):
        super(Unit, self).__init__(katana, target, keywords=["audio"])

        if keywords is None:
            keywords = []
        if target.is_url:
            raise NotApplicable('target is a URL')

        self.detector = DTMFdetector()
        try:
            if isinstance(self.target.path, bytes):
                self.detector.check(self.target.path.decode('utf-8'))
            else:
                self.detector.check(self.target.path)
        except wave.Error:
            raise NotApplicable("no RIFF id... not a .wav? mp3 not yet supported..")
        except:
            traceback.print_exc()
            raise NotApplicable("failure reading dtmf tones")

    def evaluate(self, katana, case):

        results = self.detector.getDTMFfromWAV(self.target.path.decode('utf-8'))

        katana.add_results(self, results)
        katana.recurse(self, results)
