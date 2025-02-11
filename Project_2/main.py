"""
projekt_2.py: druhý projekt Bulls & Cows do Engeto Online Python Akademie


author: Matěj Lauterkranc
email: m.lauterkranc@gmail.com
"""

import random
import time
# -----------------------------------
# Funkce pro generování tajného čísla
# -----------------------------------
def generate_secret_number():
    """Generuje náhodné čtyřmístné číslo s unikátními číslicemi, nezačíná nulou.

    Returns:
        str: Čtyřmístné číslo jako řetezec
    """

    digits = list(range(1, 10)) # Seznam čísel 1-9 (první číslice nemůže být 0)
    random.shuffle(digits) # Zamíchání pořadí čísel
    secret = [digits.pop(0)]  # první číslo nemůže být nula
    digits += [0]  # přidání nuly pro zbývající číslice
    random.shuffle(digits) # opětovné zamíchání
    secret += random.sample(digits, 3) # Přidání tří dalších unikátních číslic
    secret_number = ""
    return ''.join(map(str, secret)) # Spojení číslic do stringu

# ------------------------------------
# Funkce pro validaci vstupu uživatele
# ------------------------------------
def is_valid_guess(guess):
    """Kontroluje, zda je vstup uživatele validní čtyřmístné číslo.
    - Musí být číslo.
    - Musí mít délku 4.
    - Musí mít unikátní číslice.
    - Nesmí začínat nulou.

     Args:
        guess (str): Vstup uživatele

    Returns:
        tuple: (bool, str nebo None)
        - True: Pokud je vstup validní
        - False: Pokud vstup validní není, vrátí chybobou zprávu jinak None.


    """
    if not guess.isdigit():
        return False, "Input must be numeric."
    if len(guess) != 4:
        return False, "Input must be a 4-digit number."
    if len(set(guess)) != 4:
        return False, "Input must have unique digits."
    if guess[0] == '0':
        return False, "Input cannot start with zero."
    return True, None # Při validním vstupu je return True


# Funkce pro vyhodnocení tipů uživatele
def evaluate_guess(secret, guess):
    """Vyhodnocuje počet bulls a cows mezi tajným číslem a tipem uživatele.
    
    Bulls = správná čislice na správné pozici

    Cows = správná číslice na špatné pozici

    Args:
        secret (str): tajné číslo
        guess (str): Tip uživatele

    Returns:
        tuple: (int, int)
        - Počet bulls
        - Počet cows
    """
    bulls = sum(1 for s, g in zip(secret, guess) if s == g)
    cows = sum(1 for g in guess if g in secret) - bulls
    return bulls, cows


# Hlavní část programu
def main():
    """Spustí hru, zobrazí úvodní zprávu a běží v nekonečné smyčce,
    dokud hráč neuhodne správné číslo.
    
    Po uhodnutí čísla program zobrazí počet pokusů a čas potřebný na hádání.
    """
    print("Hi there!")
    print("-----------------------------------------------")
    print("I've generated a random 4 digit number for you.")
    print("Let's play a bulls and cows game.")
    print("-----------------------------------------------")
    
    secret_number = generate_secret_number() # Vygenerování tajného čísla
    attempts = 0 # Počítadlo pokusů
    start_time = time.time() # Uložení počátečního času

    while True:
        guess = input("Enter a number: ")# Uživatel zadá svůj tip
        #print(f"Secret number is {secret_number}") # ladění programu, zakomentovat
        valid, error = is_valid_guess(guess) # ověření zda je vstup validní
        if not valid:
            print(f"Invalid input: {error}")
            continue

        attempts += 1
        bulls, cows = evaluate_guess(secret_number, guess) # vyhodnocení tipu

        if bulls == 4:
            elapsed_time = round(time.time() - start_time, 2) # změření času
            print(f"Correct, you've guessed the right number"
                  f" in {attempts} guesses!")
            print(f"That's amazing! You took {elapsed_time} seconds.")
            break # konec hry
        else:
            print(f"{bulls} bull{'s' if bulls != 1 else ''},"
                  f"{cows} cow{'s' if cows != 1 else ''}")
# Pokud program běží jako hlavní program, zavolá se fce main()
if __name__ == "__main__":
    main()