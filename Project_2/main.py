"""
projekt_2.py: druhý projekt do Engeto Online Python Akademie

author: Matěj Lauterkranc
email: m.lauterkranc@gmail.com
"""

import random
import time

# Funkce pro generování tajného čísla
def generate_secret_number():
    """Generuje náhodné čtyřmístné číslo s unikátními číslicemi, nezačíná nulou."""
    digits = list(range(1, 10)) # Seznam čísel 1-9 (první číslice nemůže být 0)
    random.shuffle(digits)# Zamíchání pořadí čísel
    secret = [digits.pop(0)]  # první číslo nemůže být nula
    digits += [0]  # přidání nuly pro zbývající číslice
    random.shuffle(digits) # opětovné zamíchání
    secret += random.sample(digits, 3) # Přidání tří dalších unikátních číslic
    secret_number = ""
    return ''.join(map(str, secret)) # Spojení číslic do stringu

# Funkce pro validaci vstupu uživatele
def is_valid_guess(guess):
    """Kontroluje, zda je vstup uživatele validní čtyřmístné číslo.
    - Musí být číslo.
    - Musí mít délku 4.
    - Musí mít unikátní číslice.
    - Nesmí začínat nulou.
    """
    if not guess.isdigit():
        return False, "Input must be numeric."
    if len(guess) != 4:
        return False, "Input must be a 4-digit number."
    if len(set(guess)) != 4:
        return False, "Input must have unique digits."
    if guess[0] == '0':
        return False, "Input cannot start with zero."
    return True, None


# Funkce pro vyhodnocení tipů uživatele
def evaluate_guess(secret, guess):
    """Vyhodnocuje počet bulls a cows mezi tajným číslem a tipem uživatele."""
    bulls = sum(1 for s, g in zip(secret, guess) if s == g)
    cows = sum(1 for g in guess if g in secret) - bulls
    return bulls, cows


# Hlavní část programu
def main():
    """Spustí hru, zobrazí úvodní zprávu a běží v nekonečné smyčce,
    dokud hráč neuhodne správné číslo.
    """
    print("Hi there!")
    print("-----------------------------------------------")
    print("I've generated a random 4 digit number for you.")
    print("Let's play a bulls and cows game.")
    print("-----------------------------------------------")
    
    secret_number = generate_secret_number()
    attempts = 0
    start_time = time.time()

    while True:
        guess = input("Enter a number: ")
        #print(f"Secret number is {secret_number}") # delete show secret number
        valid, error = is_valid_guess(guess)
        if not valid:
            print(f"Invalid input: {error}")
            continue

        attempts += 1
        bulls, cows = evaluate_guess(secret_number, guess)

        if bulls == 4:
            elapsed_time = round(time.time() - start_time, 2)
            print(f"Correct, you've guessed the right number"
                  f" in {attempts} guesses!")
            print(f"That's amazing! You took {elapsed_time} seconds.")
            break
        else:
            print(f"{bulls} bull{'s' if bulls != 1 else ''},"
                  f"{cows} cow{'s' if cows != 1 else ''}")

if __name__ == "__main__":
    main()