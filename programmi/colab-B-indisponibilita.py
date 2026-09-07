# =====================================================================
#  INDISPONIBILITÀ — crea il file da far compilare alle persone
#  Da incollare in una cella di Google Colab e avviare con il tasto ▶
#  Modifica solo la parte "DATI DA COMPILARE" qui sotto.
# =====================================================================

# ----------------------- DATI DA COMPILARE ---------------------------
# Si scrivono a parole, come nelle schede.

MESE_E_ANNO_DI_PARTENZA = """novembre 2026"""
QUANTI_MESI = 12

NOMI_DELLE_PERSONE = """
LEONI, ROSSI M, ROSSI L, GALLINA, RUSSO, VERDI, HU,
MARINI, CONTI A, CONTI S, FERRARI, GRECO, SANNA, LI
"""

# Gli stessi codici usati nel file dell'orario. «nessuno» se non ce ne sono.
CODICI_IN_PIU_TESTO = """
Gn = guardia notte in ALTRA SEDE, blocca tutto il giorno stesso e tutto il
     giorno successivo. È una notte svolta da un'altra struttura.
C = congresso, blocca tutto il giorno
"""

# Le parti della giornata dell'orario, nello stesso ordine del file dei turni.
PARTI_DELLA_GIORNATA_TESTO = """MAT, POM, NOTTE"""

NOME_FILE = "Indisponibilita_Nov2026_Ott2027.xlsx"

# --------------------- FINE DATI DA COMPILARE ------------------------


# ------------- lettura di quello che hai scritto qui sopra ------------
import re, unicodedata

MESI = {"gennaio":1,"febbraio":2,"marzo":3,"aprile":4,"maggio":5,"giugno":6,
        "luglio":7,"agosto":8,"settembre":9,"ottobre":10,"novembre":11,"dicembre":12}

class Problema(Exception):
    pass

def _pulisci(t):
    t = unicodedata.normalize("NFC", str(t))
    return t.replace("\u2014", "-").replace("\u2013", "-").replace("\u2019", "'")

# ---------------------------------------------------------------- mese e anno
def leggi_mese(testo):
    t = _pulisci(testo).strip().lower()
    m = re.search(r"([a-zàèéìòù]+)\D*(\d{4})", t)
    if not m or m.group(1) not in MESI:
        raise Problema(f"non capisco il mese e l'anno da «{testo.strip()}». "
                       f"Scrivili così: novembre 2026")
    return MESI[m.group(1)], int(m.group(2)), m.group(1)

# ---------------------------------------------------------------- attività
def leggi_attivita(testo):
    """Una attività per riga: NOME - 2 turni: MAT, POM"""
    fuori, avvisi = [], []
    for riga in _pulisci(testo).split("\n"):
        r = riga.strip().strip("-•").strip()
        if not r:
            continue
        # tutto quello che sta dopo i due punti sono le etichette dei turni
        if ":" not in r:
            raise Problema(f"nella riga «{r}» non trovo i due punti. "
                           f"Scrivila così: STANZA 23 - 2 turni: MAT, POM")
        testa, coda = r.split(":", 1)
        turni = [x.strip().upper() for x in re.split(r"[,;/]| e ", coda) if x.strip()]
        if not turni:
            raise Problema(f"nella riga «{r}» non trovo i nomi dei turni")
        # il nome è quello che precede il trattino, o l'indicazione «N turni»
        nome = re.split(r"\s*-\s*|\s+\d+\s*turn", testa)[0].strip()
        if not nome:
            raise Problema(f"nella riga «{r}» non trovo il nome dell'attività")
        dichiarati = re.search(r"(\d+)\s*turn", testa)
        if dichiarati and int(dichiarati.group(1)) != len(turni):
            avvisi.append(f"«{nome}»: dichiari {dichiarati.group(1)} turni ma ne elenchi "
                          f"{len(turni)} ({', '.join(turni)}). Uso quelli elencati.")
        fuori.append((nome.upper(), turni))
    if not fuori:
        raise Problema("non ho trovato nessuna attività")
    return fuori, avvisi

# ---------------------------------------------------------------- persone
def leggi_persone(testo):
    nomi = [n.strip() for n in re.split(r"[,;\n]", _pulisci(testo)) if n.strip()]
    nomi = [n.upper() for n in nomi]
    if not nomi:
        raise Problema("non ho trovato nessun nome")
    doppi = {n for n in nomi if nomi.count(n) > 1}
    if doppi:
        raise Problema("questi nomi compaiono due volte: " + ", ".join(sorted(doppi)))
    return nomi

