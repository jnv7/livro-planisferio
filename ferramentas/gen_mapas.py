# -*- coding: utf-8 -*-
"""
Gera os mapas do livro a partir de UM único ficheiro base:
  ferramentas/mundo-base.svg
  "Blank world map, Equal Earth projection", por Justinkunimune
  (Wikimedia Commons, CC0). Projeção de áreas iguais — não subdimensiona
  o hemisfério sul.

Produz:
  mapas/mundo.svg                                   continentes + oceanos
  mapas/{africa,america,asia,europa,oceania}.svg    um por continente,
                                                    recortado e rotulado

Correr a partir da raiz do projeto:  python3 ferramentas/gen_mapas.py

Afinação:
  OVERRIDES  — reposiciona rótulos de país nos mapas de continente
  CONT_LABELS / OCEANOS — rótulos do mapa-mundo
  CLIP       — janela de recorte de cada continente
(coordenadas no sistema do SVG base: x ≈ -166..166, y ≈ -95..95,
 com o NORTE em y NEGATIVO)
"""
import re, json, math, os

BASE = "ferramentas/mundo-base.svg"
OUT  = "mapas"

# --- paleta (a mesma do livro-europa) ----------------------------------------
PAPER    = "#FAF7F0"
LAND_OFF = "#E7E1D3"
INK      = "#1F2421"
FONT     = 'font-family:"Work Sans","Helvetica Neue",Arial,sans-serif;'

CONT_INFO = {   # ordem só para iteração
    "america": ("América", "#7B2D3B"),
    "europa":  ("Europa",  "#2C5F7C"),
    "africa":  ("África",   "#C9932E"),
    "asia":    ("Ásia",     "#3B6B47"),
    "oceania": ("Oceânia",  "#9A6534"),
}
ANTARTIDA_FILL = "#AEC3CD"

# alpha-2 -> alpha-3 para os territórios que no ficheiro base só têm classe A3
A2A3_EXTRA = {
    "fo":"FRO","gi":"GIB","im":"IMN","je":"JEY","gg":"GGY","ax":"ALD","ps":"PSX",
    "hk":"HKG","mo":"MAC","gl":"GRL","pr":"PRI","bm":"BMU","aw":"ABW","cw":"CUW",
    "ky":"CYM","pf":"PYF","nc":"NCL","gu":"GUM","ck":"COK",
}

# --- mapa-mundo: rótulos de continente e de oceano  (x, y) -------------------
CONT_LABELS = {
    "america": (-92,  6),
    "europa":  (  6, -58),
    "africa":  ( 14,  12),
    "asia":    ( 98, -36),
    "oceania": (133,  34),
}
OCEANOS = [   # (texto, x, y, tamanho)
    ("OCEANO\nPACÍFICO",         -140,  6, 6.0),
    ("OCEANO\nPACÍFICO",          152, 14, 6.0),
    ("OCEANO\nATLÂNTICO",         -38, -2, 5.2),
    ("OCEANO\nATLÂNTICO",         -24,-48, 4.6),
    ("OCEANO\nÍNDICO",             70,-16, 5.4),
    ("MAR GLACIAL ÁRTICO",       -78,-72, 3.8),
    ("MAR GLACIAL ANTÁRTICO",     -4, 66, 4.2),
]

# --- recorte de cada continente  (x0, y0, x1, y1) ---------------------------
CLIP = {
    "europa":  (-28, -80,  52, -40),
    "africa":  (-28, -52,  62,  48),
    "asia":    ( 22, -74, 148,  12),
    "america": (-166,-90,   2,  60),
    "oceania": ( 92, -24, 202,  64),
}
# territórios que não entram no mapa do continente (mantêm o cartão)
EXCLUI_MAPA = {"america": set(), "europa": set(), "africa": set(),
               "asia": set(), "oceania": set()}

