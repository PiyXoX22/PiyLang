# =====================================
# PIYLANG IDE + INTERPRETER V3 REVISI + MIC VOICE
# =====================================
import cv2
import threading
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import scrolledtext, filedialog, PhotoImage, simpledialog
import sys, io, os, re
import speech_recognition as sr  # untuk voice input

# ================= COLOR SCHEME =================
DARK_BG = "#1e1e1e"
DARK_FG = "#ffffff"
KEYWORD_COLOR = "#ff79c6"
STRING_COLOR = "#f1fa8c"
NUMBER_COLOR = "#8be9fd"
COMMENT_COLOR = "#6272a4"
FUNC_COLOR = "#50fa7b"
ERROR_COLOR = "#ff5555"

# ================= MAIN WINDOW =================
root = tk.Tk()
root.title("PiyLang IDE v3.0")
root.geometry("1000x700")
root.configure(bg=DARK_BG)

# ================= LOGO =================
try:
    logo = PhotoImage(file="logopylang.png")
    root.iconphoto(False, logo)
except:
    pass

# ================= LINE NUMBERS =================
line_numbers = tk.Text(root, width=4, padx=4, takefocus=0, border=0,
                       background="#282a36", foreground="#6272a4",
                       state='disabled', font=("Consolas", 12))
line_numbers.pack(side="left", fill="y")

# ================= EDITOR =================
editor = scrolledtext.ScrolledText(root, wrap="none", font=("Consolas", 12),
                                   undo=True, bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_FG)
editor.pack(side="left", fill="both", expand=True)

# ================= OUTPUT =================
output = scrolledtext.ScrolledText(root, height=12, bg="black", fg="lime", font=("Consolas", 11))
output.pack(fill="x", padx=10, pady=(0,10))

# ================= STATUS BAR =================
status = tk.Label(root, text="Ready", bg="#44475a", fg="#f8f8f2", anchor="w")
status.pack(fill="x")

# ================= KEYWORDS & SNIPPETS =================
KEYWORDS = [
    "jika","atau_jika","kalau_tidak","ulang","selama","fungsi",
    "kembali","berhenti","lanjut","cetak","masukkan","coba","kecuali","import","benar","salah"
]

SNIPPETS = {
    "jika": "jika kondisi:\n    ",
    "atau_jika": "atau_jika kondisi:\n    ",
    "kalau_tidak": "kalau_tidak:\n    ",
    "ulang": "ulang i dari 1 sampai 10:\n    ",
    "selama": "selama kondisi:\n    ",
    "fungsi": "fungsi nama():\n    kembali "
}

# ================= SYNTAX HIGHLIGHT =================
def highlight(event=None):
    editor.tag_remove("keyword","1.0","end")
    editor.tag_remove("string","1.0","end")
    editor.tag_remove("number","1.0","end")
    editor.tag_remove("comment","1.0","end")

    text = editor.get("1.0","end-1c").split("\n")
    for i,line in enumerate(text):
        lineno = i+1
        if "#" in line:
            idx = line.find("#")
            editor.tag_add("comment", f"{lineno}.{idx}", f"{lineno}.end")
        start = 0
        while '"' in line[start:]:
            sidx = line.find('"', start)
            eidx = line.find('"', sidx+1)
            if eidx == -1:
                break
            editor.tag_add("string", f"{lineno}.{sidx}", f"{lineno}.{eidx+1}")
            start = eidx+1
        for kw in KEYWORDS:
            idx = line.find(kw)
            while idx != -1:
                editor.tag_add("keyword", f"{lineno}.{idx}", f"{lineno}.{idx+len(kw)}")
                idx = line.find(kw, idx+1)
        for match in re.finditer(r'\b\d+\b', line):
            editor.tag_add("number", f"{lineno}.{match.start()}", f"{lineno}.{match.end()}")

editor.tag_config("keyword", foreground=KEYWORD_COLOR)
editor.tag_config("string", foreground=STRING_COLOR)
editor.tag_config("number", foreground=NUMBER_COLOR)
editor.tag_config("comment", foreground=COMMENT_COLOR)
editor.tag_config("error", foreground=ERROR_COLOR)

# ================= LINE NUMBERS =================
def update_line_numbers(event=None):
    line_numbers.config(state='normal')
    line_numbers.delete("1.0","end")
    i = editor.index("end-1c").split(".")[0]
    lines = "\n".join(str(x) for x in range(1,int(i)))
    line_numbers.insert("1.0", lines)
    line_numbers.config(state='disabled')

editor.bind("<KeyRelease>", lambda e: [highlight(), update_line_numbers()])

# ================= AUTOCOMPLETE =================
autocomplete_listbox = None
HISTORY = []

