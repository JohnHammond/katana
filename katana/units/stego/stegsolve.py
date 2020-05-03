"""
Reveal color planes on an image with ``stegsolve``.

This unit is a Python implementation of ``stegsolve.jar``, which is often
used for CTF challenges.

You can supply a ``channel`` or ``plane`` index to specifically extract, but
if these arguments are not given the unit will bruteforce and grab the least
4 bits of each color channel (R, G, B, typically).

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is an image file.


"""
from PIL import Image
import traceback
import os

from katana.unit import FileUnit, NotApplicable
from katana.manager import Manager
from katana.target import Target


def get_plane(img, data, channel: str, index: str = 0):
    """ 
    Get a new image showcasing only one channel and index of an image.

    :param img: The Python PIL original image object

    :param data: The pixel data of the original image object

    :param channel: The channel to extract, as a string (e.g. "R", "G", "B")

    :param index: The specific bit index (0-7) you want to extract

    :return: A new Python PIL image with only the given channel and index.
    """
    if channel in img.mode:
        new_image = Image.new("L", img.size)
        new_image_data = new_image.load()

        # JOHN: I pass in the data now, so it is not loaded every time.
        img_data = data

        channel_index = img.mode.index(channel)
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                color = img_data[x, y]

                try:
                    channel = color[channel_index]
                except TypeError:
                    channel = color

                plane = bin(channel)[2:].zfill(8)
                try:
                    new_color = 255 * int(plane[abs(index - 7)])
                    new_image_data[x, y] = 255 * int(plane[abs(index - 7)])
                except IndexError:
                    pass
        return new_image
    else:
        return


class Unit(FileUnit):

    PRIORITY = 70
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a priorty
    of 70.
    """

    RECURSE_SELF = False
    """
    Recurssion would be silly in this case.
    """

    GROUPS = ["stego", "image", "stegsolve"]
    """
    These are "tags" for a unit. Considering it is a Stego unit, "stego"
    is included, as well as the tag "image", and the name of the unit itself,
    "stegsolve".
    """

    BLOCKED_GROUPS = ["stego", "forensics"]
    """
    Blocked groups.... do not recurse into forensics because running
    binwalk or foremost on new images serves no real purpose
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor is included just to provide a keyword for the
        ``FileUnit``, ensuring the provided target is an image file. This
        also validates it can be read and resizes the image if necessary.
        """
        super(Unit, self).__init__(*args, **kwargs, keywords=[" image "])

        try:
            self.img = Image.open(self.target.path)

            resizing = False
            new_size = list(self.img.size)
            if self.img.size[0] > 1000:
                resizing = True
                new_size[0] = 500
            if self.img.size[1] > 1000:
                resizing = True
                new_size[1] = 500
            if resizing:
                self.img = self.img.resize(tuple(new_size), Image.ANTIALIAS)

            self.data = self.img.load()

        # If we don't know what this is, don't bother with it.
        except OSError:
            raise NotApplicable("cannot read file")

        except Exception:
            raise NotApplicable("unknown error occurred")

    def enumerate(self):
        """
        This function will first yield the ``channel`` and ``plane`` that are 
        supplied as arguments by the end-user. If they are not supplied, by
        default it will loop through all colors channels and the least 4 bits 
        to extract from the target. These ``channel`` and ``plane`` pairs 
        will be presented as a tuple, to be used by the ``evaluate`` 
        function.
        """

        channel = self.get("channel", "")
        plane = self.get("plane", "")

        # Default to 4 planes
        max_plane = self.geti("max-plane", 4)

        # Try to decode planes
        try:
            planes = [int(x) for x in plane.split(",")]
        except (ValueError, AttributeError):
            # By default select up to max-plane planes
            planes = range(max_plane)

        # Try to decode channels
        channels = channel.upper()
        channels = "".join([c for c in channels if c in "RGBA"])

        # By default, select all channels
        if len(channels) == 0:
            channels = "RGBA"

        # Yield all plane options
        for plane in planes:
            for channel in channels:
                yield (channel, plane)

    def evaluate(self, case):
        """
        Evaluate the target. Create new images on specific color channels
        and their specified bit indexes.

        :param case: A case returned by ``enumerate``. For this unit, this \
        will be a tuple with the channel (R, G, B) and plane (0-7) to extract.

        :return: None. This function should not return any data.
        """

        # Grab the current case
        channel, plane = case

        # Carve out the needed plane
        image = get_plane(self.img, self.data, channel, plane)

        if image:
            # Create the artifact
            output_path, _ = self.generate_artifact(
                f"channel_{channel}_plane_{plane}.png", create=True
            )
            image.save(output_path)

            # Register the artifact with the manager
            self.manager.register_artifact(self, output_path)
