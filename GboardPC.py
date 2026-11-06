#!/usr/bin/env python3
# Gboard PC — an offline Bangla Avro Phonetic keyboard for Windows.
# Copyright (C) 2026 Gboard PC contributors.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See https://www.gnu.org/licenses/gpl-3.0.html
#
# Avro patterns are based on OmicronLab's Avro Phonetic dictionary and the
# pyAvroPhonetic parser by Kaustav Das Modak. The bundled word-frequency seed
# is from Minhas Kamal's BengaliDictionary repository (GPL-3.0).

"""Gboard PC. Windows 10/11, Python 3.10+, tkinter, pystray and Pillow.

Typing data is processed only in memory. The app makes no network requests and
does not create a history or log. Only the text box and files explicitly saved
by the user retain text.
"""

from __future__ import annotations

import base64
import ctypes
import gzip
import json
import queue
import re
import threading
import tkinter as tk
import unicodedata
from ctypes import wintypes
from tkinter import filedialog, messagebox, ttk

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # A clear message is shown when not packaged.
    pystray = None
    Image = ImageDraw = ImageFont = None
    _TRAY_IMPORT_ERROR = exc
else:
    _TRAY_IMPORT_ERROR = None


APP_NAME = "Gboard PC"
HOTKEY_LABEL = "Ctrl + Alt + Shift + Space"
SUGGESTION_HOTKEY_LABEL = "Ctrl + Alt + Shift + Q / W / E"
SUGGESTION_VKS = {0x51: 0, 0x57: 1, 0x45: 2}

# Compressed Avro Phonetic pattern data and 3,000 high-frequency romanized
# Bangla entries are embedded so the built app works fully offline.
AVRO_SPEC_GZIP_B64 = (
    "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"
)
WORD_FREQUENCY_GZIP_B64 = (
    "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"
    "5PJq4F9l3/8CedXKFBReAAA="
)


def _unpack_text(payload: str) -> str:
    return gzip.decompress(base64.b64decode(payload)).decode("utf-8")


AVRO_SPEC = json.loads(_unpack_text(AVRO_SPEC_GZIP_B64))["data"]
PATTERNS = AVRO_SPEC["patterns"]
VOWELS = set(AVRO_SPEC["vowel"])
CONSONANTS = set(AVRO_SPEC["consonant"])
CASE_SENSITIVE = set(AVRO_SPEC["casesensitive"])
NUMBER_KEYS = set(AVRO_SPEC["number"])


def _is_vowel(char: str) -> bool:
    return bool(char) and char.lower() in VOWELS


def _is_consonant(char: str) -> bool:
    return bool(char) and char.lower() in CONSONANTS


def _is_punctuation(char: str) -> bool:
    return not (_is_vowel(char) or _is_consonant(char))


def _is_vowel_pattern(pattern: str) -> bool:
    """Return true for an Avro pattern made only of Roman vowel keys."""
    return bool(pattern) and all(_is_vowel(char) for char in pattern)


def _fix_case(text: str) -> str:
    return "".join(ch if ch.lower() in CASE_SENSITIVE else ch.lower() for ch in text)


def _rule_match(rule_match: dict, text: str, start: int, end: int) -> bool:
    kind = rule_match["type"]
    scope = rule_match["scope"]
    negative = scope.startswith("!")
    if negative:
        scope = scope[1:]
    check_at = start - 1 if kind == "prefix" else end

    if scope == "punctuation":
        actual = not (0 <= check_at < len(text)) or _is_punctuation(text[check_at])
    elif scope == "vowel":
        actual = 0 <= check_at < len(text) and _is_vowel(text[check_at])
    elif scope == "consonant":
        actual = 0 <= check_at < len(text) and _is_consonant(text[check_at])
    elif scope == "exact":
        value = rule_match.get("value", "")
        if kind == "prefix":
            exact_start, exact_end = start - len(value), start
        else:
            exact_start, exact_end = end, end + len(value)
        # Match pyAvroPhonetic's boundary handling for its exact-scope rules.
        actual = exact_start >= 0 and exact_end <= len(text) and text[exact_start:exact_end] == value
    else:
        actual = False
    return actual ^ negative


def _rules_replace(rules: list, text: str, start: int, end: int):
    for rule in rules:
        if all(_rule_match(condition, text, start, end) for condition in rule["matches"]):
            return rule["replace"]
    return None


