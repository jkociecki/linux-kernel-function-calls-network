# Skrypt prezentacji do plakatu

Ten plik jest zgodny z liczbami i interpretacjami z plakatu oraz z [POSTER_PLAN.md](/workspaces/linux-kernel-function-calls-network/POSTER_PLAN.md).

Założenie:
- kolega mówi sekcje 1-2, czyli wprowadzenie, dane i metodę
- Ty mówisz część analityczną i wnioski
- całość ma zająć do 10 minut

## Najpierw: o co chodzi w projekcie, bardzo prosto

Najprostsza wersja jest taka:

- Linux to ogromny program złożony z setek tysięcy funkcji.
- Jedna funkcja często wywołuje inne funkcje.
- Jeśli potraktujemy każdą funkcję jako punkt, a każde wywołanie jako strzałkę, dostajemy sieć.
- Tę sieć można badać narzędziami od sieci złożonych, tak jak bada się Internet albo sieci społeczne.

W tym projekcie:

- węzeł = funkcja w jądrze Linuxa
- krawędź = wywołanie jednej funkcji przez drugą
- dane powstały ze statycznej analizy kompilacji kernela

To znaczy, że nie patrzymy na to, co kernel zrobił w jednej chwili po uruchomieniu, tylko na to, jakie zależności są wpisane w kod.

Pytanie badawcze brzmi:

- czy Linux ma strukturę przypadkową,
- czy raczej ma ukrytą architekturę typową dla złożonych systemów,
- i czy jest odporny na awarie.

Najważniejsza intuicja:

- jeśli kilka funkcji jest bardzo centralnych, to uszkodzenie ich może rozwalić pół systemu,
- jeśli struktura jest modularna, to znaczy że część rzeczy da się zmieniać lokalnie,
- jeśli wszystko zależy od wszystkiego, to system jest trudny do refaktoryzacji i testowania.

## Co sprawdziłem i co było błędne w poprzedniej wersji

Poprzedni skrypt miał kilka błędów interpretacyjnych względem plakatowych wykresów:

1. `γ ≈ 2.06` zostało błędnie opisane jako assortatywność.
2. Bow-tie było opisane odwrotnie: na plakacie `90,4%` dotyczy składowej `IN`, a nie `SCC`.
3. Dysasortatywność była opisana odwrotnie jako dodatnia assortatywność.
4. Sekcja o `3 315×` była miejscami mieszana z community detection, a na plakacie to wynik metryki FCI i symulacji ataku.

Ten plik poprawia to wszystko.

## Podział czasu

Proponowany timing:

1. Kolega: problem, dane, pipeline, co to jest graf funkcji — 2 min
2. Ty: bezskalowość i role funkcji — 1,5 min
3. Ty: bow-tie i PageRank — 2 min
4. Ty: FCI i podatność — 1,5 min
5. Ty: macierz subsystemów i BC kernela — 1 min
6. Ty: wnioski — 1 min
7. Zapas — 1 min

Razem: około 9 minut.

---

## Twoja część: gotowy skrypt mówiony

## Sekcja A. Sieć bezskalowa

### Co mówisz

"Teraz przechodzę do pierwszego głównego wyniku. Ten wykres pokazuje, że sieć wywołań jądra Linuxa jest bezskalowa.

To znaczy, że większość funkcji ma mało połączeń, ale istnieje bardzo mała grupa funkcji, które mają ich ogromnie dużo.

Na plakacie mamy parametr gamma około 2,06. To jest wykładnik prawa potęgowego. Innymi słowy, rozkład nie przypomina dzwonu Gaussa, tylko ma długi ogon.

Praktycznie oznacza to, że Linux nie jest równomiernie zorganizowany. Nie wszystkie funkcje są podobnie ważne. Mamy mnóstwo zwykłych funkcji i garść hubów, które spajają cały system.

To jest bardzo podobne do Internetu albo sieci cytowań naukowych. Właśnie dlatego mówimy, że kernel zachowuje się jak klasyczna sieć złożona." 

