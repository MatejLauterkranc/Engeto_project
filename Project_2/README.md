# Bulls & Cows
Tvým úkolem je vytvořit program, který simuluje hru Bulls and Cows. Po vypsání úvodního textu uživateli začne hádání tajného čtyřciferného čísla.
# Úvod
Cílem projektu je vytvořit hru, ve které uživatel hádá tajné číslo, které počítač vygeneruje. Hráč se snaží uhodnout nejen správné číslo, ale také správné pořadí číslic v čísle. Po každém tipu hráči program vyhodnotí, kolik číslic (bulls) je na správných místech a kolik (cows) se nachází v čísle, ale na špatném místě.

>>
Příklad hry s číslem 2017:
--------------------------

Hi there!
-----------------------------------------------
I've generated a random 4 digit number for you.
Let's play a bulls and cows game.
-----------------------------------------------
Enter a number:
-----------------------------------------------
>>> 1234
0 bulls, 2 cows
-----------------------------------------------
>>> 6147
1 bull, 1 cow
-----------------------------------------------
>>> 2417
3 bulls, 0 cows
-----------------------------------------------
>>> 2017
Correct, you've guessed the right number
in 4 guesses!
-----------------------------------------------
That's amazing! You took 60.33 seconds.

## Použité technologie
- **Jazyk:** Python  
- **Knihovny:** 
    - random ->  pro generování náhodného čísla
    - time -> pro měření času

## Struktura projektu
- `main.py` - Obsahuje kompletní kód projektu 
- `zadani_projektu.txt` - Plné zadání projektu  
- `README.md` - Tento soubor
- `requirements.txt` - seznam knihoven (i když v tomto projektu jde o standardní knihovny, soubor může být užitečný pro případné budoucí rozšíření projektu).

## Instalace a spuštění
1. **Naklonujte repozitář:**
   git clone https://github.com/MatejLauterkranc/Engeto_project.git

2. Otevřete složku Project 2

3. Spusťte projekt v libovolném prostředí:
    - Jupyter Notebook
    - Visual Studio Code
    - PyCharm
    - nebo přímo v terminálu:
    python main.py

## Kontakt
Máte otázky? Kontaktujte mě na [LinkedIn](https://www.linkedin.com/in/mat%C4%9Bj-lauterkranc-8a9b7a228/) nebo přes e-mail: m.lauterkranc@gmail.com  
 
## Budoucí možné vylepšení
- Přidat funkci pro statistiky: která bude sledovat, kolik her hráč už odehrál, jak dlouho mu trvalo uhádnutí a kolik pokusů potřeboval. Tato funkce by mohla uložit výsledky do souboru.
- Zvážit možnost přidání více herních módů (např. hraní s více číslicemi).
- Šlo by vylepšit i uživatelské rozhraní GUI místo terminálu.
- Nápověda uživateli by taky mohla být vylepšením pokud by si o ní uživatel požádal