def avro_parse(text: str) -> str:
    """Transliterate roman text with Avro's longest ordered pattern rules."""
    fixed = _fix_case(text)
    output = []
    processed_to = 0
    for cursor, char in enumerate(fixed):
        if cursor < processed_to:
            continue
        # Keep OmicronLab's original order across *all* patterns. Searching
        # non-rule and rule patterns in separate passes can let a shorter
        # consonant match steal the beginning of a vowel/conjunct sequence.
        found = next((p for p in PATTERNS
                      if fixed.startswith(p["find"], cursor)), None)
        if found is not None:
            processed_to = cursor + len(found["find"])
            previous = fixed[cursor - 1] if cursor else ""
            if previous and _is_consonant(previous) and _is_vowel_pattern(found["find"]):
                # A vowel pattern immediately after a consonant uses that
                # pattern's dependent sign (kar). This explicitly preserves
                # ke -> কে, kE -> কে, ki -> কি, and equivalent Avro forms.
                output.append(found["replace"])
            elif "rules" in found:
                replacement = _rules_replace(found["rules"], fixed, cursor, processed_to)
                output.append(found["replace"] if replacement is None else replacement)
            else:
                output.append(found["replace"])
        else:
            processed_to = cursor + 1
            output.append(char)
    return "".join(output)


# Common chat spellings have deliberate spellings in everyday Bangla. These
# entries also guarantee the exact examples listed in the app specification.
COMMON_WORDS = {
    "ami": "আমি", "tumi": "তুমি", "kemon": "কেমন", "acho": "আছো",
    "bhalo": "ভালো", "banglay": "বাংলায়", "gan": "গান", "gai": "গাই",
    "amra": "আমরা", "apni": "আপনি", "tora": "তোরা", "tara": "তারা",
    "bangla": "বাংলা", "manush": "মানুষ", "bhasha": "ভাষা",
    "bari": "বাড়ি", "desh": "দেশ", "dhonnobad": "ধন্যবাদ",
    "shundor": "সুন্দর", "khub": "খুব", "bhalo": "ভালো",
    "ki": "কি", "kothay": "কোথায়", "keno": "কেন", "hobe": "হবে",
    "hoy": "হয়", "korbo": "করব", "koro": "করো", "kori": "করি",
    "likhi": "লিখি", "dekhi": "দেখি", "bujhi": "বুঝি", "chai": "চাই",
    "jabo": "যাব", "asho": "এসো", "aj": "আজ", "kal": "কাল",
    "ekhon": "এখন", "onek": "অনেক", "shob": "সব", "kichu": "কিছু",
    "ache": "আছে", "nei": "নেই", "na": "না", "hya": "হ্যাঁ",
    "hoyechhe": "হয়েছে", "korchi": "করছি", "bhalo achi": "ভালো আছি",
}


def _build_dictionary():
    words = _unpack_text(WORD_FREQUENCY_GZIP_B64).splitlines()
    result = {}
    # Preserve the corpus order: it is sorted by observed frequency.
    for roman in words:
        roman = roman.strip()
        if not roman or not re.fullmatch(r"[A-Za-z.]{2,}", roman):
            continue
        bangla = avro_parse(roman)
        if not any("\u0980" <= ch <= "\u09ff" for ch in bangla):
            continue
        result.setdefault(roman.lower(), bangla)
    result.update(COMMON_WORDS)
    return result


DICTIONARY = _build_dictionary()
DICTIONARY_WORD_COUNT = len(set(DICTIONARY.values()))
if DICTIONARY_WORD_COUNT < 2000:
    raise RuntimeError("The bundled offline Bangla dictionary is incomplete.")

BENGALI_LETTER_RE = re.compile(r"[\u0980-\u09ff]")
LATIN_LETTER_RE = re.compile(r"[A-Za-z]")


def _edit_distance_one(left: str, right: str) -> bool:
    if left == right:
        return True
    if abs(len(left) - len(right)) > 1:
        return False
    i = j = differences = 0
    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            i += 1
            j += 1
        else:
            differences += 1
            if differences > 1:
                return False
            if len(left) >= len(right):
                i += 1
            if len(right) >= len(left):
                j += 1
    if i < len(left) or j < len(right):
        differences += 1
    return differences <= 1


def word_output(roman: str) -> str:
    key = roman.lower()
    if key in COMMON_WORDS:
        return COMMON_WORDS[key]
    return DICTIONARY.get(key, avro_parse(roman))


def suggestions(roman: str) -> list[str]:
    if not roman:
        return []
    key = roman.lower()
    candidates = []

    def add(value):
        # Keep the suggestion strip in Bengali script. Unknown or partial
        # Roman text can still be typed, but it should not appear as a Bangla
        # candidate chip unless the transliterator has produced Bengali text.
        if (value and value not in candidates
                and BENGALI_LETTER_RE.search(value)
                and not LATIN_LETTER_RE.search(value)):
            candidates.append(value)

    add(word_output(roman))
    # Exact and partial dictionary hits, in the corpus frequency order.
    for source, bangla in DICTIONARY.items():
        if source.startswith(key):
            add(bangla)
            if len(candidates) >= 3:
                return candidates[:3]
    # A one-character typo may still offer the intended common word.
    if len(key) >= 3 and len(candidates) < 3:
        for source, bangla in DICTIONARY.items():
            if _edit_distance_one(key, source):
                add(bangla)
                if len(candidates) >= 3:
                    break
    return candidates[:3]