# países que RECEBEM O NOME no mapa (os restantes levam número + legenda).
# lista por continente; se vazio, decide-se pelo tamanho.
NOMEADOS = {
    "america": {"ca","us","mx","br","ar","cl","pe","bo","co","ve","gl","py","ec","uy","gy","sr"},
    "europa":  {"pt","es","fr","de","it","gb","ie","no","se","fi","pl","ua","by","ro","ru","is"},
    "africa":  {"dz","ly","eg","ml","ne","td","sd","ss","et","so","cd","cg","ao","na","za","bw",
                "zm","zw","mz","tz","ke","ng","cm","cf","ma","mr","gn","gh","ci","sn","mg"},
    "asia":    {"tr","sa","ir","iq","sy","kz","uz","tm","af","pk","in","cn","mn","mm","th","vn",
                "id","ph","my","jp","kp","kr","np","ye","om","bd","la","kh"},
    "oceania": {"au","nz","pg","sb","fj","vu"},
}

# --- ajustes manuais de rótulos nos mapas de continente --------------------
#   iso: (dx, dy)   empurra o rótulo (nome) ou o número
OVERRIDES = {
    "ru": (16, 4), "us": (-8, 6), "cl": (-4, 0),
    "no": (-6, 9), "ie": (-5, 1), "es": (0, 5), "pt": (-2, 0),
    "se": (2, 2), "eg": (2, -2), "cn": (-6, 6),
    "ca": (0, 8), "br": (-4, 4), "au": (0, 6),
    "cd": (-4, -10), "ao": (-2, 6), "kr": (2, 4), "jp": (4, 0),
    "cm": (-4, -2), "cf": (6, 2),
}
# territórios "grandes" que preferimos numerar (nome poluiria o mapa)
NAO_NOMEAR = {"gy", "sr"}

WRAP_DX = 331.0    # deslocação para juntar as ilhas a leste da antimeridiana

# nomes curtos para o mapa (o cartão mantém o nome completo)
CURTO = {
    "va": "Vaticano", "ba": "Bósnia", "mk": "Macedónia N.",
    "cd": "R. D. Congo", "cf": "Rep. Centro-Afr.", "do": "Rep. Dominicana",
    "kn": "S. Cristóvão e Neves", "vc": "S. Vicente e Gr.", "ae": "Emirados A. U.",
    "gq": "Guiné Eq.", "cg": "Congo", "cz": "Chéquia",
}

# =============================================================================
src = open(BASE, encoding="utf-8").read()

a2a3 = {}
for a3, a2 in re.findall(r'<g class="([A-Z]{3}) ([A-Z]{2})"', src):
    a2a3[a2.lower()] = a3
a2a3.update(A2A3_EXTRA)

# --- índice de geometria por alpha-3 (path id) ------------------------------
GEO = {}   # a3 -> {"pts":[(x,y)..], "circle":(cx,cy) | None}
for m in re.finditer(r'<path\s+id="([A-Z]{3})"[^>]*\sd="([^"]*)"', src):
    a3, d = m.group(1), m.group(2)
    nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', d)]
    pts = list(zip(nums[0::2], nums[1::2]))
    GEO.setdefault(a3, {"pts": [], "circle": None})["pts"] += pts
for m in re.finditer(r'<circle id="([A-Z]{3})-circle" cx="(-?[\d.]+)" cy="(-?[\d.]+)"', src):
    a3, cx, cy = m.group(1), float(m.group(2)), float(m.group(3))
    GEO.setdefault(a3, {"pts": [], "circle": None})["circle"] = (cx, cy)
    GEO[a3]["pts"].append((cx, cy))

def bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

