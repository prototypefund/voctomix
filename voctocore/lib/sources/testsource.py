#!/usr/bin/env python3/
import logging

from configparser import NoOptionError
from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource

count = -1

GST_TYPE_VIDEO_TEST_SRC_PATTERN = [
  "smpte",
  "snow",
  "black"
  "white",
  "red",
  "green",
  "blue",
  "checkers-1",
  "checkers-2",
  "checkers-4",
  "checkers-8",
  "circular",
  "blink",
  "smpte75",
  "zone-plate",
  "gamut",
  "chroma-zone-plate",
  "solid",
  "ball",
  "smpte100",
  "bar"
]

class TestSource(AVSource):
    def __init__(self, name, has_audio=True, has_video=True,
                 force_num_streams=None):
        self.log = logging.getLogger('TestSource[{}]'.format(name))
        AVSource.__init__(self, name, has_audio, has_video,
                          force_num_streams)

        section = 'source.{}'.format(name)
        self.pattern = None
        try:
            self.pattern = Config.get(section, 'pattern')
        except NoOptionError:
            global count
            count += 1
            self.pattern = count
            self.log.info("Pattern unspecified, picking pattern '{}'"
                .format(GST_TYPE_VIDEO_TEST_SRC_PATTERN[count]))

        self.build_pipeline("")

    def port(self):
        return "(TEST)"

    def __str__(self):
        return 'TestSource[{name}]'.format(
            name=self.name
        )

    def build_audioport(self, audiostream):
        return """audiotestsrc
        is-live=true"""

    def build_videoport(self):
        return """
    videotestsrc
        pattern={}
        is-live=true""".format(self.pattern)

    def restart(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.launch_pipeline()
