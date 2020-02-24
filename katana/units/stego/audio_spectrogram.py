"""
Create an audio spectrogram for audio files

This unit will generate a spectrogram for audio files. It relies heavily
on Python libraries such as ``pydub`` and ``pylab``.

This unit inherits from the :class:`katana.unit.FileUnit` to ensure
that the target is in fact an audio file.
"""


from pydub import AudioSegment
import pylab
import wave

from katana.unit import FileUnit, NotApplicable
from katana.manager import Manager
from katana.target import Target


def get_info(wav_file: bytes) -> tuple:
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

    PRIORITY = 30
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a higher
    than normal priority for matching files
    """

    GROUPS = ["audio", "stego"]
    """
    These are "tags" for a unit. Considering it is a Stego unit, "stego"
    is included, as well as the tag "audio".
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is an audio file. This
        also validates it is not a URL to a website.
        """

        super(Unit, self).__init__(*args, **kwargs, keywords=["audio"])

        # if this is a URL, and we can reach it, don't try to mangle anything
        if self.target.is_url and not self.target.url_accessible:
            raise NotApplicable("this is a URL")

    def evaluate(self, case):
        """
        Evaluate the target. Create an audio spectrogram based off of the
        given audio file and add it to the results.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.
        """

        # Generate the artifact's (no creation, effectively grab the path)
        linear_path, _ = self.generate_artifact("spectrogram_linear.png", create=False)
        dB_path, _ = self.generate_artifact("spectrogram_dB.png", create=False)

        # Prettify the audio spectrogram output.
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

        # Do not display axes in the spectrogram image file.
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