def ponto(a3, wrap=False):
    """ponto representativo do país (mediana dos vértices)."""
    g = GEO.get(a3)
    if not g or not g["pts"]:
        return None
    pts = g["pts"]
    if wrap:
        pts = [(x + WRAP_DX if x < 0 else x, y) for x, y in pts]
    xs = sorted(p[0] for p in pts); ys = sorted(p[1] for p in pts)
    n = len(pts)
    return xs[n // 2], ys[n // 2]

def diag(a3):
    g = GEO.get(a3)
    if not g or len(g["pts"]) < 2:
        return 0.0
    x0, y0, x1, y1 = bbox(g["pts"])
    return math.hypot(x1 - x0, y1 - y0)

# --- dados do livro --------------------------------------------------------
js = open("dados-paises.js", encoding="utf-8").read()
js = js[js.index("["):js.rindex("]") + 1]
js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
js = re.sub(r",(\s*])", r"\1", js)
PAISES = json.loads(js)
for p in PAISES:
    p["a3"] = a2a3.get(p["iso"], p["iso"].upper())

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;")

def texto(t, x, y, size, cls, anchor="middle", ls=None):
    lines = t.split("\n")
    a = f'class="{cls}" x="{x:.2f}" y="{y:.2f}" font-size="{size:.2f}" text-anchor="{anchor}"'
    if ls is not None:
        a += f' letter-spacing="{ls}"'
    if len(lines) == 1:
        return f'<text {a}>{esc(t)}</text>'
    dy0 = -(len(lines) - 1) * 0.55
    inner = "".join(
        f'<tspan x="{x:.2f}" dy="{dy0 if i == 0 else 1.1:.2f}em">{esc(l)}</tspan>'
        for i, l in enumerate(lines))
    return f'<text {a}>{inner}</text>'

def set_viewbox(s, vb):
    s = re.sub(r'(<svg\b[^>]*?)\sviewBox="[^"]*"',
               r'\1 viewBox="%s"' % " ".join(f"{v:.2f}" for v in vb), s, count=1)
    s = re.sub(r'(<svg\b[^>]*?)\swidth="[^"]*"\s+height="[^"]*"',
               r'\1 width="%.0f" height="%.0f"' % (vb[2] * 10, vb[3] * 10), s, count=1)
    if "preserveAspectRatio" not in s[:400]:
        s = s.replace("<svg ", '<svg preserveAspectRatio="xMidYMid meet" ', 1)
    return s

# =============================================================================
#  MAPA-MUNDO
# =============================================================================
def gen_mundo():
    s = src
    rules = [".country{fill:%s;stroke:%s;stroke-width:.1}" % (LAND_OFF, PAPER),
             "circle{display:none}"]
    for cont, (_, cor) in CONT_INFO.items():
        a3s = sorted({p["a3"] for p in PAISES if p["continente"] == cont})
        paths = [a for a in a3s if GEO.get(a) and GEO[a]["pts"] and not (GEO[a]["circle"] and len(GEO[a]["pts"]) == 1)]
        circs = [a for a in a3s if GEO.get(a) and GEO[a]["circle"] and len(GEO[a]["pts"]) == 1]
        if paths:
            rules.append(",".join(f"#{a}" for a in paths) + "{fill:%s}" % cor)
        if circs:
            rules.append(",".join(f"#{a}-circle" for a in circs)
                         + "{display:inline;fill:%s;stroke:%s;stroke-width:.3}" % (cor, PAPER))
    rules.append("#ATA{fill:%s}" % ANTARTIDA_FILL)
    css = ("\n/* livro-planisfério */\n" + "\n".join(rules) + "\n"
           ".mlbl{%sfont-weight:700;fill:%s;paint-order:stroke;stroke:#123;"
           "stroke-width:1.4;stroke-linejoin:round;}\n"
           ".mlbl.oce{fill:#4d6b78;stroke:%s;stroke-width:1.4;font-style:italic;"
           "font-weight:600;}\n" % (FONT, PAPER, PAPER))
    s = s.replace("</style>", css + "</style>", 1)

    # viewBox = envolvente de toda a terra emersa (sem a moldura de água)
    allpts = [q for a in GEO for q in GEO[a]["pts"]]
    x0, y0, x1, y1 = bbox(allpts)
    s = set_viewbox(s, (x0 - 3, y0 - 3, (x1 - x0) + 6, (y1 - y0) + 6))

    lbl = []
    for cont, (nome, _) in CONT_INFO.items():
        x, y = CONT_LABELS[cont]
        lbl.append(texto(nome.upper(), x, y, 7.5, "mlbl", ls=2))
    if "ATA" in GEO:
        bx0, by0, bx1, by1 = bbox(GEO["ATA"]["pts"])
        lbl.append(texto("ANTÁRTIDA", (bx0 + bx1) / 2, (by0 + by1) / 2, 5.5, "mlbl", ls=1.5))
    for t, x, y, sz in OCEANOS:
        lbl.append(texto(t, x, y, sz, "mlbl oce", ls=0.5))
    s = s.replace("</svg>", '<g id="rotulos">' + "".join(lbl) + "</g></svg>", 1)
    open(os.path.join(OUT, "mundo.svg"), "w", encoding="utf-8").write(s)
    print("mundo.svg", len(s) // 1024, "kB")

# =============================================================================
#  MAPA DE UM CONTINENTE
#  países grandes -> nome no mapa
#  países pequenos -> número (círculo) + legenda numerada na página do livro
# =============================================================================
LEGENDAS = {}

def _declutter(items, obstacles, vb, fs, iters=900):
    """items: dicts com 'anc', 'pos' (móveis) e 'w' (nº de caracteres).
    obstacles: (x, y, raio) fixos (rótulos de nome grandes).
    Repulsão sensível à largura da etiqueta (caixa, não círculo)."""
    x0, y0, w, h = vb
    hh = fs * 1.15
    for it in items:
        it["hw"] = max(it["w"] * fs * 0.28, fs * 1.2) + fs * 0.5
    for _ in range(iters):
        for a in items:
            fx = fy = 0.0
            ax, ay = a["anc"]; px, py = a["pos"]
            fx += (ax - px) * 0.010; fy += (ay - py) * 0.014
            for b in items:
                if b is a:
                    continue
                dx = px - b["pos"][0]; dy = py - b["pos"][1]
                ox_ = a["hw"] + b["hw"] - abs(dx)
                oy_ = 2 * hh - abs(dy)
                if ox_ > 0 and oy_ > 0:
                    if ox_ < oy_:
                        fx += math.copysign(ox_ * 0.55, dx or 1)
                    else:
                        fy += math.copysign(oy_ * 0.6, dy or 1)
            for ox, oy, orad in obstacles:
                dx = px - ox; dy = py - oy
                dd = math.hypot(dx, dy) or 0.001
                rr = orad + a["hw"]
                if dd < rr:
                    k = (rr - dd) / dd * 0.8
                    fx += dx * k; fy += dy * k
            px += max(-fs*1.5, min(fs*1.5, fx))
            py += max(-fs*1.5, min(fs*1.5, fy))
            px = min(x0 + w - a["hw"], max(x0 + a["hw"], px))
            py = min(y0 + h - hh, max(y0 + hh, py))
            a["pos"] = (px, py)


def gen_continente(cont):
    nome, cor = CONT_INFO[cont]
    wrap = (cont == "oceania")
    membros = [p for p in PAISES if p["continente"] == cont and p["a3"] in GEO
               and GEO[p["a3"]]["pts"]]

    # --- janela ---
    pts = []
    for p in membros:
        pts += [(x + WRAP_DX if (wrap and x < 0) else x, y)
                for x, y in GEO[p["a3"]]["pts"]]
    x0, y0, x1, y1 = bbox(pts)
    cx0, cy0, cx1, cy1 = CLIP[cont]
    x0, y0, x1, y1 = max(x0, cx0), max(y0, cy0), min(x1, cx1), min(y1, cy1)
    padx = (x1 - x0) * 0.03 + 1
    pady = (y1 - y0) * 0.03 + 1
    vb = (x0 - padx, y0 - pady, (x1 - x0) + 2 * padx, (y1 - y0) + 2 * pady)
    fs = max(0.9, vb[2] / 58)

    s = src
    ativos = sorted({p["a3"] for p in membros})
    paths = [a for a in ativos if not (GEO[a]["circle"] and len(GEO[a]["pts"]) == 1)]
    circs = [a for a in ativos if GEO[a]["circle"] and len(GEO[a]["pts"]) == 1]
    rules = [".country{fill:#ECE7DA;stroke:#CFC7B3;stroke-width:.08}", "circle{display:none}"]
    if paths:
        rules.append(",".join(f"#{a}" for a in paths)
                     + "{fill:#83A9BA;stroke:%s;stroke-width:.1}" % PAPER)
    if circs:
        rules.append(",".join(f"#{a}-circle" for a in circs)
                     + "{display:inline;fill:#83A9BA;stroke:%s;stroke-width:.25}" % PAPER)
    css = ("\n/* livro-planisfério · %s */\n" % cont + "\n".join(rules) + "\n"
           ".nm{%sfill:%s;paint-order:stroke;stroke:#1c4258;"
           "stroke-width:%.2f;stroke-linejoin:round;}\n"
           ".nm.big{font-weight:700;}\n"
           ".nm.sml{font-weight:600;fill:%s;stroke:%s;stroke-width:%.2f;}\n"
           ".ld{stroke:#a99a7d;stroke-width:%.2f;fill:none;}\n"
           ".dot{display:inline;fill:#8a7a5c;}\n"
           % (FONT, PAPER, fs * 0.5, INK, PAPER, fs * 0.5, fs * 0.07))
    s = s.replace("</style>", css + "</style>", 1)
    s = set_viewbox(s, vb)

    if wrap:   # junta as ilhas a leste da antimeridiana
        def _shift(m):
            return 'id="%s-circle" cx="%.6f"' % (m.group(1), float(m.group(2)) + WRAP_DX)
        for a in ativos:
            if GEO[a]["circle"] and GEO[a]["circle"][0] < 0:
                s = re.sub(r'id="(%s)-circle" cx="(-[\d.]+)"' % a, _shift, s)

    nomeados_set = NOMEADOS.get(cont, set())
    exclui = EXCLUI_MAPA.get(cont, set())
    lbls, lds, badges, obstacles = [], [], [], []
    numerados = []

    def rep_point(p):
        g = GEO[p["a3"]]["pts"]
        g = [(x + WRAP_DX if (wrap and x < 0) else x, y) for x, y in g]
        xs = sorted(q[0] for q in g); ys = sorted(q[1] for q in g)
        return xs[len(g)//2], ys[len(g)//2]

    for p in sorted(membros, key=lambda q: q["nome"].lower()):
        if p["iso"] in exclui:
            continue
        nm = CURTO.get(p["iso"], p["nome"])
        px, py = rep_point(p)
        d = diag(p["a3"])
        big = (p["iso"] in nomeados_set) if nomeados_set else (d > fs*4 and not GEO[p["a3"]]["circle"])
        if p["iso"] in NAO_NOMEAR:
            big = False
        dx, dy = OVERRIDES.get(p["iso"], (0, 0))
        if big:
            f = fs * (1.15 if d > fs*13 else 0.95)
            lbls.append(texto(nm, px+dx, py+dy, f, "nm big"))
            obstacles.append((px+dx, py+dy, max(len(nm)*f*0.32, f*1.5)))
        else:
            numerados.append({"p": p, "nm": nm, "anc": (px+dx, py+dy),
                              "pos": (px+dx, py+dy), "w": len(nm)})

    _declutter(numerados, obstacles, vb, fs)
    LEGENDAS[cont] = [it["p"]["iso"] for it in numerados]
    for it in numerados:
        ax, ay = it["anc"]; lx, ly = it["pos"]
        if math.hypot(lx-ax, ly-ay) > fs*1.1:
            lds.append(f'<line class="ld" x1="{lx:.1f}" y1="{ly:.1f}" x2="{ax:.1f}" y2="{ay:.1f}"/>'
                       f'<circle class="dot" cx="{ax:.1f}" cy="{ay:.1f}" r="{fs*0.24:.2f}"/>')
        badges.append(texto(it["nm"], lx, ly + fs*0.35, fs*0.82, "nm sml"))

    overlay = '<g id="rotulos">' + "".join(lds) + "".join(lbls) + "".join(badges) + "</g>"
    s = s.replace("</svg>", overlay + "</svg>", 1)
    open(os.path.join(OUT, f"{cont}.svg"), "w", encoding="utf-8").write(s)
    print(f"{cont}.svg  {len(s)//1024} kB  ·  {len(membros)} países  "
          f"({len(lbls)} com nome, {len(numerados)} numerados)")

# =============================================================================
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    gen_mundo()
    for c in CONT_INFO:
        gen_continente(c)
    with open(os.path.join(OUT, "legendas.js"), "w", encoding="utf-8") as f:
        f.write("window.MAPA_LEGENDA = " + json.dumps(LEGENDAS, ensure_ascii=False, indent=1) + ";\n")
    print("legendas.js", sum(len(v) for v in LEGENDAS.values()), "entradas")
    print("feito.")
