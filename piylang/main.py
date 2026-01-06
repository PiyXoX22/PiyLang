# =====================================
# PIYLANG INTERPRETER (FULL FEATURE VERSI INDO REVISI)
# =====================================

# ===================== GUI INPUT =====================
GUI_INPUT = None  # nanti bisa diassign dari IDE

variabel = {}
fungsi = {}

# ===================== EXCEPTIONS =====================
class KembaliException(Exception):
    def __init__(self, nilai):
        self.nilai = nilai

class BerhentiException(Exception):
    pass

class LanjutException(Exception):
    pass

class PiyLangError(Exception):
    def __init__(self, pesan, baris=None):
        super().__init__(pesan)
        self.pesan = pesan
        self.baris = baris

    def tampilkan(self):
        lokasi = f" (Baris {self.baris})" if self.baris else ""
        print(f"❌ Error PiyLang{lokasi}: {self.pesan}")

# ===================== NORMALISASI =====================
def normalisasi(expr):
    return (
        expr.replace(" dan ", " and ")
            .replace(" atau ", " or ")
            .replace(" bukan ", " not ")
            .replace(" benar", " True")
            .replace(" salah", " False")
    )

# ===================== EVALUATOR EKSPRESI =====================
import re

def hitung(expr, baris):
    expr = normalisasi(expr).strip()

    # ---------- BUILTIN ----------
    if expr.startswith("panjang(") and expr.endswith(")"):
        isi = expr[8:-1].strip()
        return len(hitung(isi, baris))

    # ---------- INTEGER ----------
    if expr.isdigit():
        return int(expr)

    # ---------- STRING ----------
    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]

    # ---------- LIST ----------
    if expr.startswith("[") and expr.endswith("]"):
        isi = expr[1:-1].strip()
        if not isi:
            return []
        return [hitung(x.strip(), baris) for x in isi.split(",")]

    # ---------- INDEX LIST ----------
    if "[" in expr and expr.endswith("]"):
        nama, idx = expr.split("[", 1)
        idx = idx[:-1]
        if nama.strip() not in variabel:
            raise PiyLangError("Variabel tidak dikenal", baris)
        return variabel[nama.strip()][hitung(idx, baris)]

    # ---------- VARIABEL ----------
    if expr in variabel:
        return variabel[expr]

    # ---------- OPERATOR PERBANDINGAN ----------
    ops = ["==", "!=", ">=", "<=", ">", "<"]
    for op in ops:
        pattern = rf"(.+){re.escape(op)}(.+)"
        m = re.match(pattern, expr)
        if m:
            a = hitung(m.group(1).strip(), baris)
            b = hitung(m.group(2).strip(), baris)

            # konversi otomatis ke angka jika memungkinkan
            def ubah_ke_angka(x):
                try:
                    if isinstance(x, (int, float)):
                        return x
                    if "." in str(x):
                        return float(x)
                    return int(x)
                except:
                    return str(x)

            a = ubah_ke_angka(a)
            b = ubah_ke_angka(b)

            return {
                "==": a == b,
                "!=": a != b,
                ">=": a >= b,
                "<=": a <= b,
                ">": a > b,
                "<": a < b
            }[op]

    # ---------- ARITMATIKA / KONKATENASI STRING ----------
    for op in ["+", "-", "*", "/", "%"]:
        if op in expr:
            a, b = expr.split(op, 1)
            a = hitung(a.strip(), baris)
            b = hitung(b.strip(), baris)
            if op == "+":
                return str(a) + str(b)  # selalu aman gabung string/angka
            if op == "-": return float(a) - float(b)
            if op == "*": return float(a) * float(b)
            if op == "/": return float(a) / float(b)
            if op == "%": return float(a) % float(b)

    raise PiyLangError("Ekspresi tidak dikenali", baris)

