import wave

import pylab
from katana import units
from katana.units import NotApplicable
from katana.units.ocr.tesseract import attempt_ocr
from pwn import *
from pydub import AudioSegment


def get_info(wav_file):
    if not isinstance(wav_file, bytes):
        wav_file = wav_file.encode('utf-8')
    if wav_file.split(b".")[-1] == b"mp3":
        sound = AudioSegment.from_mp3(wav_file.decode('utf-8'))
        frames = sound._data
        frame_rate = sound.frame_rate

    else:
        wav = wave.open(wav_file.decode('utf-8'), 'r')
        frames = wav.readframes(-1)
        frame_rate = wav.getframerate()
        wav.close()

    sound_info = pylab.fromstring(frames, 'int16')
    return sound_info, frame_rate


class Unit(units.FileUnit):
    PRIORITY = 30

    def __init__(self, katana, target, keywords=None):
        super(Unit, self).__init__(katana, target, keywords=["audio"])

        self.completed = True
        if keywords is None:
            keywords = []
        print("did we get here?")
        if target.is_url:
            raise NotApplicable('target is a URL')

    def evaluate(self, katana, case):

        start_path = katana.get_artifact_path(self)
        linear_path, _ = katana.create_artifact(self, f"spectrogram_linear.png", create=False)
        dB_path, _ = katana.create_artifact(self, f"spectrogram_dB.png", create=False)

        pylab.style.use(['seaborn-dark'])
        pylab.tight_layout()
        sound_info, frame_rate = get_info(self.target.path)
        pylab.figure(num=None, figsize=(18, 10), frameon=False)
        pylab.specgram(x=sound_info, Fs=2, NFFT=1024, mode='magnitude', scale='linear', sides='onesided')

        pylab.gca().axes.get_yaxis().set_visible(False)
        pylab.gca().axes.get_xaxis().set_visible(False)

        pylab.savefig(linear_path, pad_inches=0, bbox_inches="tight", bbox_extra_artists=[])
        pylab.specgram(x=sound_info, Fs=2, NFFT=1024, mode='magnitude', scale='dB', sides='onesided')
        pylab.savefig(dB_path, pad_inches=0, bbox_inches="tight", bbox_extra_artists=[])

        katana.add_image(dB_path)
        katana.add_image(linear_path)

        ocr_text = attempt_ocr(os.path.abspath(dB_path))
        if ocr_text:
            if katana.locate_flags(self, ocr_text.replace('\n', '')):
                # If we do find a flag, stop this unit!!
                self.completed = True

        ocr_text = attempt_ocr(os.path.abspath(linear_path))
        if ocr_text:
            if katana.locate_flags(self, ocr_text.replace('\n', '')):
                # If we do find a flag, stop this unit!!
                pass
