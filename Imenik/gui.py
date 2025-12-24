# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import os
import csv

from logic.baza import KontaktBaza
from logic.sektori import ucitaj_sektore_iz_fajla, upisi_sektor_u_fajl

SEKTORI = ucitaj_sektore_iz_fajla()

class Aplikacija(tk.Tk):
    def __init__(self):
        super().__init__()
        self.iconbitmap("ikonica.ico")
        self.title("Imenik")
        self.geometry("950x600")
        self.configure(bg="white")

        self.baza = KontaktBaza()
        self.slika_putanja = None
        self.selected_sektor = "Svi sektori"

        self.create_widgets()
        self.ucitaj_kontakte_za_sektor()

    def create_widgets(self):
        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.prikaz_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.prikaz_tab, text="Prikaz kontakata")

        frame_sektori = tk.Frame(self.prikaz_tab, bg="#ecf0f1", bd=2, relief=tk.GROOVE)
        frame_sektori.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0), pady=10)

        tk.Label(frame_sektori, text=" Filter po sektoru", bg="#3498db", fg="white", font=("Arial", 12, "bold"),
                 anchor="w").pack(fill=tk.X)

        self.sektor_listbox = tk.Listbox(
            frame_sektori,
            height=10,
            font=("Arial", 11),
            bg="white",
            fg="#2c3e50",
            selectbackground="#2980b9",
            selectforeground="white",
            activestyle="none",
            relief=tk.FLAT,
            bd=0
        )
        self.sektor_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.sektor_listbox.insert(tk.END, "Svi sektori")
        for sektor in SEKTORI:
            self.sektor_listbox.insert(tk.END, sektor)
        self.sektor_listbox.selection_set(0)
        self.sektor_listbox.bind("<<ListboxSelect>>", self.promena_sektora)

        frame_dugmici = tk.Frame(self.prikaz_tab, bg="white")
        frame_dugmici.pack(fill=tk.X, padx=10, pady=(10, 0))

        btn_izvoz_csv = tk.Button(frame_dugmici, text="Izvezi u CSV", command=self.izvezi_u_csv,
                                  bg="#3498db", fg="white", font=("Arial", 10, "bold"))
        btn_izvoz_csv.pack(side=tk.RIGHT, padx=(5, 0))

        # Višestruka polja za pretragu
        frame_pretraga = tk.Frame(self.prikaz_tab, bg="#ecf0f1", bd=2, relief=tk.GROOVE)
        frame_pretraga.pack(fill=tk.X, padx=10, pady=(10, 10))

        tk.Label(frame_pretraga, text=" Pretraga kontakata", bg="#3498db", fg="white",
                 font=("Arial", 12, "bold"), anchor="w").pack(fill=tk.X)

        polja_okvir = tk.Frame(frame_pretraga, bg="#ecf0f1")
        polja_okvir.pack(fill=tk.X, padx=10, pady=10)

        labels = ["Ime", "Prezime", "Telefon", "Email", "Sektor"]
        self.pretraga_polja = {}

        for l in labels:
            frame_polje = tk.Frame(polja_okvir, bg="#ecf0f1")
            frame_polje.pack(side=tk.LEFT, padx=10)

            lbl = tk.Label(frame_polje, text=l + ":", bg="#ecf0f1", font=("Arial", 10))
            lbl.pack(anchor="w")

            e = tk.Entry(frame_polje, font=("Arial", 10), width=14, relief=tk.SOLID, bd=1)
            e.pack(anchor="w")
            e.bind("<KeyRelease>", self.pretrazi_kontakte)
            self.pretraga_polja[l.lower()] = e

        #################################
        self.canvas = tk.Canvas(self.prikaz_tab, bg="#f0f4fa")
        self.scrollbar = ttk.Scrollbar(self.prikaz_tab, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.frame_kontakti = tk.Frame(self.canvas, bg="#f0f4fa")
        self.canvas.create_window((0, 0), window=self.frame_kontakti, anchor="nw", tags="kontakti_frame")

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig("kontakti_frame", width=e.width))
        self.frame_kontakti.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.dodaj_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.dodaj_tab, text="Dodaj kontakt")
        self.create_dodaj_tab()

        self.izmena_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.izmena_tab, text="Izmeni kontakt")

        self.create_izmena_tab()

        self.brisanje_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.brisanje_tab, text="Obriši kontakt")
        self.create_brisanje_tab()

    def promena_sektora(self, event):
        selection = self.sektor_listbox.curselection()
        if selection:
            index = selection[0]
            sektor = self.sektor_listbox.get(index)
            self.selected_sektor = sektor

            # Resetuj sva pretrazna polja
            for e in self.pretraga_polja.values():
                e.delete(0, tk.END)

            # Prikaz kontakata za izabrani sektor
            self.ucitaj_kontakte_za_sektor()

    def ucitaj_kontakte_za_sektor(self):
        for widget in self.frame_kontakti.winfo_children():
            widget.destroy()

        svi_kontakti = self.baza.kontakti_za_sektor(self.selected_sektor)

        if not svi_kontakti:
            tk.Label(self.frame_kontakti, text="Nema kontakata.", bg="#f0f4fa", font=("Arial", 12)).pack(pady=20)
            return

        # Grupisanje po sektoru
        sektorski_kontakti = {}
        for kontakt in svi_kontakti:
            sektor = kontakt[6] or "Nepoznat sektor"
            sektorski_kontakti.setdefault(sektor, []).append(kontakt)

        for sektor, kontakti in sektorski_kontakti.items():
            # Plavi zaglavni red sa imenom sektora
            zaglavni_frame = tk.Frame(self.frame_kontakti, bg="#3498db")
            zaglavni_frame.pack(fill=tk.X, pady=(10, 2))

            zaglavlje = tk.Label(zaglavni_frame, text=" " + sektor.upper(), bg="#3498db", fg="white",
                                 font=("Arial", 12, "bold"), anchor="w", pady=6)
            zaglavlje.pack(fill=tk.X, padx=10)

            for kontakt in kontakti:
                self.prikazi_kontakt_novi(kontakt)

    def prikazi_kontakt_novi(self, kontakt):
        id, ime, prezime, pozicija, telefon, email, sektor, slika = kontakt

        frame_k = tk.Frame(self.frame_kontakti, bg="white", pady=10, padx=10, relief=tk.SOLID, bd=0)
        frame_k.pack(fill=tk.X, padx=10, pady=5)

        sadrzaj = tk.Frame(frame_k, bg="white")
        sadrzaj.pack(fill=tk.X)

        # Slika levo
        if slika and os.path.exists(slika):
            img = Image.open(slika)
            img = img.resize((90, 90), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            slika_labela = tk.Label(sadrzaj, image=photo, bg="white", width=90, height=90)
            slika_labela.image = photo
            slika_labela.pack(side=tk.LEFT, padx=10)
        else:
            slika_labela = tk.Label(sadrzaj, text="Nema slike", bg="white", width=12, height=6, relief=tk.RIDGE)
            slika_labela.pack(side=tk.LEFT, padx=10)

        # Tekst desno od slike
        tekst_frame = tk.Frame(sadrzaj, bg="white")
        tekst_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(tekst_frame, text=f"{ime} {prezime}", bg="white", font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(tekst_frame, text=f"Organizacioni deo: {sektor}", bg="white", font=("Arial", 10)).pack(anchor="w")
        tk.Label(tekst_frame, text=f"Pozicija: {pozicija}", bg="white", font=("Arial", 10)).pack(anchor="w")
        tk.Label(tekst_frame, text=f"Telefon: {telefon}", bg="white", font=("Arial", 10)).pack(anchor="w")
        tk.Label(tekst_frame, text=f"Email: {email}", bg="white", font=("Arial", 10)).pack(anchor="w")

        # ⚠️ Dodaj ovu funkciju unutar prikazi_kontakt_novi da zna za "kontakt"
        def bind_duboko(widget):
            widget.bind("<Button-1>", lambda e: self.prikazi_detalje_kontakta(kontakt))
            for child in widget.winfo_children():
                bind_duboko(child)

        bind_duboko(frame_k)

    def prikazi_kontakt(self, kontakt, frame, kol):
        id, ime, prezime, poz, tel, email, sektor, slika = kontakt
        frame_k = tk.Frame(frame, bd=1, relief=tk.SOLID, bg="white", padx=10, pady=10)
        frame_k.grid(row=0, column=kol, padx=5, pady=5, sticky="n")

        if slika and os.path.exists(slika):
            img = Image.open(slika)
            img.thumbnail((120, 120))
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(frame_k, image=photo, bg="white")
            lbl.image = photo
            lbl.pack()
        else:
            lbl = tk.Label(frame_k, text="Nema slike", bg="white")
            lbl.pack()

        tk.Label(frame_k, text=f"{ime.upper()} {prezime.upper()}", font=("Arial", 11, "bold"), bg="white").pack(
            pady=(5, 0))
        tk.Label(frame_k, text=poz, font=("Arial", 10), bg="white").pack()
        tk.Label(frame_k, text=tel, font=("Arial", 10), bg="white").pack()
        tk.Label(frame_k, text=email, font=("Arial", 10), bg="white").pack()
        tk.Label(frame_k, text=sektor, font=("Arial", 10, "italic"), bg="white").pack()

    def create_dodaj_tab(self):
        frame = tk.Frame(self.dodaj_tab, bg="#ecf0f1", bd=2, relief=tk.GROOVE)
        frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(frame, text=" Dodaj novi kontakt", bg="#3498db", fg="white",
                 font=("Arial", 12, "bold"), anchor="w").pack(fill=tk.X)

        polja_frame = tk.Frame(frame, bg="#ecf0f1")
        polja_frame.pack(padx=20, pady=20)

        labels = ["Ime", "Prezime", "Pozicija", "Telefon", "Email", "Sektor"]
        self.unos_dodaj = {}

        for i, l in enumerate(labels):
            tk.Label(polja_frame, text=l + ":", bg="#ecf0f1", font=("Arial", 11)).grid(row=i, column=0, sticky="e",
                                                                                       padx=10, pady=8)
            if l == "Sektor":
                cb = ttk.Combobox(polja_frame, values=SEKTORI, state="readonly")
                cb.grid(row=i, column=1, sticky="w", padx=10, pady=8)
                cb.current(0)
                self.unos_dodaj[l] = cb

                btn_novi_sektor = tk.Button(polja_frame, text="Dodaj novi sektor", command=self.dodaj_novi_sektor_dodaj)
                btn_novi_sektor.grid(row=i, column=2, padx=10, pady=8)
            else:
                e = tk.Entry(polja_frame, font=("Arial", 11), width=30)
                e.grid(row=i, column=1, sticky="w", padx=10, pady=8)
                self.unos_dodaj[l] = e

        self.dodaj_sliku_btn = tk.Button(frame, text="Izaberi sliku", command=self.izaberi_sliku_dodaj, bg="#7f8c8d",
                                         fg="white")
        self.dodaj_sliku_btn.pack(pady=10)

        self.dodaj_btn = tk.Button(frame, text="Dodaj kontakt", command=self.dodaj_kontakt,
                                   bg="#2ecc71", fg="white", font=("Arial", 11, "bold"))
        self.dodaj_btn.pack(pady=10)

    def dodaj_novi_sektor_dodaj(self):
        novi_sektor = simpledialog.askstring("Novi sektor", "Unesite naziv novog sektora:", parent=self)
        if novi_sektor:
            novi_sektor = novi_sektor.strip()
            if novi_sektor and novi_sektor not in SEKTORI:
                SEKTORI.append(novi_sektor)
                upisi_sektor_u_fajl(novi_sektor)
                self.unos_dodaj["Sektor"]['values'] = SEKTORI
                self.unos_dodaj["Sektor"].set(novi_sektor)
                self.osvezi_filter_sektora()

                # ⬇️ Osveži izmenu karticu ako postoji
                if hasattr(self, "unos_izmena") and "Sektor" in self.unos_izmena:
                    self.unos_izmena["Sektor"]["values"] = SEKTORI
            else:
                messagebox.showwarning("Upozorenje", "Taj sektor već postoji ili je nevažeći naziv.")

    def dodaj_novi_sektor_izmena(self):
        novi_sektor = simpledialog.askstring("Novi sektor", "Unesite naziv novog sektora:", parent=self)
        if novi_sektor:
            novi_sektor = novi_sektor.strip()
            if novi_sektor and novi_sektor not in SEKTORI:
                SEKTORI.append(novi_sektor)
                upisi_sektor_u_fajl(novi_sektor)
                self.unos_izmena["Sektor"]['values'] = SEKTORI
                self.unos_izmena["Sektor"].set(novi_sektor)
                self.osvezi_filter_sektora()

                # ⬇️ Osveži i "Dodaj kontakt" karticu
                if hasattr(self, "unos_dodaj") and "Sektor" in self.unos_dodaj:
                    self.unos_dodaj["Sektor"]["values"] = SEKTORI
            else:
                messagebox.showwarning("Upozorenje", "Taj sektor već postoji ili je nevažeći naziv.")

    def osvezi_filter_sektora(self):
        # Osvežavanje filtera na levom panelu u prikazu kontakata
        self.sektor_listbox.delete(0, tk.END)
        self.sektor_listbox.insert(tk.END, "Svi sektori")
        for sektor in SEKTORI:
            self.sektor_listbox.insert(tk.END, sektor)
        self.sektor_listbox.selection_clear(0, tk.END)
        self.sektor_listbox.selection_set(0)
        self.selected_sektor = "Svi sektori"
        self.ucitaj_kontakte_za_sektor()

    def izaberi_sliku_dodaj(self):
        putanja = filedialog.askopenfilename(
            title="Izaberi sliku",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if putanja:
            self.slika_putanja = putanja
            messagebox.showinfo("Slika", f"Izabrana slika: {putanja}")

    def dodaj_kontakt(self):
        podaci = {k: v.get() if not isinstance(v, ttk.Combobox) else v.get() for k, v in self.unos_dodaj.items()}

        for kljuc, vrednost in podaci.items():
            if not vrednost.strip():
                messagebox.showwarning("Greška", f"Polje '{kljuc}' je obavezno.")
                return

        if not self.slika_putanja:
            messagebox.showwarning("Greška", "Morate izabrati sliku za kontakt.")
            return

        try:
            self.baza.dodaj_kontakt(
                podaci["Ime"], podaci["Prezime"], podaci["Pozicija"],
                podaci["Telefon"], podaci["Email"], podaci["Sektor"],
                self.slika_putanja
            )
            messagebox.showinfo("Uspeh", "Kontakt je dodat.")
            self.ocisti_polja_dodaj()
            self.ucitaj_kontakte_za_sektor()
            self.osvezi_kontakte_izmena()

            # ⬇️ Osveži i listu za brisanje
            if hasattr(self, "combo_brisanje"):
                self.combo_brisanje['values'] = self.baza.imena_kontakata()

        except Exception as e:
            messagebox.showerror("Greška", f"Greška prilikom dodavanja: {e}")

    def ocisti_polja_dodaj(self):
        for v in self.unos_dodaj.values():
            if isinstance(v, ttk.Combobox):
                v.current(0)
            else:
                v.delete(0, tk.END)
        self.slika_putanja = None

    def create_izmena_tab(self):
        frame = tk.Frame(self.izmena_tab, bg="#ecf0f1", bd=2, relief=tk.GROOVE)
        frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(frame, text=" Izmeni kontakt", bg="#3498db", fg="white",
                 font=("Arial", 12, "bold"), anchor="w").pack(fill=tk.X)

        polja_frame = tk.Frame(frame, bg="#ecf0f1")
        polja_frame.pack(padx=20, pady=20)

        labels = ["Izaberi kontakt", "Ime", "Prezime", "Pozicija", "Telefon", "Email", "Sektor"]
        self.unos_izmena = {}

        for i, l in enumerate(labels):
            tk.Label(polja_frame, text=l + ":", bg="#ecf0f1", font=("Arial", 11)).grid(row=i, column=0, sticky="e",
                                                                                       padx=10, pady=8)

            if l == "Izaberi kontakt":
                cb = ttk.Combobox(polja_frame, values=self.baza.imena_kontakata(), state="readonly", width=30)
                cb.grid(row=i, column=1, sticky="w", padx=10, pady=8)
                cb.bind("<<ComboboxSelected>>", self.ucitaj_kontakt_za_izmenu)
                self.unos_izmena[l] = cb

            elif l == "Sektor":
                cb = ttk.Combobox(polja_frame, values=SEKTORI, state="readonly", width=28)
                cb.grid(row=i, column=1, sticky="w", padx=10, pady=8)
                self.unos_izmena[l] = cb

                btn_novi_sektor = tk.Button(polja_frame, text="Dodaj novi sektor",
                                            command=self.dodaj_novi_sektor_izmena)
                btn_novi_sektor.grid(row=i, column=2, padx=10, pady=8)

            else:
                e = tk.Entry(polja_frame, font=("Arial", 11), width=30)
                e.grid(row=i, column=1, sticky="w", padx=10, pady=8)
                self.unos_izmena[l] = e

        self.izmeni_btn = tk.Button(frame, text="Sačuvaj izmene", command=self.sacuvaj_izmene,
                                    bg="#f39c12", fg="white", font=("Arial", 11, "bold"))
        self.izmeni_btn.pack(pady=10)

    def osvezi_kontakte_izmena(self):
        combo = self.unos_izmena.get("Izaberi kontakt")
        if combo:
            combo['values'] = self.baza.imena_kontakata()
            combo.set('')

    def ucitaj_kontakt_za_izmenu(self, event):
        puno_ime = self.unos_izmena["Izaberi kontakt"].get()
        if not puno_ime:
            return
        kontakt = self.baza.kontakt_po_imenu_prezimenu(puno_ime)
        if not kontakt:
            messagebox.showwarning("Greška", "Kontakt nije pronađen.")
            return

        _, ime, prezime, poz, tel, email, sektor, _ = kontakt

        self.unos_izmena["Ime"].delete(0, tk.END)
        self.unos_izmena["Ime"].insert(0, ime)

        self.unos_izmena["Prezime"].delete(0, tk.END)
        self.unos_izmena["Prezime"].insert(0, prezime)

        self.unos_izmena["Pozicija"].delete(0, tk.END)
        self.unos_izmena["Pozicija"].insert(0, poz)

        self.unos_izmena["Telefon"].delete(0, tk.END)
        self.unos_izmena["Telefon"].insert(0, tel)

        self.unos_izmena["Email"].delete(0, tk.END)
        self.unos_izmena["Email"].insert(0, email)

        self.unos_izmena["Sektor"].set(sektor)

    def pretrazi_kontakte(self, event=None):
        for widget in self.frame_kontakti.winfo_children():
            widget.destroy()

        # Uzimamo sve kontakte za trenutno izabrani sektor (ili sve ako je "Svi sektori")
        svi_kontakti = self.baza.kontakti_za_sektor(self.selected_sektor)
        filtrirani = []

        # Uzimamo tekst iz pretrage
        kriterijumi = {
            "ime": self.pretraga_polja["ime"].get().lower(),
            "prezime": self.pretraga_polja["prezime"].get().lower(),
            "telefon": self.pretraga_polja["telefon"].get().lower(),
            "email": self.pretraga_polja["email"].get().lower(),
            "sektor": self.pretraga_polja["sektor"].get().lower(),
        }

        # Ako su sva polja prazna, prikaži kao ucitaj_kontakte_za_sektor (tj. svi izabrani sektor)
        if all(v == "" for v in kriterijumi.values()):
            self.ucitaj_kontakte_za_sektor()
            return

        # Filtriraj kontakte
        for k in svi_kontakti:
            id, ime, prezime, poz, tel, email, sektor, slika = k
            if (
                    kriterijumi["ime"] in ime.lower()
                    and kriterijumi["prezime"] in prezime.lower()
                    and kriterijumi["telefon"] in (tel or "").lower()
                    and kriterijumi["email"] in (email or "").lower()
                    and kriterijumi["sektor"] in (sektor or "").lower()
            ):
                filtrirani.append(k)

        if not filtrirani:
            tk.Label(self.frame_kontakti, text="Nema rezultata za zadatu pretragu.", bg="#f0f4fa",
                     font=("Arial", 12)).pack(pady=20)
            return

        # Grupisi filtrirane kontakte po sektoru
        sektorski_kontakti = {}
        for kontakt in filtrirani:
            sektor = kontakt[6] or "Nepoznat sektor"
            sektorski_kontakti.setdefault(sektor, []).append(kontakt)

        # Prikaz po sektoru sa zaglavljem
        for sektor, kontakti in sektorski_kontakti.items():
            zaglavni_frame = tk.Frame(self.frame_kontakti, bg="#3498db")
            zaglavni_frame.pack(fill=tk.X, pady=(10, 2))

            zaglavlje = tk.Label(zaglavni_frame, text=" " + sektor.upper(), bg="#3498db", fg="white",
                                 font=("Arial", 12, "bold"), anchor="w", pady=6)
            zaglavlje.pack(fill=tk.X, padx=10)

            for kontakt in kontakti:
                self.prikazi_kontakt_novi(kontakt)

    def sacuvaj_izmene(self):
        puno_ime = self.unos_izmena["Izaberi kontakt"].get()
        if not puno_ime:
            messagebox.showwarning("Greška", "Izaberite kontakt za izmenu.")
            return

        kontakt = self.baza.kontakt_po_imenu_prezimenu(puno_ime)
        if not kontakt:
            messagebox.showwarning("Greška", "Kontakt nije pronađen.")
            return

        id_kontakta = kontakt[0]

        ime = self.unos_izmena["Ime"].get()
        prezime = self.unos_izmena["Prezime"].get()
        pozicija = self.unos_izmena["Pozicija"].get()
        telefon = self.unos_izmena["Telefon"].get()
        email = self.unos_izmena["Email"].get()
        sektor = self.unos_izmena["Sektor"].get()

        # ✅ Validacija svih polja
        sva_polja = [ime, prezime, pozicija, telefon, email, sektor]
        nazivi = ["Ime", "Prezime", "Pozicija", "Telefon", "Email", "Sektor"]

        for naziv, vrednost in zip(nazivi, sva_polja):
            if not vrednost.strip():
                messagebox.showwarning("Greška", f"Polje '{naziv}' je obavezno.")
                return

        try:
            self.baza.izmeni_kontakt(id_kontakta, ime, prezime, pozicija, telefon, email, sektor)
            messagebox.showinfo("Uspeh", "Kontakt je izmenjen.")
            self.ucitaj_kontakte_za_sektor()
            self.osvezi_kontakte_izmena()
        except Exception as e:
            messagebox.showerror("Greška", f"Greška prilikom izmene: {e}")

    def create_brisanje_tab(self):
        frame = tk.Frame(self.brisanje_tab, bg="#ecf0f1", bd=2, relief=tk.GROOVE)
        frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(frame, text=" Obriši kontakt", bg="#3498db", fg="white",
                 font=("Arial", 12, "bold"), anchor="w").pack(fill=tk.X)

        inner = tk.Frame(frame, bg="#ecf0f1")
        inner.pack(padx=20, pady=20)

        tk.Label(inner, text="Izaberite kontakt za brisanje:", bg="#ecf0f1", font=("Arial", 11)).grid(row=0, column=0,
                                                                                                      padx=10, pady=10,
                                                                                                      sticky="e")

        self.combo_brisanje = ttk.Combobox(inner, values=self.baza.imena_kontakata(), state="readonly", width=30)
        self.combo_brisanje.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        btn_obrisi = tk.Button(frame, text="Obriši kontakt", command=self.obrisi_kontakt,
                               bg="#e74c3c", fg="white", font=("Arial", 11, "bold"))
        btn_obrisi.pack(pady=10)

    def obrisi_kontakt(self):
        puno_ime = self.combo_brisanje.get()
        if not puno_ime:
            messagebox.showwarning("Upozorenje", "Niste izabrali kontakt za brisanje.")
            return

        potvrda = messagebox.askyesno("Potvrda", f"Da li ste sigurni da želite da obrišete kontakt: {puno_ime}?")
        if not potvrda:
            return

        kontakt = self.baza.kontakt_po_imenu_prezimenu(puno_ime)
        if not kontakt:
            messagebox.showerror("Greška", "Kontakt nije pronađen u bazi.")
            return

        try:
            self.baza.obrisi_kontakt(kontakt[0])
            messagebox.showinfo("Uspeh", "Kontakt je obrisan.")
            self.ucitaj_kontakte_za_sektor()
            self.osvezi_kontakte_izmena()
            self.combo_brisanje['values'] = self.baza.imena_kontakata()
            self.combo_brisanje.set('')
        except Exception as e:
            messagebox.showerror("Greška", f"Greška prilikom brisanja: {e}")

    def izvezi_u_csv(self):
        kontakti = self.baza.kontakti_za_sektor("Svi sektori")

        if not kontakti:
            messagebox.showinfo("Izvoz", "Nema kontakata za izvoz.")
            return

        fajl = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV fajlovi", "*.csv")],
            title="Izaberi lokaciju za čuvanje"
        )

        if not fajl:
            return

        try:
            with open(fajl, mode="w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Ime", "Prezime", "Pozicija", "Telefon", "Email", "Sektor"])

                for k in kontakti:
                    writer.writerow([k[1], k[2], k[3], k[4], k[5], k[6]])

            messagebox.showinfo("Uspeh", f"Kontakti su uspešno izvezeni u:\n{fajl}")

        except Exception as e:
            messagebox.showerror("Greška", f"Greška pri izvozu: {e}")

    def prikazi_detalje_kontakta(self, kontakt):
        id, ime, prezime, pozicija, telefon, email, sektor, slika = kontakt

        detalji = tk.Toplevel(self)
        detalji.title(f"Detalji kontakta – {ime} {prezime}")
        detalji.configure(bg="white")
        detalji.geometry("400x500")

        # Slika
        if slika and os.path.exists(slika):
            img = Image.open(slika)
            img = img.resize((150, 150), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            lbl_slika = tk.Label(detalji, image=photo, bg="white")
            lbl_slika.image = photo
            lbl_slika.pack(pady=15)
        else:
            lbl_slika = tk.Label(detalji, text="Nema slike", width=20, height=10, bg="#ecf0f1", relief=tk.RIDGE)
            lbl_slika.pack(pady=15)

        # Podaci
        def info_red(label, value):
            frame = tk.Frame(detalji, bg="white")
            frame.pack(fill=tk.X, padx=30, pady=5)
            tk.Label(frame, text=label + ":", width=12, anchor="w", font=("Arial", 10, "bold"), bg="white").pack(
                side=tk.LEFT)
            tk.Label(frame, text=value, anchor="w", font=("Arial", 10), bg="white").pack(side=tk.LEFT)

        info_red("Ime", ime)
        info_red("Prezime", prezime)
        info_red("Pozicija", pozicija)
        info_red("Telefon", telefon)
        info_red("Email", email)
        info_red("Sektor", sektor)

        # Zatvori dugme
        tk.Button(detalji, text="Zatvori", command=detalji.destroy, bg="#d35400", fg="white",
                  font=("Arial", 10, "bold")).pack(pady=20)

