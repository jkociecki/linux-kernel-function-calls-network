# AUDYT PLAKATU - ZNALEZIONE NIESPÓJNOŚCI

**Data audytu:** 2025-05-06  
**Analiza:** Porównanie tekstu i figur w POSTER_PLAN.md z rzeczywistymi danymi w node_metrics.csv

---

## 🔴 KRYTYCZNE BŁĘDY (muszą być poprawione)

### 1. KERNEL ROLE COMPOSITION — TEKST VS RZECZYWISTOŚĆ

**Problem:** Tekst w POSTER_PLAN.md (linia 124) mówi:
```
`kernel` złożony niemal wyłącznie z dyspozytorów — wywołuje całą resztę systemu.
```

**Rzeczywiste dane z node_metrics.csv:**
```
Kernel subsystem (13,934 funkcji):
  Dispatcher:  5,154 funkcji (37.0%)
  Bridge:      8,573 funkcji (61.5%)  ← WIĘKSZOŚĆ!
  Executor:       44 funkcji (0.3%)
  Isolated:      163 funkcji (1.2%)
```

**Weryfikacja figury:** Attachment pokazuje Fig. 3 z kernelem: **37% niebieski (dispatcher) + 62% zielony (bridge)**

**Diagnoza:** Tekst jest **BŁĘDNY**. Kernel NIE jest "niemal wyłącznie dyspozytorów". 
- Dyspozytorzy (37%) — inicjują operacje, nie są wywoływane
- Mostki (62.5%) — POŚREDNICZĄ: odbierają komendy (`in > 0`) i wykonują je delegując (`out > 0`)

**Rekomendacja:** Zmień tekst na:
```
`kernel` to architektoniczny węzeł centralny — jego funkcje (37% dyspozytorów + 62% mostów) 
pośredniczą między syscallami a pozostałymi subsystemami, jednocześnie inicjując operacje 
i same będąc wywoływane z każdego innego subsystemu.
```

**Impact na prezentację:** WYSOKI — zmieniłoby interpretację całej sekcji o rolach funkcji.

---

### 2. GAMMA (Power-law exponent) — TEKST VS FIGURA

**Problem:** POSTER_PLAN.md (linia 65) podaje:
```
γ ≈ 2,06
```

**Co figura 1 (01_hero_powerlaw.png) pokazuje:**
```
in-degree:    y = 2.20 ± 0.01   ← INNA WARTOŚĆ!
out-degree:   y = 2.27 ± 0.00
total degree: y = 2.14 ± 0.00
```

**Moje obliczenia (xmin=32):** γ = 1.874

**Diagnoza:** Rozbieżności między tekstem (2.06), figurą (2.20), a moimi obliczeniami (1.87).
- Możliwe przyczyny: inny `xmin`, inna metodologia (MLE vs LS), inne źródło danych

**Rekomendacja:** 
1. Weryfikacja: które `xmin` użyto do fitowania?
2. Jeśli figura jest źródłem prawdy, zmień tekst na: `γ ≈ 2.20 ± 0.01`
3. Dodać footnote: "(dla in-degree, xmin = ? węzłów)"

**Impact:** ŚREDNI — wpływa na interpretację skali sieci, ale nie drastycznie.

---

### 3. BOW-TIE COMPONENT: OUT — TEKST VS MOJE OBLICZENIA

**Problem:** POSTER_PLAN.md (tabela linia 135) i figura 2 (07_q2_bowtie.png) mówią:
```
OUT (inicjatory, sami nie wywoływani):  0,5%
```

**Moje obliczenia Kosaraju SCC:**
```
OUT component: 0 węzłów (0.0%)   ← KOMPLETNIE PUSTY!
```

**Diagnoza:** W największej SCC nie znalazłem węzłów z `in_degree=0 and out_degree>0`.
- Możliwe: OUT to węzły spoza największej SCC, lub inna definicja SCC