### Co to znaczy teoretycznie

Bezskalowość oznacza, że rozkład stopnia dobrze przybliża prawo potęgowe:

$$P(k) \propto k^{-\gamma}$$

Gdzie:

- $k$ to liczba połączeń węzła,
- $\gamma$ to wykładnik rozkładu,
- na plakacie: $\gamma \approx 2{,}06$.

Interpretacja:

- jeśli sieć byłaby losowa, większość węzłów miałaby podobny stopień,
- tutaj tak nie jest: kilka funkcji ma ekstremalnie dużo połączeń,
- więc uszkodzenie losowej funkcji zwykle ma mały wpływ, ale uszkodzenie huba może być katastrofalne.

To jest dokładnie sens hasła: sieć bezskalowa.

### Co zapamiętać

- `γ ≈ 2,06` to nie assortatywność i nie centralność
- to parametr prawa potęgowego
- oznacza istnienie hubów i bardzo nierówny rozkład zależności

---

## Sekcja B. Role funkcji w sieci

### Co mówisz

"Drugi wykres porządkuje funkcje według ról. Autorzy dzielą je na dyspozytory, mosty, wykonawców i funkcje izolowane.

Dyspozytor to funkcja, która głównie uruchamia inne rzeczy. Most pośredniczy między warstwami. Wykonawca jest końcówką logiki, czyli raczej coś robi niż czymś steruje.

To rozróżnienie jest ważne, bo pozwala zrozumieć, które części kernela sterują ruchem w systemie, a które tylko realizują polecenia.

Na poziomie architektury widzimy, że `kernel` skupia funkcje sterujące, a `drivers` częściej pełnią rolę wykonawców. To dobrze pasuje do intuicji: rdzeń zleca pracę, a sterowniki ją wykonują." 

### Co to znaczy teoretycznie

To nie jest jedna standardowa metryka z teorii grafów, tylko sensowna klasyfikacja oparta o `in-degree` i `out-degree`:

- dyspozytor: dużo wychodzących, mało przychodzących,
- most: i przychodzące, i wychodzące,
- wykonawca: głównie przychodzące,
- izolowana: praktycznie brak udziału w ruchu.

Ta sekcja mówi o funkcjonalnych rolach w architekturze kodu, a nie o samej topologii globalnej.

---

## Sekcja C. Bow-tie

### Co mówisz

"Teraz jeden z najciekawszych wyników strukturalnych, czyli bow-tie.

Sieć została rozbita na cztery części: IN, SCC, OUT i tendrils.

Najważniejsza liczba z plakatu to 90,4 procent. Ale uwaga: to nie jest rdzeń. To jest część IN.

To znaczy, że ogromna większość funkcji to w praktyce liście albo odbiorniki logiki sterowania. Natomiast silnie spójny rdzeń, czyli SCC, jest bardzo mały i ma około 2,1 procent całej sieci.

Czyli złożoność sterowania jest skupiona w bardzo małej części systemu, a cała reszta jest do niej podpięta.

To bardzo mocny wniosek architektoniczny: ogrom kodu jest peryferyjny, a prawdziwa logika sterująca siedzi w małym rdzeniu." 

### Co to znaczy teoretycznie

Bow-tie to klasyczna dekompozycja skierowanej sieci:

- `SCC` to największa silnie spójna składowa, gdzie z każdego węzła można dojść do każdego innego,
- `IN` to węzły prowadzące do rdzenia,
- `OUT` to węzły osiągalne z rdzenia,
- `tendrils` to reszta.

Na plakacie interpretacja jest taka:

- `IN = 90,4%`
- `SCC = 2,1%`
- `OUT = 0,5%`
- `tendrils = 7,1%`

Najważniejszy sens:

- rdzeń sterowania jest mały,
- większość funkcji nie tworzy gęstej sieci sprzężeń zwrotnych,
- architektura jest silnie asymetryczna.

### Co zapamiętać

- `90,4%` na plakacie dotyczy `IN`, nie `SCC`
- `SCC` jest mały, ale strategiczny
- większość kodu jest podpięta do rdzenia, a nie równorzędna wobec niego

