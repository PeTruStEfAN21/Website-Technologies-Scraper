# Web Technology Detector - Cum am gandit si construit proiectul

## 1. Documentarea initiala si planul de lucru
Inainte sa ma apuc efectiv de scris cod, m-am documentat in mare despre ce inseamna web scraping-ul si cum poti sa iti dai seama cu ce tehnologii este facut un site fara sa ai acces la codul lor de pe server. Am deschis cateva site-uri in browser, m-am uitat in DevTools (la Network si la codul sursa al paginii) si am observat ca majoritatea platformelor isi lasa amprenta in cateva locuri clare: in HTTP headers, in cookies, in tag-urile `<meta>`, in link-urile catre fisierele `.js` (scripts) si `.css` (href) sau direct in structura HTML.

De aici mi-am impartit proiectul pe etape logice:
1. Sa fac mai intai partea de conexiune la server si extragere a datelor brute (`fetcher.py`).
2. Sa fac partea de parsare a fisierelor si de detectare a tehnologiilor (`detector.py` + `signatures.json`).
3. Sa descifrez fisierul primit cu lista de domenii si sa rulez totul cap-coada (`main.py`).

## 2. Conexiunea la server si partea grea: amprentele tehnologiilor
Pentru prima parte (`fetcher.py`), am facut o clasa `PageData` in care sa adun toate informatiile importante de pe un site intr-un singur loc. Am folosit `requests` pentru a descarca pagina si `BeautifulSoup` pentru a parsa HTML-ul o singura data si a scoate intr-o forma curata doar listele de scripturi, link-uri si meta tags.

Partea cu adevarat grea a venit la pasul urmator, cand a trebuit sa caut identificatorii specifici pentru fiecare tool sau tehnologie (WordPress, Shopify, Next.js, Cloudflare, Nginx etc.). Mi-am dat seama rapid ca daca scriu zeci de `if`-uri direct in codul de Python o sa iasa un cod imposibil de citit si de intretinut. Asa ca am separat regulile intr-un fisier `signatures.json`, iar in `detector.py` am scris doar logica care compara ce a extras `Fetcher`-ul cu ce scrie in JSON. 

Aici m-am lovit de o chestie interesanta: la unele headere (cum e `server: cloudflare`) trebuie sa verifici valoarea, dar la altele (cum e `cf-ray` sau `x-shopid` la Shopify) valoarea este un cod generat aleatoriu. Am rezolvat asta punand string gol `""` in JSON acolo unde ma intereseaza doar daca exista cheia respectiva in header. De asemenea, ca sa nu imi adauge aceeasi tehnologie de mai multe ori in lista (daca o gaseste si in scripts, si in href), am pus un `break` imediat ce gaseste prima potrivire.

## 3. Descifrarea listei de domenii si trecerea la Multi-threading
Dupa ce am vazut ca motorul de detectie merge bine pe cateva site-uri de test, am trecut la lista de domenii primita pentru tema. Fisierul fiind in format `.snappy.parquet`, m-am documentat despre ce inseamna formatul Parquet si am facut un mic script in Python (cu `pandas` si `pyarrow`) ca sa il descifrez si sa extrag lista curata de domenii intr-un fisier text.

Cand am incercat sa rulez programul pe toata lista de 200 de domenii liniar (site cu site, intr-un simplu `for`), am observat ca dura o eternitate. Motivul era simplu: programul statea si astepta secunde intregi dupa fiecare site lent sau picat inainte sa treaca la urmatorul.

Am cautat solutii ca sa citesc mai multe site-uri deodata si am decis sa folosesc multi-threading (`ThreadPoolExecutor`). Mai auzisem de multi-threading pana acum la facultate, dar sincer nu am avut nevoie sa il folosesc in proiectele mele pentru ca nu m-am lovit de ceva care sa ceara o putere sau o viteza de asteptare atat de mare.

