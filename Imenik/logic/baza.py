# logic/baza.py
import sqlite3

class KontaktBaza:
    def __init__(self, db_path="resources/kontakti.db"):
        self.conn = sqlite3.connect(db_path)
        self.kreiraj_tabelu()

    def kreiraj_tabelu(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS kontakti (
                    id INTEGER PRIMARY KEY,
                    ime TEXT NOT NULL,
                    prezime TEXT NOT NULL,
                    pozicija TEXT,
                    telefon TEXT,
                    email TEXT,
                    sektor TEXT,
                    slika TEXT
                )
            ''')

    def dodaj_kontakt(self, ime, prezime, pozicija, telefon, email, sektor, slika):
        with self.conn:
            self.conn.execute("""
                INSERT INTO kontakti (ime, prezime, pozicija, telefon, email, sektor, slika)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (ime, prezime, pozicija, telefon, email, sektor, slika))

    def izmeni_kontakt(self, id_kontakta, ime, prezime, pozicija, telefon, email, sektor):
        with self.conn:
            self.conn.execute("""
                UPDATE kontakti SET ime=?, prezime=?, pozicija=?, telefon=?, email=?, sektor=?
                WHERE id=?""",
                (ime, prezime, pozicija, telefon, email, sektor, id_kontakta))

    def obrisi_kontakt(self, id_kontakta):
        with self.conn:
            self.conn.execute("DELETE FROM kontakti WHERE id=?", (id_kontakta,))

    def imena_kontakata(self):
        cur = self.conn.cursor()
        cur.execute("SELECT ime || ' ' || prezime FROM kontakti")
        return [r[0] for r in cur.fetchall()]

    def kontakt_po_imenu_prezimenu(self, puno_ime):
        cur = self.conn.cursor()
        if " " in puno_ime:
            ime, prezime = puno_ime.split(" ", 1)
        else:
            ime = puno_ime
            prezime = ""
        cur.execute("SELECT * FROM kontakti WHERE ime = ? AND prezime = ?", (ime, prezime))
        return cur.fetchone()

    def kontakti_za_sektor(self, sektor):
        cur = self.conn.cursor()
        if sektor == "Svi sektori":
            cur.execute("SELECT * FROM kontakti")
        else:
            cur.execute("SELECT * FROM kontakti WHERE sektor = ?", (sektor,))
        return cur.fetchall()