def autocorrect(roman: str, plain: str) -> str:
    key = roman.lower()
    if key in DICTIONARY:
        return DICTIONARY[key]
    if len(key) >= 4:
        close = next((candidate for candidate in DICTIONARY
                      if _edit_distance_one(key, candidate)), None)
        if close:
            return DICTIONARY[close]
    return plain


# Win32 SendInput structures. Unicode packets work with normal desktop apps,
# including Notepad, Word and browsers.
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_BACK = 0x08
VK_RETURN = 0x0D
VK_SPACE = 0x20
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C
LLKHF_INJECTED = 0x10
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012
ASFW_ANY = 0xFFFFFFFF


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]


class INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUTUNION)]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND), ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM), ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD), ("pt", POINT),
                ("lPrivate", wintypes.DWORD)]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int,
                              wintypes.WPARAM, wintypes.LPARAM)
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetKeyState.argtypes = [ctypes.c_int]
user32.GetKeyState.restype = wintypes.SHORT
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.AllowSetForegroundWindow.argtypes = [wintypes.DWORD]
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetCurrentThreadId.restype = wintypes.DWORD


def _key_input(vk=0, scan=0, flags=0) -> INPUT:
    value = INPUT()
    value.type = INPUT_KEYBOARD
    value.union.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
    return value


def _send_events(events: list[INPUT]):
    if events:
        array = (INPUT * len(events))(*events)
        user32.SendInput(len(events), array, ctypes.sizeof(INPUT))


def send_unicode(text: str):
    events = []
    for char in text:
        encoded = char.encode("utf-16-le")
        for offset in range(0, len(encoded), 2):
            unit = encoded[offset] | (encoded[offset + 1] << 8)
            events.append(_key_input(scan=unit, flags=KEYEVENTF_UNICODE))
            events.append(_key_input(scan=unit, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))
    _send_events(events)


def _backspace_count(text: str) -> int:
    """Count user-visible Unicode clusters for Windows Backspace replacement."""
    count = 0
    join_next = False
    for char in text:
        if char == "\u09cd":  # Bengali hasant joins the following consonant.
            join_next = True
            continue
        if char == "\u200d":  # ZWJ also binds the next character to this cluster.
            join_next = True
            continue
        if char == "\u200c":  # ZWNJ explicitly breaks a conjunct.
            join_next = False
            continue
        if unicodedata.category(char).startswith("M"):
            # Bengali vowel signs, nukta and nasal marks are part of the
            # preceding visible character and should not get separate deletes.
            continue
        if join_next:
            join_next = False
            continue
        count += 1
    return count


def send_vk(vk: int, count: int = 1):
    events = []
    for _ in range(max(0, count)):
        events.append(_key_input(vk=vk))
        events.append(_key_input(vk=vk, flags=KEYEVENTF_KEYUP))
    _send_events(events)


def _is_down(vk: int) -> bool:
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def _physical_character(vk: int) -> str | None:
    shift = _is_down(VK_SHIFT)
    caps = bool(user32.GetKeyState(0x14) & 1)
    upper = shift ^ caps
    if 0x41 <= vk <= 0x5A:
        char = chr(vk)
        return char if upper else char.lower()
    normal = {
        0x30: "0", 0x31: "1", 0x32: "2", 0x33: "3", 0x34: "4",
        0x35: "5", 0x36: "6", 0x37: "7", 0x38: "8", 0x39: "9",
        0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-", 0xBE: ".",
        0xBF: "/", 0xC0: "`", 0xDB: "[", 0xDC: "\\", 0xDD: "]", 0xDE: "'",
    }
    shifted = {
        0x30: ")", 0x31: "!", 0x32: "@", 0x33: "#", 0x34: "$",
        0x35: "%", 0x36: "^", 0x37: "&", 0x38: "*", 0x39: "(",
        0xBA: ":", 0xBB: "+", 0xBC: "<", 0xBD: "_", 0xBE: ">",
        0xBF: "?", 0xC0: "~", 0xDB: "{", 0xDC: "|", 0xDD: "}", 0xDE: '"',
    }
    if vk in normal:
        return shifted[vk] if shift else normal[vk]
    if 0x60 <= vk <= 0x69:
        return str(vk - 0x60)
    return None


