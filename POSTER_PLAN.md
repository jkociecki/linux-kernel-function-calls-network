# Plakat naukowy A0 — plan i pełny tekst

> **Format:** A0 poziomy (119 × 84 cm) · PDF do e-portalu (nie trzeba drukować)  
> **Tło:** `#0d1b2a` · **Figury:** `figures/poster/styled/` (przezroczyste tła)  
> **Kryteria oceny:** (1) narzędzia ASZ · (2) wyniki i wnioski · (3) jakość plakatu · (4) prototyp systemu

---

## UKŁAD PLAKATU — A0 poziomy, 4 równe kolumny

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ [LOGO]   Jądro Linuxa jako sieć złożona:                                        [QR kod] │
│          topologia, hierarchia i podatność 466 tys. funkcji                              │
│          Imię Nazwisko · Uczelnia · Sieci Złożone · 2026                                 │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  STRESZCZENIE — 2–3 zdania, pełna szerokość, 14 pt                                       │
├─────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┤
│  KOL. 1             │  KOL. 2              │  KOL. 3              │  KOL. 4              │
│  Problem + Dane     │  Analiza 1 + 2       │  Analiza 3 + 4       │  Analiza 5 + Wnioski │
│  + Metoda           │  fig_A + fig_C       │  fig_B + fig_F       │  fig_D + literatura  │
│                     │  γ ≈ 2,06            │  90,4%               │  3 315×              │
├─────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┤
│  ANALIZA 6 (⭐ oryginał) — fig_E_coupling.png — pełna szerokość — BC(kernel) = 0,993     │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## PASEK TYTUŁOWY *(pełna szerokość, ~8 cm)*

**Tytuł** — 80–90 pt, bold, biały, wyśrodkowany:
> Jądro Linuxa jako sieć złożona:  
> topologia, hierarchia i podatność 466 tys. funkcji

**Wariant angielski** *(na konferencję)*:
> The Linux Kernel as a Scale-Free Network: Topology, Hierarchy and Vulnerability

**Autorzy** — 18 pt, `#94A3B8`:
> Imię Nazwisko · Nazwa Uczelni · Kurs „Sieci Złożone" · 2026

---

## STRESZCZENIE *(pełna szerokość, 14 pt, max 80 słów)*

> Analizujemy jądro systemu Linux (v6.x) jako skierowaną sieć złożoną złożoną z **466 572 węzłów**
> (funkcji) i **4 440 158 krawędzi** (wywołań), pozyskanych przez kompilację źródeł z flagą GCC
> `-fdump-rtl-expand`. Sieć jest **bezskalowa** (γ ≈ 2,06) i strukturalnie **asymetryczna**: 90,4%
> funkcji to czyste odbiorniki wywołań. Wprowadzamy metrykę **FCI** (*Fraction of Calls Intact*),
> która ujawnia ekstremalną kruchość: 63 węzły kontrolują 50% wywołań, a atak celowany jest
> **3 315× skuteczniejszy** od losowej awarii.

---

## KOLUMNA 1 — Problem badawczy, dane i metoda *(kryterium 1: narzędzia ASZ)*

### Problem i motywacja

Linux to jeden z największych projektów open-source — **30+ mln linii kodu w C**, tysiące
programistów, 30+ lat rozwoju. Jego **graf wywołań** jest naturalną siecią złożoną:

- **węzeł** = funkcja języka C (466 572 funkcji)
- **krawędź A → B** = A wywołuje B (4 440 158 wywołań)

**Pytania badawcze:**
1. Czy sieć wywołań jest siecią bezskalową?
2. Jaka jest hierarchiczna struktura przepływu wywołań?
3. Jak odporna jest sieć na celowe i losowe awarie?

---

### Dane i ekstrakcja sieci

**Źródło:** kompilacja jądra Linux 6.x w konfiguracji `allmodconfig`
z flagą GCC `-fdump-rtl-expand` → pliki RTL (pośrednia reprezentacja kompilatora,
**przed** optymalizacją → pełny obraz statycznych zależności).

**Pipeline ekstrakcji:**