---

## Sekcja D. Paradoks PageRank

### Co mówisz

"Kolejny wynik pokazuje, że popularność funkcji nie jest tym samym co wpływ.

Na plakacie jest porównanie typu `memset` kontra `kasan_report`. `memset` ma bardzo duży in-degree, czyli woła go mnóstwo funkcji. Ale PageRank ma niższy niż `kasan_report`.

Dlaczego? Bo PageRank nie liczy tylko tego, ile połączeń wchodzi do węzła, ale także jak ważne są źródła tych połączeń.

Czyli można być bardzo popularnym technicznie, ale nie być strategicznie centralnym. I odwrotnie: można mieć mniej połączeń, ale być ważnym, bo prowadzą do ciebie bardzo wpływowe funkcje.

To jest właśnie paradoks PageRank z tego plakatu: stopień węzła nie wystarcza, żeby opisać znaczenie funkcji w systemie." 

### Co to znaczy teoretycznie

PageRank to miara wpływu oparta na rekursji:

$$PR(v) = \frac{1-d}{N} + d \sum_{u \to v} \frac{PR(u)}{out(u)}$$

Gdzie:

- $d$ to współczynnik tłumienia,
- $N$ to liczba węzłów,
- liczy się nie tylko liczba krawędzi przychodzących, ale jakość źródeł.

Dlatego:

- `memset` może być wywoływany przez masę zwykłych funkcji,
- a `kasan_report` może być wywoływany przez mniejszą liczbę, ale bardziej centralnych elementów systemu.

To pokazuje, że lokalna popularność i globalny wpływ to dwie różne rzeczy.

---

## Sekcja E. FCI i kruchość sieci

### Co mówisz

"To jest moim zdaniem najmocniejszy wynik na całym plakacie.

Autorzy wprowadzili metrykę FCI, czyli Fraction of Calls Intact. Ona mierzy, jaki odsetek wywołań nadal działa po usunięciu pewnych węzłów.

Wynik jest brutalny. Wystarczy usunąć 63 funkcje, czyli około 0,01 procent całej sieci, żeby stracić połowę wszystkich wywołań.

A gdy porównamy atak celowany do losowego, to okazuje się, że atak celowany jest 3 315 razy skuteczniejszy.

Czyli Linux jest odporny na przypadkowe uszkodzenia, ale bardzo wrażliwy na trafienie w odpowiednie huby.

To jest klasyczne zachowanie sieci bezskalowej: losowy chaos system przeżyje, ale precyzyjne uderzenie w centrum już nie." 

### Co to znaczy teoretycznie

FCI to metryka funkcjonalna:

$$FCI(t) = \frac{\text{liczba zachowanych wywołań po usunięciu } t \text{ węzłów}}{\text{liczba wszystkich wywołań}}$$

Znaczenie:

- nie patrzymy tylko, czy graf pozostaje spójny,
- patrzymy, ile realnej funkcjonalności sieci zostało.

Na plakacie:

- Gini dla wywołań: `0,928`
- 63 funkcje kontrolują 50% wywołań
- atak celowany jest `3315×` skuteczniejszy niż losowy.

To mówi, że nierówność rozkładu wywołań jest ekstremalna.

### Co zapamiętać

- `3315×` dotyczy FCI i symulacji ataku
- to nie community detection i nie modularność
- główny przekaz: sieć jest funkcjonalnie krucha mimo dużego rozmiaru

---

## Sekcja F. Macierz sprzężeń i BC kernela

### Co mówisz

"Ostatni główny wynik pokazuje relacje między subsystemami, czyli nie między pojedynczymi funkcjami, tylko między dużymi częściami kernela.

Najważniejsza liczba tutaj to BC, czyli betweenness centrality dla `kernel`, równe 0,993.

To znaczy, że `kernel` jest praktycznie jedynym mostem architektonicznym. Prawie każda istotna ścieżka komunikacji między subsystemami przechodzi przez rdzeń.

