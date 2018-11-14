import logging
import os

from gi.repository import Gtk, GdkPixbuf
import lib.connection as Connection

from lib.config import Config
from lib.toolbar.helpers import mark_label, unmark_label, icon_path


class StreamblankToolbarController(object):
    """Manages Accelerators and Clicks on the Composition Toolbar-Buttons"""

    def __init__(self, toolbar, win, uibuilder, warning_overlay):
        self.log = logging.getLogger('StreamblankToolbarController')

        self.warning_overlay = warning_overlay

        accelerators = Gtk.AccelGroup()
        win.add_accel_group(accelerators)

        livebtn = uibuilder.find_widget_recursive(toolbar, 'stream_live')
        blankbtn = uibuilder.find_widget_recursive(toolbar, 'stream_blank')

        blankbtn_pos = toolbar.get_item_index(blankbtn)

        if not Config.getboolean('stream-blanker', 'enabled'):
            self.log.info('disabling stream-blanker features '
                          'because the server does not support them: %s',
                          Config.getboolean('stream-blanker', 'enabled'))

            toolbar.remove(livebtn)
            toolbar.remove(blankbtn)
            return

        blank_sources = Config.getlist('stream-blanker', 'sources')

        self.current_status = None

        key, mod = Gtk.accelerator_parse('F12')
        livebtn.connect('toggled', self.on_btn_toggled)
        livebtn.set_name('live')
        livebtn.set_can_focus(False)
        livebtn.set_label("F12")
        livebtn.set_tooltip_text("Go live")
        livebtn.get_child().add_accelerator('clicked', accelerators,
                                            key, mod, Gtk.AccelFlags.VISIBLE)
        self.livebtn = livebtn
        self.blank_btns = {}

        accel_f_key = 11

        for idx, name in enumerate(blank_sources):
            key, mod = Gtk.accelerator_parse('F%u' % accel_f_key)

            if idx == 0:
                new_btn = blankbtn
            else:
                new_icon = Gtk.Image.new_from_pixbuf(blankbtn.get_icon_widget()
                                                     .get_pixbuf())
                new_btn = Gtk.RadioToolButton(group=livebtn)
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(os.path.join(icon_path(),
                                                        "nostream.svg"))
                image = Gtk.Image()
                image.set_from_pixbuf(pixbuf)
                new_btn.set_icon_widget(image)
                toolbar.insert(new_btn, blankbtn_pos)

            new_btn.set_name(name)
            new_btn.set_can_focus(False)
            new_btn.set_label("F%s" % accel_f_key)
            new_btn.connect('toggled', self.on_btn_toggled)
            new_btn.set_tooltip_text("Stop streaming by %s" % name)

            new_btn.get_child().add_accelerator(
                'clicked', accelerators,
                key, mod, Gtk.AccelFlags.VISIBLE)

            self.blank_btns[name] = new_btn
            accel_f_key = accel_f_key - 1

        # connect event-handler and request initial state
        Connection.on('stream_status', self.on_stream_status)
        Connection.send('get_stream_status')

    def on_btn_toggled(self, btn):
        if btn.get_active():
            mark_label(btn)
            btn_name = btn.get_name()
            if btn_name == 'live':
                self.warning_overlay.disable()
            else:
                self.warning_overlay.enable(btn_name)

            if self.current_status == btn_name:
                self.log.info('stream-status already activate: %s', btn_name)
                return

            self.log.info('stream-status activated: %s', btn_name)
            if btn_name == 'live':
                Connection.send('set_stream_live')
            else:
                Connection.send('set_stream_blank', btn_name)
        else:
            unmark_label(btn)


    def on_stream_status(self, status, source=None):
        self.log.info('on_stream_status callback w/ status %s and source %s',
                      status, source)

        self.current_status = source if source is not None else status
        if status == 'live':
            btn = self.livebtn
            self.warning_overlay.disable()
        else:
            btn = self.blank_btns[source]
            self.warning_overlay.enable(btn.get_name())
        if not btn.get_active():
            btn.set_active(True)