```
[ Kompilacja jądra ]     [ Pliki RTL ]      [ Parsowanie ]    [ Graf ]       [ Analiza ]
  allmodconfig       →    24 978 plików  →   Python + regex →  466k / 4,4M →  NetworkX /
  GCC 12, Linux 6.x       .expand dump       wyrażenia reg.    węzłów/kraw.   NetworkKit
```

*Kod dostępny na GitHub. Graf jako lista krawędzi CSV (310 MB).*

**Zastosowane narzędzia ASZ:** stopień węzła, CCDF, dopasowanie prawa potęgowego
(MLE + KS-test), dekompozycja SCC (bow-tie), PageRank, betweenness centrality,
macierz sprzężeń subsystemów, symulacje ataków (FCI — metryka oryginalna).

---

## KOLUMNA 2 — Analiza 1 + Analiza 2

### Analiza 1: Sieć bezskalowa *(kryterium 2: wyniki)*

**Wstaw:** `fig_A_powerlaw.png`

**LICZBA WOW** *(60 pt, `#4C9BE8`, bold)*: **γ ≈ 2.16**

Rozkład stopni wejściowych podąża za prawem potęgowym **P(k) ∝ k⁻ᵞ** z γ ≈ 2.16
*(MLE Clauesta et al., k_min = 2, n = 110,369 węzłów w ogonie)*. Wartość typowa dla sieci
rzeczywistych: WWW γ ≈ 2.1; cytowania naukowe γ ≈ 3.0. **Jądro Linux jest siecią bezskalową.**

Implikacja: nieliczna grupa funkcji wywoływanych tysiącami innych, zdecydowana
większość wywoływana rzadko lub wcale → ekstremalnie heterogeniczna architektura.

---

### Analiza 2: Role funkcji *(kryterium 2: wyniki)*

**Wstaw:** `fig_C_dispatchers.png`

Klasyfikacja wszystkich 466 572 funkcji do czterech ról:

| Rola | Warunek | Interpretacja |
|------|---------|---------------|
| **Dyspozytor** | out > 0, in ≈ 0 | inicjuje operacje (centrum dowodzenia) |
| **Most** | out > 0, in > 0 | pośredniczy między warstwami |
| **Wykonawca** | out = 0, in > 0 | implementuje logikę (liść) |
| **Izolowana** | out = 0, in = 0 | martwy kod |

`kernel` to architektoniczny węzeł centralny — jego funkcje (37% dyspozytorów + 62% mostów)
pośredniczą między systemcallami a pozostałymi subsystemami, jednocześnie inicjując operacje
i same będąc wywoływane z każdego innego subsystemu. `drivers/` zawierają głównie wykonawców — implementują logikę sprzętową.

---

## KOLUMNA 3 — Analiza 3 + Analiza 4

### Analiza 3: Struktura bow-tie *(kryterium 2: wyniki)*

**Wstaw:** `fig_B_bowtie.png`

**LICZBA WOW** *(60 pt, `#4C9BE8`, bold)*: **90,4%**

Dekompozycja Brodera (2000) — Kosaraju SCC + BFS:

| Składowa | Udział | Opis |
|----------|--------|------|
| **IN** | **90,4%** | czyste odbiorniki — nigdy nie inicjują wywołań |
| **SCC** | 2,1% | silnie spójny rdzeń — pętle wzajemnych wywołań |
| **OUT** | 0,5% | inicjują wywołania, same nie są wywoływane |
| **Tendrils** | 7,1% | słabo połączone z rdzeniem |

Jądro Linux jest **asymetryczne**: 90% kodu to bierne liście. Prawdziwa logika
sterowania skupia się w mikroskopijnym rdzeniu SCC (9 800 funkcji).

---

### Analiza 4: Paradoks PageRank *(kryterium 2: wyniki)*

**Wstaw:** `fig_F_pagerank_paradox.png`

PageRank mierzy globalny wpływ — nie liczbę połączeń, lecz *kto* do nas prowadzi:

