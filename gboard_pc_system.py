"""GBoard PC typing helper prototype for Windows 10/11."""
import ctypes
from ctypes import wintypes
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from avro_support import roman_to_bangla

DEFAULTS = {
    "teh":"the","adn":"and","taht":"that","thier":"their","recieve":"receive",
    "beleive":"believe","definately":"definitely","seperate":"separate",
    "becuase":"because","freind":"friend","wierd":"weird","occured":"occurred",
    "untill":"until","doesnt":"doesn't","dont":"don't","cant":"can't",
    "wont":"won't","isnt":"isn't","im":"I'm","ive":"I've","youre":"you're",
    "theyre":"they're","thats":"that's","whats":"what's","helllo":"hello",
    "helo":"hello","hwo":"how","waht":"what","whta":"what","goood":"good",
    "thnaks":"thanks","thankyou":"thank you","alot":"a lot"
}
IS_WINDOWS = sys.platform == "win32"
WH_KEYBOARD_LL, WM_KEYDOWN, WM_SYSKEYDOWN, WM_QUIT = 13, 0x100, 0x104, 0x12
LLKHF_INJECTED = 0x10
VK_BACK, VK_SPACE, VK_RETURN, VK_TAB = 0x08, 0x20, 0x0D, 0x09
VK_ESCAPE, VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN, VK_DELETE = 0x1B, 0x25, 0x26, 0x27, 0x28, 0x2E
INPUT_KEYBOARD, KEYEVENTF_KEYUP, KEYEVENTF_UNICODE = 1, 2, 4
if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
else:
    user32 = kernel32 = None

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_=[("vkCode",wintypes.DWORD),("scanCode",wintypes.DWORD),("flags",wintypes.DWORD),("time",wintypes.DWORD),("dwExtraInfo",ctypes.c_size_t)]
class KEYBDINPUT(ctypes.Structure):
    _fields_=[("wVk",wintypes.WORD),("wScan",wintypes.WORD),("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),("dwExtraInfo",ctypes.c_size_t)]
class _INPUTUNION(ctypes.Union):
    _fields_=[("ki",KEYBDINPUT)]
class INPUT(ctypes.Structure):
    _anonymous_=("u",)
    _fields_=[("type",wintypes.DWORD),("u",_INPUTUNION)]

def correction_for(word, bangla_mode=False):
    if not word: return None
    if bangla_mode:
        out=roman_to_bangla(word)
        return out if out != word else None
    value=DEFAULTS.get(word.lower())
    if not value: return None
    if word.isupper(): return value.upper()
    if word[:1].isupper(): return value[:1].upper()+value[1:]
    return value

class GlobalHook:
    def __init__(self, events):
        self.events=events; self.enabled=False; self.bangla=False; self.word=""
        self.thread=None; self.thread_id=0; self.hook=None; self.callback_ref=None
    def start(self):
        if not IS_WINDOWS:
            self.events.put(("status","Windows is required.")); return
        if self.enabled: return
        self.enabled=True
        self.thread=threading.Thread(target=self._run,daemon=True); self.thread.start()
    def stop(self):
        self.enabled=False; self.word=""
        if IS_WINDOWS and self.thread_id:
            user32.PostThreadMessageW(self.thread_id,WM_QUIT,0,0)
        self.events.put(("status","Disabled"))
    def _api(self):
        user32.SetWindowsHookExW.argtypes=[ctypes.c_int,ctypes.c_void_p,wintypes.HINSTANCE,wintypes.DWORD]
        user32.SetWindowsHookExW.restype=ctypes.c_void_p
        user32.CallNextHookEx.argtypes=[ctypes.c_void_p,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM]
        user32.CallNextHookEx.restype=ctypes.c_ssize_t
        user32.UnhookWindowsHookEx.argtypes=[ctypes.c_void_p]
        user32.GetMessageW.argtypes=[ctypes.POINTER(wintypes.MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT]
        user32.GetMessageW.restype=ctypes.c_int
        kernel32.GetModuleHandleW.argtypes=[wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype=wintypes.HMODULE
        kernel32.GetCurrentThreadId.restype=wintypes.DWORD
        user32.SendInput.argtypes=[wintypes.UINT,ctypes.POINTER(INPUT),ctypes.c_int]
        user32.SendInput.restype=wintypes.UINT
    def _key(self,vk,up=False):
        i=INPUT(type=INPUT_KEYBOARD,ki=KEYBDINPUT(wVk=vk,dwFlags=KEYEVENTF_KEYUP if up else 0))
        user32.SendInput(1,ctypes.byref(i),ctypes.sizeof(INPUT))
    def _unicode(self,s):
        for c in s:
            for flags in (KEYEVENTF_UNICODE,KEYEVENTF_UNICODE|KEYEVENTF_KEYUP):
                i=INPUT(type=INPUT_KEYBOARD,ki=KEYBDINPUT(wScan=ord(c),dwFlags=flags))
                user32.SendInput(1,ctypes.byref(i),ctypes.sizeof(INPUT))
    def _char(self,vk,scan):
        state=(ctypes.c_ubyte*256)()
        if not user32.GetKeyboardState(ctypes.byref(state)): return ""
        out=ctypes.create_unicode_buffer(8)
        user32.ToUnicodeEx.argtypes=[wintypes.UINT,wintypes.UINT,ctypes.c_void_p,wintypes.LPWSTR,ctypes.c_int,wintypes.UINT,ctypes.c_void_p]
        n=user32.ToUnicodeEx(vk,scan,ctypes.byref(state),out,len(out),0,user32.GetKeyboardLayout(0))
        return out.value if n==1 else ""
    def _replace(self,old,new):
        for _ in old: self._key(VK_BACK); self._key(VK_BACK,True)
        self._unicode(new)
    def _correct(self):
        old=self.word; new=correction_for(old,self.bangla)
        if new and new != old:
            self._replace(old,new); self.events.put(("status",f"{old} → {new}"))
        self.word=""
    def _run(self):
        self._api(); self.thread_id=kernel32.GetCurrentThreadId()
        Proc=ctypes.WINFUNCTYPE(ctypes.c_ssize_t,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM)
        def cb(n,w,l):
            if n>=0 and w in (WM_KEYDOWN,WM_SYSKEYDOWN):
                try:
                    k=ctypes.cast(l,ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                    if not k.flags & LLKHF_INJECTED:
                        vk=int(k.vkCode)
                        self.events.put(("activity",vk))
                        if vk==VK_SPACE:
                            self._correct()
                        elif vk in (VK_RETURN,VK_TAB): self.word=""
                        elif vk==VK_BACK: self.word=self.word[:-1]
                        elif vk in (VK_ESCAPE,VK_LEFT,VK_UP,VK_RIGHT,VK_DOWN,VK_DELETE): self.word=""
                        else:
                            c=self._char(vk,int(k.scanCode))
                            if c and c.isalpha() and c.isascii(): self.word=(self.word+c)[-50:]
                            elif c and c.isprintable() and not c.isspace():
                                if self.word: self._correct()
                                self.word=""
                except Exception: pass
            return user32.CallNextHookEx(self.hook,n,w,l)
        self.callback_ref=Proc(cb)
        self.hook=user32.SetWindowsHookExW(WH_KEYBOARD_LL,self.callback_ref,kernel32.GetModuleHandleW(None),0)
        if not self.hook:
            self.enabled=False; self.events.put(("status",f"Hook failed (Windows error {ctypes.get_last_error()})")); return
        self.events.put(("status","Applied — test in Notepad and Word"))
        msg=wintypes.MSG()
        try:
            while self.enabled and user32.GetMessageW(ctypes.byref(msg),None,0,0)>0:
                user32.TranslateMessage(ctypes.byref(msg)); user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            if self.hook: user32.UnhookWindowsHookEx(self.hook)
            self.hook=None; self.callback_ref=None

class App:
    def __init__(self,root):
        self.root=root; self.events=queue.Queue(); self.hook=GlobalHook(self.events)
        self.mode=tk.StringVar(value="On Display"); self.bangla=tk.BooleanVar(value=False)
        root.title("GBoard PC + Avro Bangla"); root.geometry("500x430"); root.minsize(470,400)
        root.configure(bg="#f5f6fa")
        tk.Label(root,text="Gboard PC",font=("Segoe UI",24,"bold"),bg="#f5f6fa",fg="#202124").pack(anchor="w",padx=24,pady=(22,2))
        tk.Label(root,text="Windows typing helper · English + Roman Bangla",font=("Segoe UI",10),bg="#f5f6fa",fg="#5f6368").pack(anchor="w",padx=25)
        panel=tk.Frame(root,bg="white",highlightbackground="#dadce0",highlightthickness=1); panel.pack(fill="x",padx=22,pady=18)
        tk.Label(panel,text="Floating keyboard",font=("Segoe UI",11,"bold"),bg="white").pack(anchor="w",padx=15,pady=(12,4))
        ttk.Radiobutton(panel,text="On Display (show while typing)",variable=self.mode,value="On Display").pack(anchor="w",padx=15,pady=3)
        ttk.Radiobutton(panel,text="Non-display (hide keyboard)",variable=self.mode,value="Non-display").pack(anchor="w",padx=15,pady=3)
        ttk.Checkbutton(panel,text="Avro Bangla mode (ami → আমি)",variable=self.bangla,command=self.set_bangla).pack(anchor="w",padx=15,pady=(7,14))
        row=tk.Frame(root,bg="#f5f6fa"); row.pack(fill="x",padx=22)
        ttk.Button(row,text="Apply",command=self.apply).pack(side="left",expand=True,fill="x",ipady=7,padx=(0,6))
        ttk.Button(row,text="Disable",command=self.disable).pack(side="left",expand=True,fill="x",ipady=7,padx=(6,0))
        self.status=tk.StringVar(value="Disabled — choose options and click Apply")
        tk.Label(root,textvariable=self.status,wraplength=440,justify="left",bg="#f5f6fa",fg="#3c4043").pack(anchor="w",padx=25,pady=15)
        tk.Label(root,text="Prototype: pause before passwords. Not an official Google product.",font=("Segoe UI",8),bg="#f5f6fa",fg="#777").pack(anchor="w",padx=25)
        self.float=None; self.hide_job=None; self.root.after(80,self.poll); root.protocol("WM_DELETE_WINDOW",self.close)
    def set_bangla(self): self.hook.bangla=self.bangla.get()
    def apply(self):
        self.set_bangla(); self.hook.start()
    def disable(self):
        self.hook.stop(); self.hide_float()
    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=="status": self.status.set(value)
                elif kind=="activity":
                    if self.mode.get()=="On Display": self.show_float(value)
        except queue.Empty: pass
        self.root.after(80,self.poll)
    def show_float(self,vk):
        if self.float is None or not self.float.winfo_exists():
            self.float=tk.Toplevel(self.root); self.float.overrideredirect(True); self.float.attributes("-topmost",True)
            self.float.configure(bg="#202124")
            self.float_label=tk.Label(self.float,text="⌨  Gboard PC",font=("Segoe UI",11),bg="#202124",fg="white",padx=16,pady=9)
            self.float_label.pack()
        self.float_label.config(text=f"⌨  Typing…  ({vk})")
        self.float.geometry(f"+{max(0,self.root.winfo_screenwidth()-250)}+{max(0,self.root.winfo_screenheight()-100)}")
        if self.hide_job: self.root.after_cancel(self.hide_job)
        self.hide_job=self.root.after(1300,self.hide_float)
    def hide_float(self):
        if self.hide_job:
            try:self.root.after_cancel(self.hide_job)
            except Exception:pass
            self.hide_job=None
        if self.float is not None:
            try:self.float.destroy()
            except Exception:pass
            self.float=None
    def close(self):
        self.disable(); self.root.destroy()

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()