**Rekomendacja:** Weryfikacja algorytmu dekompozycji bow-tie — czy używamy tej samej definicji?

**Impact:** WYSOKI jeśli figura zawiera błąd.

---

## 🟡 ROZBIEŻNOŚCI DRUGORZĘDNE (małe, mogą być zaokrągleniami)

### 4. GINI COEFFICIENT

| Źródło | Wartość | Notatka |
|--------|---------|---------|
| **POSTER_PLAN.md** | 0,928 | Stwierdzone |
| **Moje obliczenia** | 0.957 | Z bieżących danych |
| **Różnica** | +0.029 | Mała (~3%) |

**Diagnoza:** Różnica może być wynikiem instrumentation functions lub innej metodologii.
Jeśli filtrujemy ASAN/sanitizer functions, Gini powinien spaść.

**Status:** Akceptowalny margines błędu dla danych empirycznych.

---

### 5. BOW-TIE IN COMPONENT

| Źródło | Wartość | Notatka |
|--------|---------|---------|
| **POSTER_PLAN.md** | 90,4% | |
| **Moje obliczenia** | 90.8% | Kosaraju SCC |
| **Różnica** | +0.4% | Bardzo mała |

**Status:** ✓ ZGADZA SIĘ w ramach błędu zaokrąglenia.

---

### 6. BOW-TIE SCC COMPONENT

| Źródło | Wartość | Notatka |
|--------|---------|---------|
| **POSTER_PLAN.md** | 2,1% | |
| **Moje obliczenia** | 2.1% | |
| **Różnica** | 0.0% | IDEALNA |

**Status:** ✓ IDEALNE DOPASOWANIE.

---

## 📊 WERYFIKACJA LICZB PODSTAWOWYCH

| Metryka | POSTER_PLAN.md | node_metrics.csv | Status |
|---------|-----------------|------------------|--------|
| Węzły | 466,572 | 466,572 | ✓ |
| Krawędzie | 4,440,158 | 4,440,158 | ✓ |
| Średni degree | — | 9.52 | — |
| Max in-degree | — | 426,077 | ← ASAN |
| Gini | 0,928 | 0,957 | ⚠️ +0.029 |
| IN (bow-tie) | 90,4% | 90,8% | ✓ +0.4% |
| SCC (bow-tie) | 2,1% | 2,1% | ✓ |
| OUT (bow-tie) | 0,5% | 0,0% | ⚠️ |

---

## 🔧 REKOMENDACJE POPRAWEK

### Priorytet 1 (MUSZĄ): 
1. **Kernel text** — zmienić z "niemal wyłącznie dyspozytorzy" na "37% dyspozytorów + 62% mostów"
2. **Gamma value** — weryfikacja czy 2.06 czy 2.20 ± 0.01

### Priorytet 2 (POWINNA): 
3. **OUT component** — wyjaśnić czy 0.5% czy 0.0%

### Priorytet 3 (OPCJONALNIE):
4. **Gini refinement** — filtrowanie instrumentation functions może wyrównać 0.957 → ~0.928

---

## 📝 PLIKI DO SPRAWDZENIA

```
figures/poster/01_hero_powerlaw.png      — Gamma wartości
figures/poster/07_q2_bowtie.png          — Bow-tie komponenty
figures/poster/07_q3_dispatcher_executor.png — Kernel rola
POSTER_PLAN.md (linie: 65, 124, 135)     — Tekstowe stwierdzenia
```

---

## ⚠️ UWAGA OGÓLNA

Te niespójności sugerują, że **plakat może być generowany z innego źródła danych** niż bieżące `node_metrics.csv`. 
Możliwe przyczyny:
- Inne filterowanie (instrumentation functions)
- Inne kompilacja kernela (np. defconfig vs allmodconfig)
- Inne xmin do power-law fit
- Inna implementacja dekompozycji bow-tie

**Rekomendacja:** Sprawdzić git historię figur i upewnić się, że dane są aktualne.