Na macierzy widać, że wiele subsystemów odwołuje się do `kernel`, więc rdzeń nie jest po prostu jedną z części systemu, tylko punktem pośredniczącym dla całej reszty.

W praktyce: bez `kernel` Linux rozpada się na izolowane wyspy." 

### Co to znaczy teoretycznie

Betweenness centrality mierzy, przez ile najkrótszych ścieżek przechodzi dany węzeł lub komponent:

$$BC(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$

Na plakacie nie chodzi o pojedynczą funkcję, tylko o metagraf subsystemów.

Interpretacja `BC(kernel) = 0,993`:

- rdzeń kernela pośredniczy w niemal wszystkich ważnych przepływach między subsystemami,
- `drivers`, `fs`, `net` i inne części nie są równorzędnie połączone ze sobą,
- system ma jeden dominujący most architektoniczny.

To bardzo mocny argument, że kernel jest centrum integracji całej platformy.

---

## Sekcja G. Wnioski końcowe

### Co mówisz

"Podsumowując, z tego plakatu wynikają pięć głównych rzeczy.

Po pierwsze, Linux jest siecią bezskalową, czyli ma huby i długi ogon rozkładu zależności.

Po drugie, struktura bow-tie pokazuje, że większość kodu to peryferia, a prawdziwy rdzeń sterowania jest bardzo mały.

Po trzecie, popularność funkcji nie oznacza wpływu, co dobrze pokazuje paradoks PageRank.

Po czwarte, kernel jako subsystem jest prawie jedynym mostem architektonicznym, co potwierdza betweenness centrality równe 0,993.

I po piąte, mimo że sieć wygląda na dużą i rozproszoną, funkcjonalnie jest bardzo krucha: 63 funkcje wystarczą, żeby wyłączyć połowę wszystkich wywołań.

Czyli Linux jest jednocześnie modularny i bardzo nierówny. To system ogromny, ale zależny od bardzo małej liczby krytycznych punktów." 

---

## Krótkie omówienie teoretyczne każdej liczby z plakatu

### `466 572`

Liczba węzłów, czyli liczba funkcji uwzględnionych w grafie.

### `4 440 158`

Liczba krawędzi, czyli liczba statycznie wykrytych wywołań funkcji.

### `γ ≈ 2,06`

Wykładnik prawa potęgowego dla rozkładu stopni.

### `90,4%`

Udział składowej `IN` w dekompozycji bow-tie.

### `2,1%`

Udział `SCC`, czyli małego, ale strategicznego rdzenia.

### `0,928`

Współczynnik Giniego dla nierówności rozkładu wywołań. Bardzo wysoka koncentracja.

### `63`

Liczba funkcji, które kontrolują połowę wszystkich wywołań.

### `3315×`

Przewaga ataku celowanego nad losowym w sensie FCI.

### `0,993`

Betweenness centrality subsystemu `kernel` w metagrafie subsystemów.

---

## Czego nie mówić, żeby nie popełnić błędu

1. Nie mów, że `γ ≈ 2,06` to assortatywność.
2. Nie mów, że `90,4%` to SCC.
3. Nie mów, że `3315×` to liczba społeczności albo wynik FCI bez kontekstu ataku.
4. Nie mów, że `BC = 0,993` dotyczy pojedynczej funkcji, jeśli na plakacie chodzi o `kernel` jako subsystem.
5. Nie mieszaj PageRank z in-degree.

---

## Jedna bardzo prosta wersja do nauczenia na szybko

Jeśli będziesz miała mało czasu na naukę, zapamiętaj ten skrót:

- Linux to graf funkcji.
- Jest bezskalowy, więc ma kilka bardzo ważnych hubów.
- Większość kodu to peryferia, a sterowanie siedzi w małym rdzeniu.
- Popularność funkcji nie znaczy jeszcze, że jest najważniejsza globalnie.
- 63 funkcje wystarczą, żeby wyciąć połowę wywołań.
- Kernel jest głównym mostem między subsystemami.

To już wystarczy, żeby obronić większość pytań.