class KeyboardEngine:
    """Low-level hook plus the active roman word and correction undo stack."""

    def __init__(self, events: queue.Queue):
        self.events = events
        self.lock = threading.RLock()
        self.enabled = False
        self.mode = "English"
        self.raw = ""
        self.rendered = ""
        self.active_hwnd = None
        self.commits = []
        self.suppressed = set()
        self.thread = None
        self.thread_id = 0
        self.hook = None
        self.ready = threading.Event()
        self._callback_ref = HOOKPROC(self._callback)

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.ready.clear()
        self.thread = threading.Thread(target=self._hook_loop, name="GboardPC keyboard hook", daemon=True)
        self.thread.start()
        self.ready.wait(3)

    def stop(self):
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

    def _hook_loop(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        self.hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._callback_ref, kernel32.GetModuleHandleW(None), 0)
        self.ready.set()
        if not self.hook:
            self.events.put(("error", "Windows did not allow the global keyboard hook."))
            return
        msg = MSG()
        while True:
            result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        user32.UnhookWindowsHookEx(self.hook)
        self.hook = None
        self.thread_id = 0

    def set_enabled(self, value: bool):
        with self.lock:
            self.enabled = bool(value)
            self._clear_word()
        self.events.put(("status", None))

    def set_mode(self, value: str):
        with self.lock:
            self.mode = "Avro Phonetic (বাংলা)" if value.startswith("Avro") else "English"
            self._clear_word()
        self.events.put(("status", None))

    def reset_composition(self):
        with self.lock:
            self._clear_word()

    def _clear_word(self):
        self.raw = ""
        self.rendered = ""
        self.active_hwnd = None
        self.commits.clear()
        self.events.put(("compose", "", []))

    def _send_to_target(self, text=None, vk=None, count=1):
        target = self.active_hwnd
        current = user32.GetForegroundWindow()
        if target and current != target:
            if not user32.IsWindow(target):
                self.active_hwnd = None
                return
            user32.AllowSetForegroundWindow(ASFW_ANY)
            user32.SetForegroundWindow(target)
            if user32.GetForegroundWindow() != target:
                return
        if text is not None:
            send_unicode(text)
        elif vk is not None:
            send_vk(vk, count)

    def _replace_rendered(self, text: str):
        """Replace the visible preview of the active Roman word in-place."""
        if text == self.rendered:
            return
        if self.rendered:
            self._send_to_target(vk=VK_BACK, count=_backspace_count(self.rendered))
        if text:
            self._send_to_target(text=text)
        self.rendered = text

    def feed_character(self, char: str, target=None):
        with self.lock:
            if not self.enabled or self.mode == "English":
                return
            if target:
                if self.active_hwnd and target != self.active_hwnd and (self.raw or self.commits):
                    self._clear_word()
                self.active_hwnd = target
            if char.isascii() and char.isalnum():
                if not self.raw:
                    self.active_hwnd = self.active_hwnd or user32.GetForegroundWindow()
                self.raw += char
                rendered = word_output(self.raw)
                self._replace_rendered(rendered)
                self.events.put(("compose", self.raw, suggestions(self.raw)))
            elif char == " ":
                self._commit(" ")
            elif char in ("\r", "\n"):
                self._commit("\n")
            elif char.isspace():
                self._commit(char)
            else:
                self._commit(avro_parse(char))

    def feed_virtual(self, char: str, target=None):
        """Handle a click on a screen key in either of the two modes."""
        with self.lock:
            if target:
                self.active_hwnd = target
            if self.enabled and self.mode != "English":
                self.feed_character(char, target)
            elif char == "BACK":
                self._send_to_target(vk=VK_BACK)
            elif char == "\r":
                self._send_to_target(vk=VK_RETURN)
            else:
                self._send_to_target(text=char)

    def _commit(self, separator: str):
        raw = self.raw
        plain = word_output(raw) if raw else ""
        corrected = autocorrect(raw, plain) if raw else ""
        if raw:
            self._replace_rendered(corrected)
        if separator == "\n":
            self._send_to_target(vk=VK_RETURN)
            separator_for_undo = "\n"
        elif separator:
            self._send_to_target(text=separator)
            separator_for_undo = separator
        else:
            separator_for_undo = ""
        if raw:
            self.commits.append((raw, plain, corrected, separator_for_undo))
            if len(self.commits) > 30:
                del self.commits[:-30]
        self.raw = ""
        self.rendered = ""
        self.events.put(("compose", "", []))

    def backspace(self):
        with self.lock:
            if self.raw:
                self.raw = self.raw[:-1]
                rendered = word_output(self.raw) if self.raw else ""
                self._replace_rendered(rendered)
                self.events.put(("compose", self.raw, suggestions(self.raw)))
            elif self.commits:
                raw, plain, corrected, separator = self.commits.pop()
                erase_count = _backspace_count(corrected + separator)
                if erase_count:
                    self._send_to_target(vk=VK_BACK, count=erase_count)
                self._send_to_target(text=plain)
                self.raw = raw
                self.rendered = plain
                self.events.put(("compose", raw, suggestions(raw)))
            else:
                self._send_to_target(vk=VK_BACK)

    def choose_suggestion(self, index: int):
        with self.lock:
            if not self.raw:
                return
            options = suggestions(self.raw)
            if not 0 <= index < len(options):
                return
            raw = self.raw
            plain = word_output(raw)
            chosen = options[index]
            self._replace_rendered(chosen)
            self.commits.append((raw, plain, chosen, ""))
            self.raw = ""
            self.rendered = ""
            self.events.put(("compose", "", []))

    def _callback(self, code, wparam, lparam):
        if code < 0:
            return user32.CallNextHookEx(self.hook, code, wparam, lparam)
        try:
            info = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            vk = int(info.vkCode)
            down = wparam in (WM_KEYDOWN, WM_SYSKEYDOWN)
            up = wparam in (WM_KEYUP, WM_SYSKEYUP)
            if info.flags & LLKHF_INJECTED:
                return user32.CallNextHookEx(self.hook, code, wparam, lparam)
            if up and vk in self.suppressed:
                self.suppressed.discard(vk)
                return 1
            if not down:
                return user32.CallNextHookEx(self.hook, code, wparam, lparam)

            ctrl, alt, shift = _is_down(VK_CONTROL), _is_down(VK_MENU), _is_down(VK_SHIFT)
            if ctrl and alt and shift and vk == VK_SPACE:
                with self.lock:
                    self.mode = "English" if self.mode.startswith("Avro") else "Avro Phonetic (বাংলা)"
                    self._clear_word()
                self.suppressed.add(vk)
                self.events.put(("status", None))
                return 1
            if ctrl and alt and shift and vk in SUGGESTION_VKS:
                self.choose_suggestion(SUGGESTION_VKS[vk])
                self.suppressed.add(vk)
                return 1

            with self.lock:
                if not self.enabled or self.mode == "English":
                    return user32.CallNextHookEx(self.hook, code, wparam, lparam)
                if ctrl or alt or _is_down(VK_LWIN) or _is_down(VK_RWIN):
                    if self.raw or self.commits:
                        self._clear_word()
                    return user32.CallNextHookEx(self.hook, code, wparam, lparam)
                target = user32.GetForegroundWindow()
                if self.active_hwnd and target != self.active_hwnd and (self.raw or self.commits):
                    self._clear_word()
                self.active_hwnd = target
                if vk == VK_BACK:
                    self.backspace()
                    self.suppressed.add(vk)
                    return 1
                if vk == VK_SPACE:
                    self.feed_character(" ", target)
                    self.suppressed.add(vk)
                    return 1
                if vk == VK_RETURN:
                    self.feed_character("\r", target)
                    self.suppressed.add(vk)
                    return 1
                char = _physical_character(vk)
                if char is not None:
                    self.feed_character(char, target)
                    self.suppressed.add(vk)
                    return 1
                # Moving the caret or changing controls invalidates our undo
                # positions, so let those keys through and forget that history.
                if vk in (0x09, 0x1B, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E,
                          0x21, 0x22, 0x23, 0x24):
                    self._clear_word()
                    return user32.CallNextHookEx(self.hook, code, wparam, lparam)
        except Exception:
            # A low-level hook must never unwind through Windows.
            return user32.CallNextHookEx(self.hook, code, wparam, lparam)
        return user32.CallNextHookEx(self.hook, code, wparam, lparam)


