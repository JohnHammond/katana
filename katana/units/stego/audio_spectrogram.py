#!/usr/bin/env python3
from pydub import AudioSegment
import pylab
import wave

from katana.unit import FileUnit, NotApplicable
from katana.manager import Manager
from katana.target import Target


def get_info(wav_file: bytes):
    """ Get audiodata from the given the file path """

    # Ensure this is actually bytes
    if not isinstance(wav_file, bytes):
        wav_file = wav_file.encode("utf-8")

    if wav_file.split(b".")[-1] == b"mp3":
        # This is an MP3 file not a wave file
        sound = AudioSegment.from_mp3(wav_file.decode("utf-8"))
        frames = sound._data
        frame_rate = sound.frame_rate
    else:
        # Open the wave file
        wav = wave.open(wav_file.decode("utf-8"), "r")
        frames = wav.readframes(-1)
        frame_rate = wav.getframerate()
        wav.close()

    sound_info = pylab.fromstring(frames, "int16")
    return sound_info, frame_rate


class Unit(FileUnit):
    """ Analyze the audio spectogram of a clip and look for visual text/images """

    # Higher than normal priority for matching files
    PRIORITY = 30
    # Groups we belong to
    GROUPS = ["audio", "stego"]

    def __init__(self, manager: Manager, target: Target):
        super(Unit, self).__init__(manager, target, keywords=["audio"])

        # CALEB: But what if it was a URL to an audio file? :?
        if target.is_url:
            raise NotApplicable("target is a URL")

    def evaluate(self, case):

        # Generate the artifact's (no creation, effectively grab the path)
        linear_path, _ = self.generate_artifact("spectrogram_linear.png", create=False)
        dB_path, _ = self.generate_artifact("spectrogram_dB.png", create=False)

        # CALEB: John wrote this, and I don't know how to comment it...
        pylab.style.use(["seaborn-dark"])
        pylab.tight_layout()
        sound_info, frame_rate = get_info(self.target.path)
        pylab.figure(num=None, figsize=(18, 10), frameon=False)
        pylab.specgram(
            x=sound_info,
            Fs=2,
            NFFT=1024,
            mode="magnitude",
            scale="linear",
            sides="onesided",
        )

        pylab.gca().axes.get_yaxis().set_visible(False)
        pylab.gca().axes.get_xaxis().set_visible(False)

        pylab.savefig(
            linear_path, pad_inches=0, bbox_inches="tight", bbox_extra_artists=[]
        )
        pylab.specgram(
            x=sound_info,
            Fs=2,
            NFFT=1024,
            mode="magnitude",
            scale="dB",
            sides="onesided",
        )
        pylab.savefig(dB_path, pad_inches=0, bbox_inches="tight", bbox_extra_artists=[])

        # Register the figures with the manager
        self.manager.register_artifact(self, linear_path)
        self.manager.register_artifact(self, dB_path)

        # CALEB: This should already happen when Katana recurses on the above artifacts


#         ocr_text = attempt_ocr(os.path.abspath(dB_path))
#         if ocr_text:
#             if katana.locate_flags(self, ocr_text.replace('\n', '')):
#                 # If we do find a flag, stop this unit!!
#                 self.completed = True
#
#         ocr_text = attempt_ocr(os.path.abspath(linear_path))
#         if ocr_text:
#             if katana.locate_flags(self, ocr_text.replace('\n', '')):
#                 # If we do find a flag, stop this unit!!
#                 pass
