'''
Projekt : Textovy analyzator
Tvuj prvni projekt

Zadaní projektu

V tomto projektu bude tvým cílem vytvořit textový analyzátor- program, který se bude umet
prokousat libovolné dlouhým textem a zjistit o něm různé informace.

Ještě než zapneš, budeš pracovat se zadanými předefinovanými texty. Kód seti pak bude lepe
kontrolovat. Tyto texty jsou dostupné zde.

Na začátku souboru vypiš hlavičku, ať' se s tebou můžeme snadněji spojit:
"""
projekt_1.py: první projekt do Engeto Online Python Akademie

author: Petr Svetr
email: petr.svetr@gmail.com
"""
tady bude začínat tvůj kód:

Tvůj program bude obsahovat následující:
1.	Vyžádá si od uživatele přihlašovací jméno a heslo,

2.	zjisti, jestli zadané údaje odpovídají někomu zregistrovaných uživatelů,

3.	pokud je registrovaný, pozdrav jej a umožni mu analyzovat texty,

4.	pokud není registrovaný, upozorni jej a ukonči program.

Registrovaní jsou následující uživatele:
+------+-------------+
| user |   password  |
+------+-------------+
| bob  |     123     |
| ann  |   pass123   |
| mike | password123 |
| liz  |   pass123   |
+------+-------------+

Program nechá uživatele vybrat mezi třemi texty, uloženými v proměnné TEXTS :
•	Pokuť užívateľ vybere takové číslo textu, které není v  zadaní, program jej upozorni a skonči,
•	pokud uživatel zadá jiný vstup nez cislo, program jej rovnez upozorni a skonci.

Pro vybrany text spocita nasledujfcf statistiky:
•	pocet slov,
•	pocet slov zacinajicich velkym pismenem,
•	pocet slov psanych velkymi pismeny,
•	pocet slov psanych malymi pismeny,
•	pocet cisel (ne cifer),
•	sumu vsech cisel (ne cifer) v textu.

Program zobrazi jednoduchy sloupcovy graf, ktery bude reprezentovat cetnost ruznych délek slov
v textu. Napriklad takto:

# ...
 7| * 1
 8| *********** 11
 9| *************** 15
10| ********* 9
11| ********** 10

Po spuštění by měl průběh vypadat následovně:

username:bob
password:123
----------------------------------------
Welcome to the app, bob
We have 3 texts to be analyzed.
----------------------------------------
Enter a number btw. 1 and 3 to select: 1
----------------------------------------
There are 54 words in the selected text.
There are 12 titlecase words.
There are 1 uppercase words.
There are 38 lowercase words.
There are 3 numeric strings.
The sum of all the numbers 8510
----------------------------------------
LEN|  OCCURENCES  |NR.
----------------------------------------
  1|*             |1
  2|*********     |9
  3|******        |6
  4|***********   |11
  5|************  |12
  6|***           |3
  7|****          |4
  8|*****         |5
  9|*             |1
 10|*             |1
 11|*             |1

Pokud uživatel není registrovaný:

username:marek
password:123
unregistered user, terminating the program..

'''