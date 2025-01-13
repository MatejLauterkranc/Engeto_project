# Program na začátku ověří uživatele, má 3 pokusy na ověření
# Po uspěšném ověření mu nabídne k víběru číslo textu na ověření
# Po výběru textu se text zobrazí a následně se zobrazí další informace,
# které text analyzují

'''
projekt_1.py: první projekt do Engeto Online Python Akademie

author: Matěj Lauterkranc
email: m.lauterkranc@gmail.com
'''
TEXTS = ['''
Situated about 10 miles west of Kemmerer,
Fossil Butte is a ruggedly impressive
topographic feature that rises sharply
some 1000 feet above Twin Creek Valley
to an elevation of more than 7500 feet
above sea level. The butte is located just
north of US 30N and the Union Pacific Railroad,
which traverse the valley. ''',
'''At the base of Fossil Butte are the bright
red, purple, yellow and gray beds of the Wasatch
Formation. Eroded portions of these horizontal
beds slope gradually upward from the valley floor
and steepen abruptly. Overlying them and extending
to the top of the butte are the much steeper
buff-to-white beds of the Green River Formation,
which are about 300 feet thick.''',
'''The monument contains 8198 acres and protects
a portion of the largest deposit of freshwater fish
fossils in the world. The richest fossil fish deposits
are found in multiple limestone layers, which lie some
100 feet below the top of the butte. The fossils
represent several varieties of perch, as well as
other freshwater genera and herring similar to those
in modern oceans. Other fish such as paddlefish,
garpike and stingray are also present.'''
]

separator = "-"*50

# List of registered users

Registered_users = {
    "bob": "123",
    "ann": "pass123",
    "mike": "password123",
    "liz": "pass123",
    }

# verification eneter user data
# User will have multiple attempts to log in
attempts = 3  # number of attempts
 
while attempts > 0:
    username = input("Please enter your Username: ").strip()
    password = input("Please enter your Password: ").strip()

    if username in Registered_users and Registered_users[username] == password:
        print(separator)
        print(f"Welcome to the app, ´{username}´"
              "\nWe have 3 texts to be analyzed."
              )
        print(separator)
        break
    else:
        attempts -= 1
        if attempts == 0:
            print(f"You have entered invalid login details 3 times. "
                  f"Exiting the program."
                  )
            exit()  # Terminate the program after 3 failed attempts
        print(f"You have entered invalid login details or you are not registered. "
              f"You have {attempts} attempts left.\n")

# Ask user get number of text for analyze
count_text = len(TEXTS)

choise = input(f"Choose number of text 1 to {count_text}: ").strip()
print (separator)

# check if the input is number and validate
if choise.isdigit():
    choise = int(choise)
    if 1<= choise <= count_text:
        selec_text = (TEXTS[choise -1])
        print(f"You choose {choise}"
              "\n"
              f"{separator}\n"
              f"{selec_text}"
              )
        print(separator)

        # analyze text
        words = [word.strip(",.!?") for word in selec_text.split()]
        count_words = len(words) # Numer of words in the text

        # Inicializace statistik
        capitalized_count = 0
        uppercase_count = 0
        lowercase_count = 0
        number_count = 0
        numeric_sum = 0
        lengths_frequency = {} 

        # Analysis in one cycle
        for word in words:
            if word.istitle():
                capitalized_count += 1 # Number of words beginning with a capital letter
            if word.isupper() and word.isalpha(): # number of words capitalized
                uppercase_count += 1
            if word.islower():
                lowercase_count += 1 # number of words in lower case
            if word.isdigit():
                number_count += 1 #  number of numbers (not digits)
                numeric_sum += int(word) #sum of all the numbers (not digits) in the text
            word_length = len(word)
            lengths_frequency[word_length] = lengths_frequency.get(word_length, 0) + 1 #  counting the frequency of word lengths in the text
        
        print(f"There are {count_words} words in the selected text.")
        print(f"There are {capitalized_count} titlecase words.")
        print(f"There are {uppercase_count} uppercase words.")
        print(f"There are {lowercase_count} lowercase words.")
        print(f"There are {number_count} numeric strings.")
        print(f"The sum of all the numbers:"
              f"{numeric_sum:,}".replace(",", " ")) # number formatting

        # Create frequency chart of word lengths
        print("\nLEN|  OCCURENCES  |NR.")
        max_frequency = max(lengths_frequency.values())
        for length, frequency in sorted(lengths_frequency.items()):
            print(f"{length:<3}| {'*' * frequency:<{max_frequency}} | {frequency}")
    else:
        print("The number entered is not in the range of available texts")
        exit()
else:
    print("Invalid input")
    exit()

