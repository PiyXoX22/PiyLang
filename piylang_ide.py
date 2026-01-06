import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, PhotoImage, simpledialog
import sys, io, os
import threading
from tkinter import simpledialog
from piylang.main import jalankan, PiyLangError  # Sesuaikan path interpretermu

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
root.title("PiyLang IDE v1.0")
root.geometry("1000x700")
root.configure(bg=DARK_BG)

# ================= LOGO =================
try:
    logo = PhotoImage(file="logopylang.png")  # Pastikan ada logo 64x64
    root.iconphoto(False, logo)
except:
    print("Logo tidak ditemukan, lanjut tanpa logo")

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

# ================= SYNTAX HIGHLIGHT =================
keywords = ["cetak","jika","elif","else","selama","ulang","fungsi","kembali","hentikan","lanjutkan","masukan"]
def highlight(event=None):
    editor.tag_remove("keyword","1.0","end")
    editor.tag_remove("string","1.0","end")
    editor.tag_remove("number","1.0","end")
    editor.tag_remove("comment","1.0","end")
    editor.tag_remove("func","1.0","end")
    editor.tag_remove("error","1.0","end")

    text = editor.get("1.0","end-1c").split("\n")
    for i,line in enumerate(text):
        lineno = i+1
        # Comments
        if "#" in line:
            idx = line.find("#")
            editor.tag_add("comment", f"{lineno}.{idx}", f"{lineno}.end")
        # Strings
        start = 0
        while '"' in line[start:]:
            sidx = line.find('"', start)
            eidx = line.find('"', sidx+1)
            if eidx == -1:
                break
            editor.tag_add("string", f"{lineno}.{sidx}", f"{lineno}.{eidx+1}")
            start = eidx+1
        # Keywords
        for kw in keywords:
            idx = line.find(kw)
            while idx != -1:
                editor.tag_add("keyword", f"{lineno}.{idx}", f"{lineno}.{idx+len(kw)}")
                idx = line.find(kw, idx+1)
        # Numbers
        import re
        for match in re.finditer(r'\b\d+\b', line):
            editor.tag_add("number", f"{lineno}.{match.start()}", f"{lineno}.{match.end()}")

editor.tag_config("keyword", foreground=KEYWORD_COLOR)
editor.tag_config("string", foreground=STRING_COLOR)
editor.tag_config("number", foreground=NUMBER_COLOR)
editor.tag_config("comment", foreground=COMMENT_COLOR)
editor.tag_config("func", foreground=FUNC_COLOR)
editor.tag_config("error", foreground=ERROR_COLOR)

editor.bind("<KeyRelease>", highlight)

# ================= LINE NUMBER UPDATE =================
def update_line_numbers(event=None):
    line_numbers.config(state='normal')
    line_numbers.delete("1.0","end")
    i = editor.index("end-1c").split(".")[0]
    lines = "\n".join(str(x) for x in range(1,int(i)))
    line_numbers.insert("1.0", lines)
    line_numbers.config(state='disabled')
editor.bind("<KeyRelease>", update_line_numbers)

# ================= GUI INPUT =================
def gui_input(prompt):
    result = [None]

    def ask():
        result[0] = simpledialog.askstring("PiyLang Input", prompt, parent=root)

    root.after(0, ask)

    # Tunggu sampai user input muncul & selesai
    while result[0] is None:
        root.update()  # biarkan GUI tetap responsive
    return result[0]


# ================= RUN FUNCTION =================
def run_code():
    def task():
        output.delete("1.0","end")
        code = editor.get("1.0","end")
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        highlight()
        try:
            jalankan(code)
            result = sys.stdout.getvalue()
            output.insert("end", result)
            status.config(text="✅ Run successful")
        except PiyLangError as e:
            output.insert("end", f"❌ Error: {e.pesan}\n")
            status.config(text="❌ Error in code")
        except Exception as e:
            output.insert("end", f"🔥 Runtime Error: {e}\n")
            status.config(text="🔥 Runtime Error")
        finally:
            sys.stdout = old_stdout

    threading.Thread(target=task, daemon=True).start()

# ================= TOOLBAR =================
toolbar = tk.Frame(root, bg="#44475a")
toolbar.pack(fill="x")
tk.Button(toolbar, text="▶ Run", command=run_code, bg="#50fa7b").pack(side="left", padx=2, pady=2)
tk.Button(toolbar, text="🗑 Clear Output", command=lambda: output.delete("1.0","end"), bg="#ff5555").pack(side="left", padx=2)
tk.Button(toolbar, text="💾 Save File", command=lambda: save_file(), bg="#f1fa8c").pack(side="left", padx=2)
tk.Button(toolbar, text="📂 Open File", command=lambda: open_file(), bg="#8be9fd").pack(side="left", padx=2)

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