# ===================== INTERPRETER =====================
def jalankan(kode):
    baris_baris = kode.split("\n")
    i = 0

    while i < len(baris_baris):
        baris = baris_baris[i].rstrip()
        baris_ke = i + 1

        if not baris.strip() or baris.strip().startswith("#"):
            i += 1
            continue

        # ---------- IMPORT ----------
        if baris.startswith("import"):
            modul = baris.replace("import", "").strip()
            globals()[modul] = __import__(modul)
            i += 1
            continue

        # ---------- FUNGSI ----------
        if baris.startswith("fungsi"):
            nama = baris.split()[1].split("(")[0]
            params = baris[baris.find("(")+1:baris.find(")")].split(",")
            params = [p.strip() for p in params if p.strip()]

            i += 1
            blok = []
            while i < len(baris_baris) and baris_baris[i].startswith("    "):
                blok.append(baris_baris[i][4:])
                i += 1

            fungsi[nama] = (params, blok)
            continue

        # ---------- KEMBALI ----------
        if baris.startswith("kembali"):
            nilai = hitung(baris.replace("kembali", "").strip(), baris_ke)
            raise KembaliException(nilai)

        # ---------- BERHENTI / LANJUT ----------
        if baris.strip() == "berhenti":
            raise BerhentiException()
        if baris.strip() == "lanjut":
            raise LanjutException()

        # ---------- ULANG ----------
        if baris.startswith("ulang"):
            _, var, _, awal, _, akhir = baris.replace(":", "").split()
            awal = hitung(awal, baris_ke)
            akhir = hitung(akhir, baris_ke)

            i += 1
            blok = []
            while i < len(baris_baris) and baris_baris[i].startswith("    "):
                blok.append(baris_baris[i][4:])
                i += 1

            for n in range(awal, akhir + 1):
                variabel[var] = n
                try:
                    jalankan("\n".join(blok))
                except LanjutException:
                    continue
                except BerhentiException:
                    break
            continue

        # ---------- SELAMA ----------
        if baris.startswith("selama"):
            kondisi = baris.replace("selama", "").replace(":", "").strip()

            i += 1
            blok = []
            while i < len(baris_baris) and baris_baris[i].startswith("    "):
                blok.append(baris_baris[i][4:])
                i += 1

            while hitung(kondisi, baris_ke):
                try:
                    jalankan("\n".join(blok))
                except LanjutException:
                    continue
                except BerhentiException:
                    break
            continue

        # ---------- JIKA / ATAU_JIKA / KALAU_TIDAK ----------
        if baris.startswith("jika") or baris.startswith("atau_jika") or baris.startswith("kalau_tidak"):
            def ambil_blok(idx):
                blok = []
                while idx < len(baris_baris) and baris_baris[idx].startswith("    "):
                    blok.append(baris_baris[idx][4:])
                    idx += 1
                return blok, idx

            kondisi_aktif = False
            while i < len(baris_baris):
                baris = baris_baris[i].rstrip()
                if baris.startswith("jika") or baris.startswith("atau_jika"):
                    kondisi = hitung(baris.replace("jika", "").replace("atau_jika", "").replace(":", ""), i+1)
                    i += 1
                    blok, i = ambil_blok(i)
                    if kondisi and not kondisi_aktif:
                        jalankan("\n".join(blok))
                        kondisi_aktif = True
                elif baris.startswith("kalau_tidak"):
                    i += 1
                    blok, i = ambil_blok(i)
                    if not kondisi_aktif:
                        jalankan("\n".join(blok))
                    break
                else:
                    break
            continue

        # ---------- CETAK ----------
        if baris.startswith("cetak"):
            isi = baris.replace("cetak", "").strip()
            print(hitung(isi, baris_ke))

        # ---------- MASUKKAN ----------
        elif "=" in baris and "masukkan" in baris:
            nama, prompt = baris.split("=", 1)
            prompt = prompt.replace("masukkan", "").strip().strip('"')
            
            if GUI_INPUT:
                val = GUI_INPUT(prompt)
            else:
                val = input(prompt + " ")
            
            # otomatis convert ke angka jika bisa
            try:
                if "." in val:
                    val = float(val)
                else:
                    val = int(val)
            except:
                pass  # tetap string jika gagal

            variabel[nama.strip()] = val

        # ---------- COBA / KECUALI ----------
        elif baris.startswith("coba"):
            i += 1
            blok_coba = []
            while i < len(baris_baris) and baris_baris[i].startswith("    "):
                blok_coba.append(baris_baris[i][4:])
                i += 1

            # cek apakah ada kecuali setelahnya
            blok_kecuali = []
            if i < len(baris_baris) and baris_baris[i].startswith("kecuali"):
                i += 1
                while i < len(baris_baris) and baris_baris[i].startswith("    "):
                    blok_kecuali.append(baris_baris[i][4:])
                    i += 1

            try:
                jalankan("\n".join(blok_coba))
            except Exception as e:
                variabel["error"] = str(e)
                if blok_kecuali:
                    jalankan("\n".join(blok_kecuali))
            continue

        # ---------- PANGGIL FUNGSI ----------
        elif "(" in baris and ")" in baris:
            target = None
            call = baris

            if "=" in baris:
                target, call = baris.split("=", 1)
                target = target.strip()
                call = call.strip()

            nama = call.split("(")[0]
            args = call[call.find("(")+1:call.find(")")].split(",")

            if nama not in fungsi:
                raise PiyLangError("Fungsi tidak ditemukan", baris_ke)

            params, blok = fungsi[nama]
            backup = variabel.copy()

            try:
                for p, a in zip(params, args):
                    variabel[p] = hitung(a.strip(), baris_ke)
                hasil = jalankan("\n".join(blok))
                if target:
                    variabel[target] = hasil
            except KembaliException as k:
                variabel.update(backup)
                if target:
                    variabel[target] = k.nilai

        # ---------- ASSIGN ----------
        elif "=" in baris:
            nama, nilai = baris.split("=", 1)
            variabel[nama.strip()] = hitung(nilai.strip(), baris_ke)

        i += 1

# ===================== ENTRY POINT =====================
def jalankan_file(file):
    with open(file, encoding="utf-8") as f:
        jalankan(f.read())

def main():
    import sys
    if len(sys.argv) < 2:
        print("Cara pakai: piy file.piy")
        return
    jalankan_file(sys.argv[1])

if __name__ == "__main__":
    main()
