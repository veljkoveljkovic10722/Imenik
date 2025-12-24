# logic/sektori.py
import os

SEKTORI_FAJL = "resources/sektori.txt"

def ucitaj_sektore_iz_fajla():
    if not os.path.exists(SEKTORI_FAJL):
        with open(SEKTORI_FAJL, "w") as f:
            f.write("IT\nMarketing\nProdaja\n")
    with open(SEKTORI_FAJL, "r") as f:
        return [linija.strip() for linija in f if linija.strip()]

def upisi_sektor_u_fajl(sektor):
    with open(SEKTORI_FAJL, "a") as f:
        f.write(f"{sektor}\n")
