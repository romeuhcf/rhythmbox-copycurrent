#!/usr/bin/python
# coding: UTF-8
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

from gi.repository import GObject, RB, Peas, GLib, Gdk, Notify
from Xlib import display, X, error
from urllib.parse import urlparse
import os
import Xlib
import urllib.request, urllib.parse, urllib.error
from shutil import  copyfile

Gdk.threads_init()

class CopyCurrentPlugin(GObject.Object, Peas.Activatable):
  __gtype_name__ = 'CopyCurrentPlugin'
  object = GObject.property(type=GObject.Object)

  CtrlModifier = Xlib.X.ControlMask
  ShiftModifier = Xlib.X.ShiftMask
  CapsLockModifier = Xlib.X.LockMask
  NumLockModifier = Xlib.X.Mod2Mask

  __BAD_ACCESS = error.CatchError(error.BadAccess)

  # Ctrl+Shift+'Insert'
  insert_key = 118

  modifier_combinations = (
    CtrlModifier | ShiftModifier,
    CtrlModifier | ShiftModifier | NumLockModifier,
    CtrlModifier | ShiftModifier | CapsLockModifier,
    CtrlModifier | ShiftModifier | NumLockModifier | CapsLockModifier)

  display = None
  root = None

  def __init__(self):
    '''
    init plugin
    '''
    super(CopyCurrentPlugin, self).__init__()

  def do_activate(self):
    '''
    register hotkey, tell X that we want keyrelease events and start
    listening
    '''
    self.display = Xlib.display.Display()
    self.root = self.display.screen().root
    self.display.allow_events(Xlib.X.AsyncKeyboard, Xlib.X.CurrentTime)
    self.root.change_attributes(event_mask = Xlib.X.KeyReleaseMask)
    self.register_hotkey()
    self.listener_src = GObject.timeout_add(300, self.listen_cb)
    Notify.init('Copy Current File Plugin')

  def do_deactivate(self):
    '''
    stop listening, unregister hotkey and clean up
    '''
    GObject.source_remove(self.listener_src)
    self.unregister_hotkey()
    self.display.close()
    self.root = None
    self.display = None
    self.listener_src = None

  def register_hotkey(self):
    '''
    register the hotkey
    '''
    for modifier in self.modifier_combinations:
      self.root.grab_key(self.insert_key, modifier, True, Xlib.X.GrabModeAsync, Xlib.X.GrabModeAsync)

  def unregister_hotkey(self):
    '''
    unregister the hotkey
    '''
    for modifier in self.modifier_combinations:
      self.root.ungrab_key(self.insert_key, modifier)

  def listen_cb(self):
    '''
    callback for listening, checks if the hotkey has been pressed
    '''
    Gdk.threads_enter()
    if self.root.display.pending_events() > 0:
      event = self.root.display.next_event()
      if (event.type == Xlib.X.KeyRelease) and (event.detail == self.insert_key):
        self.copy_current()

    Gdk.threads_leave()
    return True

  def copy_current(self):
    '''
    Copies the currently playing song
    '''
    sp = self.object.props.shell_player
    cur_entry = sp.get_playing_entry()
    if not cur_entry:
      return

    uri = urlparse(cur_entry.get_string(RB.RhythmDBPropType.LOCATION))
    if uri.scheme != 'file':
      return

    fPath = urllib.parse.unquote(uri.path)
    destination = '/media/romeu/PENDRIVE1NTFS'
    copyfile(fPath, destination + '/' + os.path.basename(fPath))
    notification = Notify.Notification.new('Rhythmbox', os.path.basename(fPath), 'trophy-gold')
    notification.show()

    try:
      sp.do_next()
    except GLib.GError:
      pass