class GboardPC:
    BG = "#f4f7fb"
    CARD = "#ffffff"
    INK = "#15243a"
    MUTED = "#67758b"
    BLUE = "#1d65d6"
    GREEN = "#13875a"
    RED = "#c33a45"

    KEY_ROWS = [
        [("q", "ক"), ("w", "ও"), ("e", "এ"), ("r", "র"), ("t", "ত"), ("y", "য"), ("u", "উ"), ("i", "ই"), ("o", "অ"), ("p", "প")],
        [("a", "আ"), ("s", "স"), ("d", "দ"), ("f", "ফ"), ("g", "গ"), ("h", "হ"), ("j", "জ"), ("k", "ক"), ("l", "ল")],
        [("z", "জ"), ("x", "ক্ষ"), ("c", "চ"), ("v", "ভ"), ("b", "ব"), ("n", "ন"), ("m", "ম")],
    ]

    def __init__(self):
        self.events = queue.Queue()
        self.engine = KeyboardEngine(self.events)
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("900x760")
        self.root.minsize(760, 680)
        self.root.configure(bg=self.BG)
        self.root.attributes("-topmost", True)
        self.root.update_idletasks()
        self.root_hwnd = user32.GetAncestor(self.root.winfo_id(), 2)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.root.bind("<FocusOut>", self._remember_focus)
        self.display_var = tk.BooleanVar(value=True)
        self.display_enabled = True
        self.mode_var = tk.StringVar(value="English")
        self.status_var = tk.StringVar(value="OFF")
        self.hint_var = tk.StringVar(value="Type in any app • offline • text stays on this PC")
        self.suggestion_buttons = []
        self.tray = None
        self.tray_thread = None
        self.last_external_hwnd = None
        self._build_ui()
        self.engine.start()
        self._refresh_status()
        self.root.after(35, self._drain_events)
        self._start_tray()
        if _TRAY_IMPORT_ERROR:
            self.root.after(400, lambda: messagebox.showerror(
                APP_NAME, "The system tray needs pystray and Pillow.\n\n"
                "Install them with: python -m pip install pystray pillow"))

    def _build_ui(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("App.TFrame", background=self.BG)
        style.configure("Card.TFrame", background=self.CARD)
        style.configure("Title.TLabel", background=self.BG, foreground=self.INK,
                        font=("Segoe UI", 21, "bold"))
        style.configure("Sub.TLabel", background=self.BG, foreground=self.MUTED,
                        font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=self.CARD, foreground=self.INK,
                        font=("Segoe UI", 12, "bold"))
        style.configure("Body.TLabel", background=self.CARD, foreground=self.MUTED,
                        font=("Segoe UI", 10))
        style.configure("Mode.TRadiobutton", background=self.CARD, foreground=self.INK,
                        font=("Segoe UI", 10, "bold"), padding=(10, 8))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"),
                        padding=(14, 9), background=self.BLUE, foreground="white")
        style.map("Primary.TButton", background=[("active", "#1554b4")])
        style.configure("Stop.TButton", font=("Segoe UI", 10, "bold"),
                        padding=(14, 9), background="#fce9eb", foreground=self.RED)
        style.map("Stop.TButton", background=[("active", "#f6d5d8")])
        style.configure("Tool.TButton", font=("Segoe UI", 10), padding=(10, 7),
                        background="#edf2f9", foreground=self.INK)

        shell = ttk.Frame(self.root, padding=20, style="App.TFrame")
        shell.pack(fill="both", expand=True)
        heading = ttk.Frame(shell, style="App.TFrame")
        heading.pack(fill="x", pady=(0, 14))
        ttk.Label(heading, text="গবোর্ড পিসি", style="Title.TLabel").pack(side="left")
        ttk.Label(heading, text="  Gboard PC", style="Sub.TLabel").pack(side="left", pady=(8, 0))
        self.status_badge = tk.Label(heading, text="● OFF", bg="#e9edf3", fg=self.MUTED,
                                     font=("Segoe UI", 10, "bold"), padx=12, pady=7)
        self.status_badge.pack(side="right", pady=(5, 0))

        mode_card = ttk.Frame(shell, padding=14, style="Card.TFrame")
        mode_card.pack(fill="x", pady=(0, 12))
        top = ttk.Frame(mode_card, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="Typing mode", style="CardTitle.TLabel").pack(side="left")
        ttk.Label(top, text=f"Global toggle: {HOTKEY_LABEL}", style="Body.TLabel").pack(side="right")
        row = ttk.Frame(mode_card, style="Card.TFrame")
        row.pack(fill="x", pady=(9, 0))
        ttk.Radiobutton(row, text="English", value="English", variable=self.mode_var,
                        style="Mode.TRadiobutton", command=lambda: self.set_mode("English")).pack(side="left")
        ttk.Radiobutton(row, text="Avro Phonetic (বাংলা)", value="Avro Phonetic (বাংলা)",
                        variable=self.mode_var, style="Mode.TRadiobutton",
                        command=lambda: self.set_mode("Avro Phonetic (বাংলা)")).pack(side="left", padx=(6, 0))
        ttk.Button(row, text="Apply", style="Primary.TButton", command=self.apply).pack(side="right")
        ttk.Button(row, text="Disable", style="Stop.TButton", command=self.disable).pack(side="right", padx=(0, 8))

        display_card = ttk.Frame(shell, padding=(14, 10), style="Card.TFrame")
        display_card.pack(fill="x", pady=(0, 12))
        ttk.Checkbutton(display_card, text="Show floating keyboard and text box",
                        variable=self.display_var, command=self._display_changed).pack(side="left")
        ttk.Label(display_card, text="Turn this off to use the tray icon only.",
                  style="Body.TLabel").pack(side="right")

        keyboard_card = ttk.Frame(shell, padding=14, style="Card.TFrame")
        keyboard_card.pack(fill="x", pady=(0, 12))
        title_row = ttk.Frame(keyboard_card, style="Card.TFrame")
        title_row.pack(fill="x")
        ttk.Label(title_row, text="বাংলা সাজেশন", style="CardTitle.TLabel").pack(side="left")
        ttk.Label(title_row, text=SUGGESTION_HOTKEY_LABEL, style="Body.TLabel").pack(side="right")
        suggest_row = ttk.Frame(keyboard_card, style="Card.TFrame")
        suggest_row.pack(fill="x", pady=(8, 12))
        for _ in range(3):
            button = ttk.Button(suggest_row, text="", style="Tool.TButton")
            self.suggestion_buttons.append(button)
            button.pack(side="left", expand=True, fill="x", padx=3)

        ttk.Label(keyboard_card, text="QWERTY", style="Body.TLabel").pack(anchor="w", pady=(0, 7))
        for row_keys in self.KEY_ROWS:
            key_row = ttk.Frame(keyboard_card, style="Card.TFrame")
            key_row.pack(fill="x", pady=2)
            for roman, bangla in row_keys:
                key = tk.Button(key_row, text=f"{roman.upper()}\n{bangla}",
                                font=("Segoe UI", 9, "bold"), bg="#f5f8fc", fg=self.INK,
                                activebackground="#e5efff", relief="flat", bd=0,
                                highlightthickness=1, highlightbackground="#e3e9f1",
                                height=2, command=lambda ch=roman: self._keyboard_press(ch))
                key.pack(side="left", expand=True, fill="x", padx=2, ipadx=2)
        bottom = ttk.Frame(keyboard_card, style="Card.TFrame")
        bottom.pack(fill="x", pady=(4, 0))
        for label, value in [("123", "1"), ("?123", "."), ("Space", " "), ("Enter", "\r"), ("⌫", "BACK")]:
            button = ttk.Button(bottom, text=label, style="Tool.TButton",
                                command=lambda val=value: self._keyboard_press(val))
            button.pack(side="left", expand=True, fill="x", padx=2)

        text_card = ttk.Frame(shell, padding=14, style="Card.TFrame")
        text_card.pack(fill="both", expand=True)
        text_head = ttk.Frame(text_card, style="Card.TFrame")
        text_head.pack(fill="x", pady=(0, 8))
        ttk.Label(text_head, text="Your text", style="CardTitle.TLabel").pack(side="left")
        self.count_label = ttk.Label(text_head, text=f"Offline dictionary: {DICTIONARY_WORD_COUNT:,} words",
                                     style="Body.TLabel")
        self.count_label.pack(side="right")
        self.text = tk.Text(text_card, wrap="word", undo=True, font=("Nirmala UI", 15),
                            bg="#fbfcfe", fg=self.INK, insertbackground=self.BLUE,
                            relief="flat", padx=12, pady=10, height=5)
        self.text.pack(fill="both", expand=True)
        self.text.bind("<FocusIn>", lambda _event: self._remember_app_target())
        toolbar = ttk.Frame(text_card, style="Card.TFrame")
        toolbar.pack(fill="x", pady=(10, 0))
        ttk.Button(toolbar, text="কপি", style="Tool.TButton", command=self.copy_selection).pack(side="left")
        ttk.Button(toolbar, text="ক্লিপে রাখুন", style="Tool.TButton", command=self.copy_all).pack(side="left", padx=7)
        ttk.Button(toolbar, text="সেভ (.txt)", style="Tool.TButton", command=self.save_text).pack(side="left")
        ttk.Button(toolbar, text="মুছুন", style="Tool.TButton", command=self.clear_text).pack(side="right")
        ttk.Label(shell, textvariable=self.hint_var, style="Sub.TLabel").pack(anchor="w", pady=(10, 0))

    def _remember_focus(self, _event=None):
        self.root.after(80, self._remember_app_target)

    def _remember_app_target(self):
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd and hwnd != self.root_hwnd:
                self.last_external_hwnd = hwnd
        except Exception:
            pass

    def _keyboard_press(self, value: str):
        target = self.engine.active_hwnd or self.last_external_hwnd or user32.GetForegroundWindow()
        if not target:
            target = self.root_hwnd
        if target == self.root_hwnd:
            self.text.focus_set()
            self.text.mark_set("insert", "end-1c")
        if value == "BACK" and self.engine.enabled and self.engine.mode.startswith("Avro"):
            self.engine.backspace()
        else:
            self.engine.feed_virtual(value, target)

    def _display_changed(self):
        if self.display_var.get():
            self.show_window()
        else:
            self.hide_window()

    def show_window(self):
        previous = user32.GetForegroundWindow()
        if previous and previous != self.root_hwnd:
            self.last_external_hwnd = previous
        self.display_enabled = True
        self.display_var.set(True)
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)

    def hide_window(self):
        self.display_enabled = False
        self.display_var.set(False)
        self.root.withdraw()

    def apply(self):
        self.engine.set_enabled(True)
        if self.mode_var.get() == "English":
            self.set_mode("Avro Phonetic (বাংলা)")
        self._refresh_status()

    def disable(self):
        self.engine.set_enabled(False)
        self._refresh_status()

    def set_mode(self, mode: str):
        self.mode_var.set(mode)
        self.engine.set_mode(mode)
        self._refresh_status()

    def _refresh_status(self):
        enabled = self.engine.enabled
        if enabled:
            self.status_var.set("ON")
            self.status_badge.configure(text="● ON", bg="#ddf5e9", fg=self.GREEN)
        else:
            self.status_var.set("OFF")
            self.status_badge.configure(text="● OFF", bg="#e9edf3", fg=self.MUTED)
        mode = self.engine.mode
        state = "ON" if enabled else "OFF"
        self.hint_var.set(f"{state}  •  {mode}  •  {HOTKEY_LABEL} switches modes  •  offline")
        if self.tray:
            self.tray.title = f"Gboard PC — {state} — {mode}"
            try:
                self.tray.icon = self._make_tray_image(enabled)
                self.tray.update_menu()
            except Exception:
                pass

    def _suggestion_clicked(self, index):
        target = self.engine.active_hwnd or self.last_external_hwnd
        if target:
            user32.AllowSetForegroundWindow(ASFW_ANY)
            user32.SetForegroundWindow(target)
        self.engine.choose_suggestion(index)

    def _drain_events(self):
        try:
            while True:
                event, value, *rest = self.events.get_nowait()
                if event == "compose":
                    choices = rest[0] if rest else []
                    for index, button in enumerate(self.suggestion_buttons):
                        if index < len(choices):
                            button.configure(text=choices[index], command=lambda i=index: self._suggestion_clicked(i))
                            button.state(["!disabled"])
                        else:
                            button.configure(text="—", command=lambda: None)
                            button.state(["disabled"])
                elif event == "status":
                    self.mode_var.set(self.engine.mode)
                    self._refresh_status()
                elif event == "error":
                    self.hint_var.set(value)
                    self.disable()
                    messagebox.showerror(APP_NAME, value)
                elif event == "ui_toggle":
                    self.engine.set_enabled(not self.engine.enabled)
                    if self.engine.enabled and self.engine.mode == "English":
                        self.set_mode("Avro Phonetic (বাংলা)")
                    self._refresh_status()
                elif event == "ui_mode":
                    self.set_mode(value)
                elif event == "ui_open":
                    self.show_window()
                elif event == "ui_display":
                    if self.display_var.get():
                        self.hide_window()
                    else:
                        self.show_window()
                elif event == "ui_exit":
                    self.disable()
                    self.root.quit()
        except queue.Empty:
            pass
        self.root.after(35, self._drain_events)

    def _make_tray_image(self, enabled):
        color = "#13875a" if enabled else "#8792a3"
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((2, 2, 62, 62), radius=16, fill=color)
        try:
            font = ImageFont.truetype("segoeuib.ttf", 27)
        except OSError:
            font = ImageFont.load_default()
        draw.text((13, 13), "Bn", fill="white", font=font)
        draw.ellipse((45, 45, 60, 60), fill="#22c55e" if enabled else "#d8dee8",
                     outline="white", width=2)
        return image

    def _tray_menu(self):
        return pystray.Menu(
            pystray.MenuItem(lambda _item: f"Typing: {'ON' if self.engine.enabled else 'OFF'}",
                             lambda _icon, _item: self.events.put(("ui_toggle", None))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("English", lambda _icon, _item: self.events.put(("ui_mode", "English")),
                             checked=lambda _item: self.engine.mode == "English", radio=True),
            pystray.MenuItem("Avro Phonetic (বাংলা)",
                             lambda _icon, _item: self.events.put(("ui_mode", "Avro Phonetic (বাংলা)")),
                             checked=lambda _item: self.engine.mode.startswith("Avro"), radio=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Gboard PC", lambda _icon, _item: self.events.put(("ui_open", None)), default=True),
            pystray.MenuItem(lambda _item: "Hide floating keyboard" if self.display_enabled else "Show floating keyboard",
                             lambda _icon, _item: self.events.put(("ui_display", None))),
            pystray.MenuItem("Exit", lambda _icon, _item: self.events.put(("ui_exit", None))),
        )

    def _start_tray(self):
        if not pystray:
            return
        try:
            self.tray = pystray.Icon(APP_NAME, self._make_tray_image(False),
                                     title="Gboard PC — OFF", menu=self._tray_menu())
            self.tray.run_detached()
        except Exception as exc:
            self.events.put(("error", f"Could not start the system tray icon: {exc}"))

    def copy_selection(self):
        try:
            value = self.text.get("sel.first", "sel.last")
        except tk.TclError:
            value = self.text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.hint_var.set("Copied to clipboard.")

    def copy_all(self):
        value = self.text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.hint_var.set("Text copied to clipboard.")

    def save_text(self):
        value = self.text.get("1.0", "end-1c")
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text file", "*.txt")],
                                            initialfile="bangla-text.txt")
        if path:
            with open(path, "w", encoding="utf-8") as stream:
                stream.write(value)
            self.hint_var.set("Saved as a UTF-8 text file.")

    def clear_text(self):
        self.text.delete("1.0", "end")
        self.engine.reset_composition()
        self.hint_var.set("Text box cleared.")

    def run(self):
        self.root.mainloop()
        self.engine.stop()
        if self.tray:
            self.tray.stop()


def main():
    if __import__("sys").platform != "win32":
        raise SystemExit("Gboard PC is a Windows 10/11 app.")
    app = GboardPC()
    app.run()


if __name__ == "__main__":
    main()