# ---------------------------------------------------------------- codici
DURATE = [
    ("giorno+dopo", r"giorno\s+success|giorno\s+dopo|due\s+giorni"),
    ("mattina",     r"\bmattin"),
    ("pomeriggio",  r"\bpomerigg"),
    ("notte",       r"\bnott"),
    ("giorno",      r"tutto\s+il\s+giorno|intera\s+giornata|tutta\s+la\s+giornata"),
]

def leggi_codici(testo):
    t = _pulisci(testo).strip()
    if not t or t.lower() in ("nessuno", "nessun", "no", "-"):
        return [], []
    # una voce comincia quando una riga inizia con «SIGLA =» oppure «SIGLA :»
    voci, corrente = [], None
    for riga in t.split("\n"):
        m = re.match(r"\s*([A-Za-z][A-Za-z0-9]{0,3})\s*[=:]\s*(.*)$", riga)
        if m:
            if corrente: voci.append(corrente)
            corrente = [m.group(1), m.group(2).strip()]
        elif corrente:
            corrente[1] += " " + riga.strip()
    if corrente: voci.append(corrente)
    if not voci:
        raise Problema("non riconosco nessun codice. Scrivili così, uno per riga: "
                       "Gn = guardia notte, blocca tutto il giorno stesso e "
                       "tutto il giorno successivo")

    fuori, avvisi = [], []
    for sigla, descr in voci:
        d = re.sub(r"\s+", " ", descr).strip().rstrip(".")
        basso = d.lower()
        # si guarda solo la parte che segue «blocca», se c'è: il resto è il motivo
        pezzo = basso.split("blocca", 1)[1] if "blocca" in basso else basso
        durata = None
        for nome, schema in DURATE:
            if re.search(schema, pezzo):
                durata = nome
                break
        if durata is None:
            raise Problema(
                f"del codice «{sigla}» non capisco che cosa blocca. Aggiungi alla "
                f"descrizione una di queste espressioni: «blocca la mattina», "
                f"«blocca il pomeriggio», «blocca la notte», «blocca tutto il giorno», "
                f"«blocca tutto il giorno stesso e tutto il giorno successivo».")
        # ambiguità: più indicazioni diverse nella stessa descrizione
        trovate = [n for n, s in DURATE if re.search(s, pezzo)]
        if len(trovate) > 1 and not (trovate[0] == "giorno+dopo" and set(trovate) <= {"giorno+dopo", "giorno", "notte"}):
            avvisi.append(f"«{sigla}»: la descrizione contiene più indicazioni "
                          f"({', '.join(trovate)}). Ho usato «{durata}».")
        fuori.append((sigla, d, durata))
    sigle = [s for s, _, _ in fuori]
    doppie = {s for s in sigle if sigle.count(s) > 1}
    if doppie:
        raise Problema("questi codici compaiono due volte: " + ", ".join(sorted(doppie)))
    scontro = set(sigle) & {"X", "Xm", "Xp", "Xn"}
    if scontro:
        raise Problema("questi codici esistono già di base e non vanno ridichiarati: "
                       + ", ".join(sorted(scontro)))
    return fuori, avvisi


try:
    _nm, ANNO, _nome_mese = leggi_mese(MESE_E_ANNO_DI_PARTENZA)
    MESE = _nome_mese.upper()
    PERSONE = leggi_persone(NOMI_DELLE_PERSONE)
    CODICI_IN_PIU, _av = leggi_codici(CODICI_IN_PIU_TESTO)
    PARTI_DELLA_GIORNATA = [x.strip().upper() for x in
                            re.split(r"[,;\n]", PARTI_DELLA_GIORNATA_TESTO) if x.strip()]
    if not PARTI_DELLA_GIORNATA:
        raise Problema("non ho trovato le parti della giornata")
except Problema as _e:
    print("NON POSSO PROCEDERE:", _e)
    raise SystemExit
for _a in _av:
    print("Avviso:", _a)

import calendar, re
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