def show_autocomplete(suggestions):
    global autocomplete_listbox
    if not suggestions:
        hide_autocomplete()
        return

    if autocomplete_listbox is None:
        autocomplete_listbox = tk.Listbox(root, height=5, bg="#282a36", fg="#f8f8f2",
                                          font=("Consolas", 12), activestyle="none")
        autocomplete_listbox.bind("<Double-1>", lambda e: insert_autocomplete())
        autocomplete_listbox.bind("<FocusOut>", lambda e: hide_autocomplete())
        autocomplete_listbox.bind("<Key>", autocomplete_keypress)
    
    autocomplete_listbox.delete(0, "end")
    for item in suggestions:
        autocomplete_listbox.insert("end", item)
    
    bbox = editor.bbox("insert")
    if bbox:
        x, y, width, height = bbox
        autocomplete_listbox.place(x=x + editor.winfo_rootx() - root.winfo_rootx(),
                                   y=y + height + editor.winfo_rooty() - root.winfo_rooty())
    autocomplete_listbox.selection_set(0)
    autocomplete_listbox.activate(0)
    autocomplete_listbox.focus_set()

def hide_autocomplete():
    global autocomplete_listbox
    if autocomplete_listbox:
        autocomplete_listbox.place_forget()

def insert_autocomplete():
    global autocomplete_listbox
    if autocomplete_listbox is None:
        return
    try:
        sel = autocomplete_listbox.get(autocomplete_listbox.curselection())
    except:
        sel = None
    if sel:
        pos = editor.index("insert")
        line_start = editor.index("insert linestart")
        line_text = editor.get(line_start, pos)
        parts = line_text.split()
        if parts:
            parts[-1] = sel
            new_text = " ".join(parts)
            editor.delete(line_start, pos)
            editor.insert(line_start, new_text)
        hide_autocomplete()

def autocomplete_keypress(event):
    if event.keysym in ["Return","Tab"]:
        insert_autocomplete()
        return "break"
    elif event.keysym == "Up":
        if autocomplete_listbox.curselection():
            idx = autocomplete_listbox.curselection()[0]
            if idx > 0:
                autocomplete_listbox.selection_clear(0, "end")
                autocomplete_listbox.selection_set(idx-1)
                autocomplete_listbox.activate(idx-1)
        return "break"
    elif event.keysym == "Down":
        if autocomplete_listbox.curselection():
            idx = autocomplete_listbox.curselection()[0]
            if idx < autocomplete_listbox.size()-1:
                autocomplete_listbox.selection_clear(0, "end")
                autocomplete_listbox.selection_set(idx+1)
                autocomplete_listbox.activate(idx+1)
        else:
            autocomplete_listbox.selection_set(0)
            autocomplete_listbox.activate(0)
        return "break"
    elif event.keysym == "Escape":
        hide_autocomplete()
        return "break"

def check_autocomplete(event=None):
    pos = editor.index("insert")
    line = editor.get(f"{pos} linestart", pos)
    kata = line.split()[-1] if line.split() else ""
    suggestions = autocomplete_engine(kata)
    show_autocomplete(suggestions)

editor.bind("<KeyRelease>", lambda e: [highlight(), update_line_numbers(), check_autocomplete()])

# ================= AUTOCOMPLETE ENGINE =================
variabel = {}
fungsi = {}

def autocomplete_engine(teks):
    if not teks.strip():
        return []
    kata = teks.split()[-1]
    saran = set()
    for k in KEYWORDS:
        if k.startswith(kata):
            saran.add(SNIPPETS.get(k, k))
    for v in variabel.keys():
        if v.startswith(kata):
            saran.add(v)
    for f in fungsi.keys():
        if f.startswith(kata):
            saran.add(f + "()")
    for h in HISTORY:
        if h.startswith(kata):
            saran.add(h)
    return sorted(saran)

# ================= GUI INPUT DENGAN WEBCAM =================
webcam_on = False
webcam_val = None
webcam_window = None
webcam_cap = None
webcam_label = None

def toggle_webcam():
    global webcam_on, webcam_window, webcam_cap, webcam_label
    if webcam_on:
        webcam_on = False
        if webcam_window:
            webcam_window.destroy()
        if webcam_cap:
            webcam_cap.release()
    else:
        webcam_on = True
        webcam_window = tk.Toplevel(root)
        webcam_window.title("PiyLang Camera Input")
        webcam_label = tk.Label(webcam_window)
        webcam_label.pack()
        webcam_cap = cv2.VideoCapture(0)

        def update_frame():
            if not webcam_on:
                return
            ret, frame = webcam_cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)               # Convert to PIL Image
                imgtk = ImageTk.PhotoImage(image=img)      # Convert to Tkinter image
                webcam_label.imgtk = imgtk
                webcam_label.configure(image=imgtk)
            webcam_label.after(30, update_frame)

        update_frame()

