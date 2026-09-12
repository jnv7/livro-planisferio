# O Mundo, Continente a Continente

Livro infantil de consulta com **um cartão por país** de todo o mundo,
organizado continente a continente, no mesmo espírito de
"A Europa, País a País" e "Portugal, Distrito a Distrito".

- **196 países** — os 193 Estados-membros da ONU + Vaticano, Palestina e Kosovo
- **+ 20 territórios** com bandeira própria (Gronelândia, Porto Rico, Taiwan,
  Hong Kong, Faroé, Polinésia Francesa, …)
- **6 continentes** pelo modelo escolar português: América, Europa, África, Ásia,
  Oceânia e Antártida (esta só no mapa-mundo, por não ter países)

## Ficheiros

| Ficheiro | O que é |
|---|---|
| `index.html` | O livro. Abre no browser; trata da renderização, dos cartões e das quebras de página. |
| `dados-paises.js` | Os dados de todos os países (nome, endónimo, capital, língua, continente, **área**, **população**). **É aqui que se edita o conteúdo.** Lista JSON dentro de uma variável (lê-se de `file://` sem servidor). |
| `mapas/mundo.svg` | Mapa-mundo com os continentes e os oceanos. |
| `mapas/{africa,america,asia,europa,oceania}.svg` | Um mapa por continente, com os países identificados. |
| `mapas/legendas.js` | Lista dos países rotulados por número em cada mapa (gerado; não usado pelo livro atual). |
| `ferramentas/gen_mapas.py` | Gerador dos mapas a partir de `ferramentas/mundo-base.svg`. |
| `ferramentas/mundo-base.svg` | Mapa-base: "Blank world map, Equal Earth projection", Justinkunimune, Wikimedia Commons, **CC0**. |
| `pdf/` | Onde guardar o export para impressão. |

## Como usar

1. Abre `index.html` num browser (Chrome de preferência).
2. Exportar: **Imprimir → Guardar como PDF**, tamanho **A4**, margens **Nenhumas**,
   com **"Gráficos de fundo"** ativado.

**Precisa de internet** ao abrir/imprimir: as bandeiras são carregadas do CDN
jsDelivr (`lipis/flag-icons`). Sem rede, o cartão aparece à mesma, com o código
do país no lugar da bandeira. Os mapas são ficheiros locais e funcionam sempre.

Pré-visualizar uma só página: `index.html#p7` mostra apenas a 7.ª folha.

## O cartão

Mínimo, de consulta. Ordem alfabética dentro de cada continente.

```
[bandeira]  Nome (português)
            endónimo (nome na língua do país)
            CAP.   nome da capital
            LÍNG.  língua(s) oficial(is)
            ÁREA   km²  · posição no mundo
            POP.   habitantes  · posição no mundo
            [se for território] a quem pertence
```

Os territórios levam um **canto dobrado** no topo direito e **não têm ranking**
(a área/população aparecem sem a posição no mundo).

O **ranking** é mundial e conta só os 196 países independentes. É **calculado**
a partir dos dados — não se escreve. Área/população: dos dados da livro-europa
para os países europeus, do Wikidata para os restantes.

## Estrutura das páginas

15 páginas: capa · (verso) · como ler · (branca) · **mapa-mundo** · e depois,
**cada continente em 2 páginas no máximo** — o mapa do continente, a introdução e
os primeiros cartões partilham a 1.ª folha; o resto dos cartões vem na 2.ª.
A Oceânia cabe numa só página. Fecha com a página de créditos.

`CONFIG` em `index.html`: `colunas` (5), `cartoesPrimeiraPagina` (25,
debaixo do mapa) e `cartoesPorFolha` (35, folhas seguintes). Se um continente
passar de 2 folhas, aparece um aviso na consola.

## Editar os dados

Cada país em `dados-paises.js`:

```js
{
  "nome": "Portugal",           // nome em português
  "endonimo": "Portugal",       // nome na(s) língua(s) oficial(is)
  "iso": "pt",                  // código de 2 letras, minúsculas (bandeira + mapa)
  "capital": "Lisboa",
  "continente": "europa",       // africa | america | asia | europa | oceania
  "populacao": 10467000,        // número cru de habitantes
  "area": 92230,                // km²
  "soberania": "Dinamarca"      // só para territórios
}
```

- **Ordem dos continentes** no livro: `CONFIG.ordemContinentes` em `index.html`.
- **Cartões por página**: `CONFIG.colunas`, `CONFIG.cartoesPrimeiraPagina`, `CONFIG.cartoesPorFolha`.
- **Introdução e curiosidades de cada continente**: objeto `CONTINENTES` no `<script>`.

## Mapas

Todos saem de **um único** ficheiro-base (`ferramentas/mundo-base.svg`, projeção
Equal Earth, de áreas iguais — não encolhe o hemisfério sul). Para regenerar:

```
python3 ferramentas/gen_mapas.py
```

O gerador:
- pinta os países do livro (por continente no mapa-mundo; a azul nos mapas de continente);
- recorta cada continente pela janela definida em `CLIP`;
- rotula os países grandes com o nome no sítio e os pequenos com o nome puxado
  por uma linha-guia para o mar (algoritmo de "declutter" por repulsão).

Afinar rótulos sem mexer no código: dicionários **`OVERRIDES`** (empurra um rótulo),
**`CURTO`** (nome abreviado no mapa), **`NOMEADOS`** (que países levam nome vs.
linha-guia) e **`CLIP`** (janela de recorte), no topo de `gen_mapas.py`. Depois
volta a correr o script.

## Créditos

- Bandeiras: [flag-icons](https://github.com/lipis/flag-icons) (lipis) — MIT / domínio público.
- Mapa-base: "Blank world map, Equal Earth projection", *Justinkunimune* (Wikimedia Commons), **CC0**.
- Área e população: Wikidata (P2046 / P1082); para os países europeus, os números do livro *A Europa, País a País*. Arredondados, sem valor oficial.
- Tipos de letra: Fraunces, Work Sans, IBM Plex Mono (Google Fonts).
- Texto elaborado com recurso a IA e revisto; sem valor oficial.
- Sem fins comerciais.