Totusi, am observat ca nici aici nu poti sa pui un numar urias de muncitori (threads) fara cap:
* Initial am incercat sa pun **60 de muncitori** ca sa termine cat mai repede, dar cand m-am uitat pe rezultate am vazut ca unele domenii care mergeau cand le testam separat imi dadeau acum status `0` (eroare de conexiune). Practic, trimitand 60 de cereri simultan, sufocam rezolutia DNS locala si imi lua timeout pe pachete.
* In plus, chiar daca asteptarea raspunsului de la server (I/O) merge in paralel, parsarea HTML-ului cu BeautifulSoup foloseste procesorul (unde in Python intervine GIL-ul). 
* Am masurat in mare timpii: o cerere asteapta dupa retea in medie cam 1.2 secunde (1200 ms), iar parsarea dureaza cam 50 ms. Facand raportul dintre timpul de asteptare si cel de procesare (1 + 1200 / 50), am ajuns la **25 de muncitori (`max_workers = 25`)**. Cu setarea asta, toate cele 200 de domenii sunt gata in ~25-30 de secunde fara sa mai pierd site-uri bune pe drum.

## 4. Analiza erorilor intalnite pe domenii reale
Ruland scraper-ul pe toate domeniile din lista, am observat ca destul de multe dadeau eroare sau se comportau ciudat. Le-am analizat manual si am impartit problemele in cateva categorii clare:

1. **Domeniul nu mai exista (DNS failure):**
   * *Exemplu:* `jcmobilecigars.com`
   * Domeniul a expirat sau a fost sters complet din DNS, deci nu exista nicio adresa IP la care sa ne conectam. Aici intoarcem `status_code = 0` si marcam eroarea ca `DNS_NOT_FOUND`.
2. **Serverul nu raspunde (Connection Timeout / Dead Host):**
   * *Exemple:* `coenzwezerijnen.nu`, `phucankhanggroup.com`
   * Domeniul inca exista in DNS, dar serverul din spate este oprit sau nu raspunde in timpul limita de 10 secunde. Marcam eroarea ca `TIMEOUT`.
3. **Site-urile blocheaza botii (WAF / Anti-bot protection):**
   * *Exemple:* `costa-coffee.be`, `jackwills.com`
   * Unele site-uri mari au sisteme de protectie agresive (Cloudflare, Akamai) care blocheaza cererile venite din scripturi sau dau `403 Forbidden` / `ReadTimeout`. Chiar si asa, pentru ca nu aruncam raspunsurile care nu au status 200, de multe ori tot reusim sa extragem din headere si din pagina de blocare ce CDN sau server folosesc (de exemplu, chiar si pe `5starremoval.weebly.com` care da `404 Not Found`, programul detecteaza corect `Weebly` si `Cloudflare`).
4. **Certificate SSL configurate gresit sau expirate:**
   * *Exemplu:* `dioxoxigenio.com.br`
   * Initial imi crapa conexiunea cu `SSLCertVerificationError (Hostname mismatch)`. Cum pe mine ma intereseaza doar sa vad ce tehnologii foloseste site-ul, nu sa fac plati bancare pe el, am implementat fallback fara validare stricta de SSL (`verify=False` in `Fetcher`) si fallback pe HTTP, putand scana fara probleme si site-urile cu HTTPS stricat.

O alta observatie legata de cand am considerat ca rezultatul e suficient de bun: pe site-uri gigant precum `google.com` sau `github.com`, detectorul intoarce lista goala `[]`. Asta e normal, pentru ca ei folosesc arhitecturi interne custom, nu WordPress sau Bootstrap, si am preferat sa las rezultatul curat decat sa ghicesc si sa bag rezultate false.

## 5. Interfata vizuala (`dashboard.py`)
La final, m-am gandit ca ar fi mult mai fain ca proiectul sa aiba si o interfata vizuala, ca sa fie un produs usor de folosit pentru oricine vrea sa se uite pe date (cu grafice pentru cele mai folosite tehnologii, tabel de filtrare si un scanner live unde poti baga orice site), fara sa isi bata capul cautand prin mii de linii intr-un fisier JSON.

Pentru partea asta de interfata in `Streamlit` (`dashboard.py`), m-am folosit de AI cu usoare interventii din partea mea, deoarece am preferat sa imi concentrez timpul si efortul pe partea practica de backend (arhitectura `Fetcher` / `Detector`, baza de semnaturi, rezolvarea erorilor de retea si optimizarea multi-threading-ului).

## Cum se ruleaza proiectul
1. Instalare dependinte:
   ```bash
   pip install -r requirements.txt
   ```
2. Rularea scraper-ului pe lista de domenii (genereaza `results.json` si afiseaza sumarul in terminal):
   ```bash
   python main.py
   ```
3. Pornirea interfetei vizuale in browser:
   ```bash
   streamlit run dashboard.py
   ```