NOMI = ["", "Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
        "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
GG = ["lunedì","martedì","mercoledì","giovedì","venerdì","sabato","domenica"]

def _sigle(parti):
    n = 1
    while True:
        prov = {p: p[:n].lower() for p in parti}
        if len(set(prov.values())) == len(parti) or n >= max(len(p) for p in parti):
            return prov
        n += 1
LETTERE = _sigle(PARTI_DELLA_GIORNATA)
NOMI_PARTE = {"MAT": "la mattina", "MATTINA": "la mattina", "POM": "il pomeriggio",
              "POMERIGGIO": "il pomeriggio", "SERA": "la sera", "NOTTE": "la notte",
              "PRANZO": "a pranzo", "GIORNO": "di giorno"}
BASE = [("X", "non disponibile tutto il giorno", "giorno")]
for _p in PARTI_DELLA_GIORNATA:
    BASE.append(("X" + LETTERE[_p],
                 "non disponibile " + NOMI_PARTE.get(_p, "in " + _p),
                 "parte:" + _p))
LEGENDA = BASE + CODICI_IN_PIU
CODICI = [c for c, _, _ in LEGENDA]
PROLUNGATI = [c for c, _, q in LEGENDA if q == "giorno+dopo"]

ISTRUZIONI = [
    "1. Cerca il foglio del mese giusto (in basso) e la colonna con il tuo nome.",
    "2. Sulla riga del giorno, scegli il codice dal menu a tendina.",
    "3. I giorni in cui sei disponibile vanno lasciati VUOTI.",
    "",
    "Esempi:",
    "  se il giorno 3 sei assente solo la mattina, scrivi Xm sulla riga del giorno 3",
    "  se il giorno 10 sei assente tutto il giorno, scrivi X sulla riga del giorno 10",
]
for c in PROLUNGATI:
    ISTRUZIONI += ["",
        f"ATTENZIONE al codice {c}: blocca anche il giorno successivo.",
        f"  Va segnato SOLO sul giorno in cui comincia. Se sei in turno il giorno 4,",
        f"  scrivi {c} sulla riga del 4 e NON scrivere niente sulla riga del 5:",
        "  il blocco del giorno dopo è già compreso nel significato del codice."]

# Excel ammette al massimo 255 caratteri nel messaggio di aiuto della tendina:
# oltre quel limite considera il file danneggiato e lo ripara all'apertura.
AIUTO = " | ".join(f"{c} = {s}" for c, s, _ in LEGENDA)
if len(AIUTO) > 250:
    AIUTO = ("Codici ammessi: " + ", ".join(CODICI) +
             ". Il significato di ciascuno è nella legenda, a destra del foglio.")

CAL = "Calibri"
f_n = Font(name=CAL, size=11); f_b = Font(name=CAL, size=11, bold=True)
f_p = Font(name=CAL, size=10)
we   = PatternFill("solid", fgColor="DDEBF7")
gr   = PatternFill("solid", fgColor="D9D9D9")
comp = PatternFill("solid", fgColor="FFF2CC")
mid  = Alignment(horizontal="center", vertical="center", wrap_text=False)
sx   = Alignment(horizontal="left",   vertical="center", wrap_text=False)
bordo = Border(*[Side(style="thin", color="BFBFBF")] * 4)

wb = Workbook(); wb.remove(wb.active)
P0 = 3
P1 = P0 + len(PERSONE) - 1
C_LEG = P1 + 2
LP0, LP1 = get_column_letter(P0), get_column_letter(P1)

anno, mese = ANNO, _nm
for _ in range(QUANTI_MESI):
    ng = calendar.monthrange(anno, mese)[1]
    R0, R1 = 4, 4 + ng - 1
    ws = wb.create_sheet(f"{NOMI[mese]} {anno}")
    ws["A1"], ws["B1"], ws["A2"] = NOMI[mese].upper(), anno, mese
    ws.cell(row=2, column=P0, value="INDISPONIBILITÀ")
    ws.merge_cells(start_row=2, start_column=P0, end_row=2, end_column=P1)
    ws.cell(row=3, column=1, value="GIORNO"); ws.cell(row=3, column=2, value="DATA")
    for i, p in enumerate(PERSONE):
        ws.cell(row=3, column=P0 + i, value=p)
    for i in range(ng):
        r = R0 + i
        ws.cell(row=r, column=1, value='=CHOOSE(WEEKDAY(DATE($B$1,$A$2,B%d),2),"%s")'
                % (r, '","'.join(GG)))
        ws.cell(row=r, column=2, value=i + 1)

    for r in (1, 2, 3):
        for c in range(1, P1 + 1):
            cel = ws.cell(row=r, column=c); cel.font = f_b; cel.alignment = mid
            if r == 3: cel.fill = gr; cel.border = bordo
    for i in range(ng):
        r = R0 + i; fine = calendar.weekday(anno, mese, i + 1) >= 5
        for c in range(1, P1 + 1):
            cel = ws.cell(row=r, column=c)
            cel.border = bordo; cel.alignment = mid; cel.font = f_n
            cel.fill = gr if c <= 2 else (we if fine else comp)
            if fine and c <= 2: cel.fill = we

    ws.cell(row=2, column=C_LEG, value="LEGENDA DEI CODICI").font = f_b
    ws.merge_cells(start_row=2, start_column=C_LEG, end_row=2, end_column=C_LEG + 1)
    ws.cell(row=3, column=C_LEG, value="CODICE").font = f_b
    ws.cell(row=3, column=C_LEG + 1, value="SIGNIFICATO").font = f_b
    for c in (C_LEG, C_LEG + 1):
        ws.cell(row=3, column=c).fill = gr; ws.cell(row=3, column=c).border = bordo
    for i, (c, sig, _) in enumerate(LEGENDA):
        a = ws.cell(row=4 + i, column=C_LEG, value=c); a.font = f_b
        a.alignment = mid; a.border = bordo
        b = ws.cell(row=4 + i, column=C_LEG + 1, value=sig); b.font = f_n
        b.alignment = sx; b.border = bordo
    r_ist = 4 + len(LEGENDA) + 2
    ws.cell(row=r_ist, column=C_LEG, value="COME COMPILARE").font = f_b
    for i, riga in enumerate(ISTRUZIONI):
        ws.cell(row=r_ist + 1 + i, column=C_LEG, value=riga).font = f_p

    def largh(testi, extra=2, minimo=6):
        return max(minimo, max((len(str(t)) for t in testi), default=0) + extra)
    ws.column_dimensions["A"].width = largh(GG)
    ws.column_dimensions["B"].width = 6
    for i, p in enumerate(PERSONE):
        ws.column_dimensions[get_column_letter(P0 + i)].width = largh([p])
    ws.column_dimensions[get_column_letter(C_LEG)].width = largh(["CODICE"] + CODICI)
    ws.column_dimensions[get_column_letter(C_LEG + 1)].width = largh(
        [s for _, s, _ in LEGENDA] + ISTRUZIONI)
    ws.freeze_panes = "C4"

    dv = DataValidation(type="list", formula1='"' + ",".join(CODICI) + '"',
                        allow_blank=True, showErrorMessage=True, showInputMessage=True)
    dv.errorTitle = "Codice non ammesso"
    dv.error = "Codice non ammesso: seleziona un valore dall'elenco"
    dv.promptTitle = "Codici ammessi"
    dv.prompt = AIUTO
    ws.add_data_validation(dv); dv.add(f"{LP0}{R0}:{LP1}{R1}")

    # protezione: si blocca tutto tranne l'area da compilare
    for row in ws.iter_rows(min_row=1, max_row=r_ist + len(ISTRUZIONI) + 2,
                            min_col=1, max_col=C_LEG + 1):
        for cel in row:
            cel.protection = Protection(locked=True)
    for r in range(R0, R1 + 1):
        for c in range(P0, P1 + 1):
            ws.cell(row=r, column=c).protection = Protection(locked=False)
    ws.protection.sheet = True
    # le quattro azioni che devono restare PERMESSE (False = non vietata)
    ws.protection.selectLockedCells = False
    ws.protection.selectUnlockedCells = False
    ws.protection.formatColumns = False
    ws.protection.formatRows = False

    mese += 1
    if mese > 12: mese, anno = 1, anno + 1

wb.save(NOME_FILE)

# ---------------- pulizia di una parte che fa "riparare" il file --------------
# openpyxl scrive dentro il file una sezione accessoria (docProps/custom.xml)
# lasciata vuota. Excel la considera un difetto e all'apertura avvisa che il file
# è danneggiato e lo ripara. Non tocca le formule, ma spaventa e basta.
# Qui la si toglie insieme ai due riferimenti che la richiamano.
import zipfile, os, re
def _togli_custom_props(percorso):
    tmp = percorso + ".tmp"
    with zipfile.ZipFile(percorso) as z:
        dati = {n: z.read(n) for n in z.namelist()}
    if "docProps/custom.xml" not in dati:
        return False
    del dati["docProps/custom.xml"]
    dati["_rels/.rels"] = re.sub(
        r'<Relationship[^>]*custom-properties[^>]*/>', '',
        dati["_rels/.rels"].decode()).encode()
    dati["[Content_Types].xml"] = re.sub(
        r'<Override[^>]*docProps/custom\.xml[^>]*/>', '',
        dati["[Content_Types].xml"].decode()).encode()
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in dati.items():
            z.writestr(n, d)
    os.replace(tmp, percorso)
    return True
_pulito = _togli_custom_props(NOME_FILE)

# ------------------------- VERIFICHE ---------------------------------
v = load_workbook(NOME_FILE)
def esito(t, ok, extra=""):
    print(("  OK   " if ok else "  ERRORE ") + t + ((" — " + extra) if extra else ""))

print("=== VERIFICHE SUL FILE SALVATO ===")
print(("  OK   sezione accessoria vuota rimossa" if _pulito
       else "  OK   nessuna sezione accessoria da rimuovere")
      + " (è una causa nota dell'avviso di riparazione di Excel)")
esito(f"fogli creati: {len(v.sheetnames)}", len(v.sheetnames) == QUANTI_MESI,
      v.sheetnames[0] + " … " + v.sheetnames[-1])
righe_ok, primo_ok, nomi_ok, prot_ok, opz_ok, dv_ok, pwd_ok = ([] for _ in range(7))
rif = None
for nome in v.sheetnames:
    w = v[nome]; a, m = w["B1"].value, w["A2"].value
    ng = calendar.monthrange(a, m)[1]
    r = 4
    while w.cell(row=r, column=2).value is not None: r += 1
    righe_ok.append(r - 4 == ng)
    primo_ok.append(str(w["A4"].value).startswith("=CHOOSE"))
    n = [w.cell(row=3, column=c).value for c in range(P0, P1 + 1)]
    if rif is None: rif = n
    nomi_ok.append(n == rif)
    p = w.protection
    prot_ok.append(p.sheet)
    pwd_ok.append(p.password is None)
    opz_ok.append(not p.selectLockedCells and not p.selectUnlockedCells
                  and not p.formatColumns and not p.formatRows)
    d = list(w.data_validations.dataValidation)
    dv_ok.append(len(d) == 1 and d[0].formula1 == '"' + ",".join(CODICI) + '"')
    esito(f"{nome}: {ng} giorni, primo = {calendar.day_name[calendar.weekday(a,m,1)]}",
          righe_ok[-1] and primo_ok[-1]) if nome in (v.sheetnames[0], v.sheetnames[-1]) else None
esito("tutti i mesi hanno il numero di giorni giusto", all(righe_ok))
esito("giorno della settimana calcolato con formula in tutti i fogli", all(primo_ok))
esito("nomi delle persone identici e nella stessa posizione", all(nomi_ok))
esito(f"tendina con i soli codici {', '.join(CODICI)}", all(dv_ok))
esito("protezione attiva su tutti i fogli", all(prot_ok))
esito("nessuna password su nessun foglio", all(pwd_ok))
esito("permesso selezionare, compilare, allargare colonne e righe", all(opz_ok))
w0 = v[v.sheetnames[0]]
esito("celle da compilare sbloccate",
      not w0.cell(row=4, column=P0).protection.locked)
esito("celle di giorno e data bloccate", w0["A4"].protection.locked)
esito("nessuna attività o turno nel file",
      all(w.cell(row=3, column=c).value in (None, "GIORNO", "DATA") or
          w.cell(row=3, column=c).value in PERSONE or c >= C_LEG
          for w in [w0] for c in range(1, C_LEG + 2)))
d0 = list(w.data_validations.dataValidation)[0] if list(w.data_validations.dataValidation) else None
esito(f"messaggio di aiuto entro i 255 caratteri di Excel: {len(d0.prompt or '')}",
      d0 is not None and len(d0.prompt or "") <= 255)
esito(f"messaggio di errore entro i 255 caratteri: {len(d0.error or '')}",
      d0 is not None and len(d0.error or "") <= 255)
esito("nessun testo a capo",
      not any(c.alignment.wrap_text for w in [w0] for row in w.iter_rows() for c in row))

print()
print("APRI IL FILE E PROVA QUESTO: clicca su una cella sotto un nome e scrivi.")
print("Se non riesci nemmeno a selezionarla, le opzioni della protezione sono sbagliate.")

try:
    from google.colab import files
    files.download(NOME_FILE)
except Exception:
    print("\n(fuori da Colab: il file è stato salvato come", NOME_FILE + ")")