def gui_input(prompt):
    global webcam_val
    if webcam_on:
        val = simpledialog.askstring("PiyLang Input", prompt, parent=root)
        return val
    else:
        return simpledialog.askstring("PiyLang Input", prompt, parent=root)

# ================= INTERPRETER =================
class PiyLangError(Exception):
    def __init__(self, pesan):
        self.pesan = pesan

def jalankan(kode):
    global HISTORY
    baris_baris = kode.split("\n")
    for i, baris in enumerate(baris_baris):
        baris_ke = i + 1
        if baris.strip() and not baris.strip().startswith("#"):
            HISTORY.append(baris.strip())
        if baris.startswith("cetak"):
            isi = baris.replace("cetak", "").strip()
            print(isi)
        if baris.startswith("masukkan"):
            val = gui_input("Input: ")
            variabel["input"] = val

# ================= RUN CODE =================
def run_code():
    def task():
        output.delete("1.0","end")
        code = editor.get("1.0","end")
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            jalankan(code)
            result = sys.stdout.getvalue()
            output.insert("end", result)
            status.config(text="✅ Run successful")
        except Exception as e:
            output.insert("end", f"❌ {e}\n")
            status.config(text="❌ Error")
        finally:
            sys.stdout = old_stdout
    threading.Thread(target=task, daemon=True).start()

# ================= MIC VOICE INPUT =================
mic_on = False
mic_thread = None

VOICE_KEYWORDS = {
    "cetak": "cetak ",
    "fungsi": "fungsi ",
    "jika": "jika ",
    "atau jika": "atau_jika ",
    "kalau tidak": "kalau_tidak",
    "ulang": "ulang ",
    "selama": "selama ",
    "kembali": "kembali ",
    "berhenti": "berhenti",
    "lanjut": "lanjut"
}

def toggle_mic():
    global mic_on, mic_thread
    mic_on = not mic_on
    if mic_on:
        status.config(text="🎤 Mic: ON")
        mic_thread = threading.Thread(target=mic_listener, daemon=True)
        mic_thread.start()
    else:
        status.config(text="🎤 Mic: OFF")

def mic_listener():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    while mic_on:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            text = recognizer.recognize_google(audio, language="id-ID").lower()
            if text:
                kode = parse_voice_to_code(text)
                editor.insert("insert", kode + "\n")
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            output.insert("end", f"❌ Mic error: {e}\n")
            break

def parse_voice_to_code(text):
    for k, v in VOICE_KEYWORDS.items():
        if text.startswith(k):
            sisa = text[len(k):].strip()
            if v.endswith(":"):  # block seperti fungsi/jika/selama
                return v + sisa + ":"
            elif v.endswith(" "):
                if k == "cetak":
                    return f'{v}"{sisa}"'
                return v + sisa
            else:
                return v
    return text

# ================= TOOLBAR =================
toolbar = tk.Frame(root, bg="#44475a")
toolbar.pack(fill="x")
tk.Button(toolbar, text="▶ Run", command=run_code, bg="#50fa7b").pack(side="left", padx=2, pady=2)
tk.Button(toolbar, text="🗑 Clear Output", command=lambda: output.delete("1.0","end"), bg="#ff5555").pack(side="left", padx=2)
tk.Button(toolbar, text="💾 Save File", command=lambda: save_file(), bg="#f1fa8c").pack(side="left", padx=2)
tk.Button(toolbar, text="📂 Open File", command=lambda: open_file(), bg="#8be9fd").pack(side="left", padx=2)
tk.Button(toolbar, text="📷 Webcam On/Off", command=toggle_webcam, bg="#8be9fd").pack(side="left", padx=2)
tk.Button(toolbar, text="🎤 Mic On/Off", command=toggle_mic, bg="#f1fa8c").pack(side="left", padx=2)

# ================= FILE FUNCTIONS =================
def save_file():
    path = filedialog.asksaveasfilename(defaultextension=".piy", filetypes=[("PiyLang files","*.piy")])
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(editor.get("1.0","end"))
        status.config(text=f"💾 Saved to {os.path.basename(path)}")

def open_file():
    path = filedialog.askopenfilename(filetypes=[("PiyLang files","*.piy")])
    if path:
        with open(path, "r", encoding="utf-8") as f:
            editor.delete("1.0","end")
            editor.insert("1.0", f.read())
        highlight()
        update_line_numbers()
        status.config(text=f"📂 Opened {os.path.basename(path)}")

# ================= RUN GUI =================
highlight()
update_line_numbers()
root.mainloop()