| Funkcja | In-degree | PageRank | |
|---------|-----------|----------|-|
| `kasan_report` | **24** | **0,052** | ← wyższy! |
| `memset` | 43 983 | 0,018 | ← niższy |

`kasan_report` wywoływana przez funkcje o bardzo wysokim PageRank — wpływ
„przerzuca się" przez sieć. **Popularność ≠ wpływ.**

Panel prawy: subsystemy `kernel` i `mm` są **fundamentami** (importerzy wywołań);
`drivers/net` i `fs` — **eksporterami** inicjującymi operacje.

---

## KOLUMNA 4 — Analiza 5 + Wnioski *(⭐ kryterium 4: prototyp systemu)*

### Analiza 5: Podatność funkcjonalna — metryka FCI *(wynik oryginalny)*

**Wstaw:** `fig_D_lorenz_fci.png`

**LICZBA WOW** *(60 pt, `#FF4D4D`, bold)*: **3 315×**

**Krzywa Lorenza:** Gini = 0,928. **63 funkcje** (0,01% sieci) pośredniczą w 50%
wszystkich 4 440 158 wywołań — skrajniejsza nierówność niż większość gospodarek świata.

**Metryka FCI** (*Fraction of Calls Intact*) — oryginalna propozycja:
> FCI(t) = (wywołania możliwe po usunięciu t węzłów) / (wywołania całkowite)

Wyniki symulacji:

| Strategia ataku | Węzłów do usunięcia → FCI = 50% |
|-----------------|--------------------------------|
| Celowany (↓ in-degree) | **0,01%** węzłów |
| Losowy | **44,8%** węzłów |
| **Różnica** | **3 315×** |

Sieć **topologicznie odporna** (LCC zachowane do ~40% usunięć) ale **funkcjonalnie krucha**.

---

### Prototyp systemu / warstwa prezentacji *(kryterium 4: 0,5 pkt)*

**Interaktywna mapa podatności jądra Linux** — narzędzie dla programistów i administratorów:

**Funkcje prototypu:**
- Wyszukaj dowolną funkcję → pokaż jej rolę (dispatcher/bridge/executor), in-degree, PageRank, FCI-rank
- Kolorowa mapa: które funkcje są „punktami awarii" — krytyczne dla FCI
- Symulator ataku: usuń top-N funkcji → ile % wywołań traci system?
- Wykres subsystemów: macierz sprzężeń + alerty „zbyt duże uzależnienie od kernel"

**Stack:** Python (NetworkX) + Streamlit → `streamlit run src/dashboard.py`

**Zastosowanie:** audyt architektury przed refaktoringiem, priorytetyzacja code review,
wykrywanie modułów o nadmiernym coupling do subsystemu `kernel`.

---

### Wnioski *(kryterium 2: wnioski)*

1. **Sieć bezskalowa** — γ ≈ 2,06; ta sama klasa topologiczna co WWW i cytowania naukowe
2. **Asymetria bow-tie** — 90,4% to liście; złożoność ukryta w mikroskopijnym SCC (2,1%)
3. **Paradoks PageRank** — stopień węzła to zły predyktor globalnego wpływu; KASAN > memset
4. **Jedyny most architektoniczny** — `kernel` BC = 0,993; bez niego sieć = izolowane wyspy
5. **Paradoks odporności** — topologicznie odporna, funkcjonalnie krucha; 63 węzły = single point of failure dla 50% systemu

---

### Literatura *(10 pt)*

1. Barabási & Albert (1999). Emergence of scaling in random networks. *Science* 286, 509–512.
2. Albert, Jeong & Barabási (2000). Error and attack tolerance of complex networks. *Nature* 406, 378–382.
3. Broder et al. (2000). Graph structure in the web. *Computer Networks* 33, 309–320.
4. Clauset, Shalizi & Newman (2009). Power-law distributions in empirical data. *SIAM Rev.* 51(4).

---

## PAS DOLNY — Analiza 6: Macierz zależności *(pełna szerokość, ~16 cm)*

**Wstaw:** `fig_E_coupling.png` *(skaluj do pełnej szerokości)*

