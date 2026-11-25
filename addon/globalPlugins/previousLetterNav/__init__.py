# -*- coding: UTF-8 -*-
# Navigare înapoi după literă (Shift+literă) în listele de fișiere din Windows.
#
# Litera simplă în Explorer duce la URMĂTORUL fișier care începe cu ea.
# Acest add-on adaugă Shift+literă, care duce la fișierul ANTERIOR.
# Ca în Explorer: aceeași literă repetată ciclează, iar litere diferite
# tastate rapid (sub o secundă) caută după prefix (ex. Shift+R, Shift+E -> "re").

import time

import globalPluginHandler
import controlTypes
import tones
import ui
from NVDAObjects import NVDAObject
from scriptHandler import script
from logHandler import log

try:
	import UIAHandler
	from comtypes.gen import UIAutomationClient as UIA
except Exception:
	UIAHandler = None
	UIA = None

# Clasele de fereastră ale listelor de fișiere:
# DirectUIHWND = Explorer și dialogurile moderne, SysListView32 = desktop și liste clasice.
FILE_LIST_WINDOW_CLASSES = ("DirectUIHWND", "SysListView32")
TYPEAHEAD_TIMEOUT = 1.0  # secunde, similar cu pauza din Explorer
LETTERS = "abcdefghijklmnopqrstuvwxyz"
CATEGORY = "Navigare înapoi după literă"

# accSelect flags (IAccessible)
SELFLAG_TAKEFOCUS = 0x1
SELFLAG_TAKESELECTION = 0x2


class _TypeAhead(object):
	"""Ține minte literele tastate rapid, ca tastarea incrementală din Explorer."""

	def __init__(self):
		self.buffer = ""
		self.last = 0.0

	def update(self, ch):
		now = time.monotonic()
		if now - self.last > TYPEAHEAD_TIMEOUT:
			self.buffer = ""
		self.last = now
		self.buffer += ch
		if len(set(self.buffer)) == 1:
			# Aceeași literă (o dată sau repetată): sari strict la anteriorul.
			return ch, False
		# Prefix din mai multe litere: elementul curent poate fi deja potrivit.
		return self.buffer, True


_typeAhead = _TypeAhead()


def _matches(name, prefix):
	return bool(name) and name.casefold().startswith(prefix)


def _searchOrder(count, current, inclusive):
	"""Indici înapoi de la elementul curent, cu revenire la final (wrap)."""
	if current < 0:
		current = 0
		inclusive = False
	start = current if inclusive else current - 1
	total = count if inclusive else count - 1
	for k in range(max(total, 0)):
		yield (start - k) % count


# ---------- UI Automation (Explorer, dialoguri moderne) ----------

def _findUIAList(obj):
	parent = obj.parent
	for _ in range(5):
		if parent is None:
			return None
		if parent.role == controlTypes.Role.LIST and getattr(parent, "UIAElement", None) is not None:
			return parent.UIAElement
		parent = parent.parent
	return None


def _getPattern(el, patternId, iface):
	try:
		p = el.GetCurrentPattern(patternId)
		return p.QueryInterface(iface) if p else None
	except Exception:
		return None


def _selectUIA(el):
	v = _getPattern(el, UIA.UIA_VirtualizedItemPatternId, UIA.IUIAutomationVirtualizedItemPattern)
	if v:
		try:
			v.Realize()
		except Exception:
			pass
	s = _getPattern(el, UIA.UIA_ScrollItemPatternId, UIA.IUIAutomationScrollItemPattern)
	if s:
		try:
			s.ScrollIntoView()
		except Exception:
			pass
	sel = _getPattern(el, UIA.UIA_SelectionItemPatternId, UIA.IUIAutomationSelectionItemPattern)
	if sel:
		sel.Select()
	el.SetFocus()


def _moveUIA(obj, prefix, inclusive):
	"""Returnează True/False, sau None dacă UIA nu se poate folosi aici."""
	if UIA is None or UIAHandler is None or getattr(UIAHandler, "handler", None) is None:
		return None
	focusEl = getattr(obj, "UIAElement", None)
	if focusEl is None:
		return None
	listEl = _findUIAList(obj)
	if listEl is None:
		return None
	client = UIAHandler.handler.clientObject
	cache = client.CreateCacheRequest()
	cache.AddProperty(UIA.UIA_NamePropertyId)
	cond = client.CreatePropertyCondition(UIA.UIA_ControlTypePropertyId, UIA.UIA_ListItemControlTypeId)
	# Descendants, ca să includă și elementele din grupuri (când lista e grupată).
	items = listEl.FindAllBuildCache(UIA.TreeScope_Descendants, cond, cache)
	count = items.Length if items else 0
	if not count:
		return False
	focusName = obj.name or ""
	names = []
	current = -1
	for i in range(count):
		el = items.GetElement(i)
		name = el.CachedName or ""
		names.append(name)
		if current < 0 and name == focusName and client.CompareElements(el, focusEl):
			current = i
	for idx in _searchOrder(count, current, inclusive):
		if _matches(names[idx], prefix):
			if idx == current:
				ui.message(names[idx])
			else:
				_selectUIA(items.GetElement(idx))
			return True
	return False


# ---------- Rezervă generică (IAccessible, ex. desktop) ----------

def _selectGeneric(target):
	try:
		target.IAccessibleObject.accSelect(
			SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION, target.IAccessibleChildID
		)
		return
	except Exception:
		pass
	target.setFocus()


def _moveGeneric(obj, prefix, inclusive):
	parent = obj.parent
	if parent is None:
		return False
	items = [c for c in parent.children if c.role == controlTypes.Role.LISTITEM]
	count = len(items)
	if not count:
		return False
	current = -1
	for i, c in enumerate(items):
		if c == obj:
			current = i
			break
	for idx in _searchOrder(count, current, inclusive):
		if _matches(items[idx].name, prefix):
			if idx == current:
				ui.message(items[idx].name)
			else:
				_selectGeneric(items[idx])
			return True
	return False


class PreviousLetterNavItem(NVDAObject):
	"""Adăugat peste elementele din listele de fișiere."""

	@script(
		description="Mută la elementul anterior care începe cu litera apăsată",
		category=CATEGORY,
		gestures=["kb:shift+%s" % c for c in LETTERS],
	)
	def script_previousByLetter(self, gesture):
		key = (gesture.mainKeyName or "").lower()
		if len(key) != 1:
			gesture.send()
			return
		prefix, inclusive = _typeAhead.update(key)
		found = None
		try:
			found = _moveUIA(self, prefix, inclusive)
		except Exception:
			log.debugWarning("previousLetterNav: UIA a eșuat", exc_info=True)
		if found is None:
			try:
				found = _moveGeneric(self, prefix, inclusive)
			except Exception:
				log.debugWarning("previousLetterNav: metoda generică a eșuat", exc_info=True)
				found = False
		if not found:
			tones.beep(220, 60)


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		try:
			if (
				obj.role == controlTypes.Role.LISTITEM
				and obj.windowClassName in FILE_LIST_WINDOW_CLASSES
			):
				clsList.insert(0, PreviousLetterNavItem)
		except Exception:
			pass