**LICZBA WOW** *(60 pt, `#A855F7`, bold, przy lewej krawędzi)*: **BC = 0,993**

Macierz: odsetek wywołań wychodzących z wiersza-subsystemu trafiający do kolumny-subsystemu.
Kolumna `kernel` jednolicie jasna — niemal każdy subsystem wywołuje funkcje z `kernel`.
Betweenness centrality w metagrafie subsystemów = **0,993**: pośredniczy w niemal każdej
ścieżce przepływu informacji między komponentami systemu.
**Jedyny architektoniczny most — bez niego Linux rozpada się na izolowane wyspy.**

---

## INSTRUKCJA SKŁADU W CANVIE *(dla składającego, nie na plakat)*

### Krok po kroku — A0 poziomy

1. Canva → Nowy projekt → Niestandardowe → **119 × 84 cm**
2. Tło: `#0d1b2a` (cały plakat)
3. Tytuł: Montserrat ExtraBold lub Inter Black, **80–90 pt**, biały, wyśrodkowany
4. Logo uczelni: lewy górny róg | QR GitHub/danych: prawy górny róg
5. Streszczenie: 1 pasek bezpośrednio pod tytułem, 14 pt, `#94A3B8`
6. **4 równe kolumny** (~27 cm × ~54 cm), tło sekcji `#132033`, padding 0,8 cm, zaokrąglenie 8 px
7. Figury PNG: prześlij z `figures/poster/styled/` — przezroczyste tła blendują się
8. Liczby WOW: osobne bloki, **60–80 pt bold**, kolory z tabeli poniżej
9. Tekst: 13–14 pt, `#94A3B8`; nagłówki sekcji: 18–20 pt bold, `#F0F4F8`
10. Pas dolny fig_E: usuń podział kolumn, 1 element pełnej szerokości, ~16 cm
11. Export: **PDF (druk)** lub PNG 300 dpi → wyślij na e-portal

### Paleta kolorów

| Element | Hex | Gdzie |
|---------|-----|-------|
| Tło plakatu | `#0d1b2a` | całe tło |
| Tło sekcji | `#132033` | ramki kolumn |
| Niebieski neon | `#4C9BE8` | γ ≈ 2,06 · 90,4% |
| Czerwony neon | `#FF4D4D` | 3 315× · FCI · podatność |
| Fioletowy neon | `#A855F7` | BC = 0,993 · PageRank · SCC |
| Pomarańczowy | `#FF8C42` | OUT · eksporterzy |
| Tekst główny | `#F0F4F8` | tytuły sekcji |
| Tekst wtórny | `#94A3B8` | treść akapitów |

### Liczby WOW — rozmieszczenie

| Liczba | Kolor | Gdzie na plakacie | Opis pod spodem |
|--------|-------|-------------------|----------------|
| **γ ≈ 2,06** | `#4C9BE8` | kol. 2, nad fig_A | wykładnik prawa potęgowego |
| **90,4%** | `#4C9BE8` | kol. 3, nad fig_B | funkcji to czyste odbiorniki |
| **3 315×** | `#FF4D4D` | kol. 4, nad fig_D | atak celowany vs losowy |
| **63** | `#FF4D4D` | kol. 4, przy fig_D | funkcje = 50% wywołań |
| **BC = 0,993** | `#A855F7` | pas dolny, lewa krawędź fig_E | betweenness centrality kernel |

---

## MAPOWANIE NA KRYTERIA OCENY

| Kryterium | Maks. | Gdzie w plakacie |
|-----------|-------|-----------------|
| Narzędzia i techniki ASZ | 1,0 | kol. 1 (metoda), kol. 2–4 (każda analiza), pas dolny |
| Wyniki, obserwacje, wnioski | 1,0 | kol. 2–4 (analizy 1–5), kol. 4 (wnioski), pas dolny |
| Jakość prezentacji i plakatu | 0,5 | spójny dark theme, WOW numbers, figury, czytelność |
| Prototyp systemu | 0,5 | kol. 4 „Interaktywna mapa podatności" (Streamlit) |
| **RAZEM** | **3,0** | |
