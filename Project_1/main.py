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

# List of registered users

Registered_users = {
    "bob": "123",
    "ann": "pass123",
    "mike": "password123",
    "liz": "pass123"
}

# verification eneter user data
# User will have multiple attempts to log in
attempts = 3  # number of attempts
 
while attempts > 0:
    username = input("Please enter your Username: ").strip()
    password = input("Please enter your Password: ").strip()

    if username in Registered_users and Registered_users[username] == password:
        print(f"welcome ´{username}´, you have permission to analyse texts")
        break
    else:
        attempts -= 1
        if attempts > 0:
            print("You have entered invalid login details or you are not registered")

# Ask user get number of text for analyze
count_text = len(TEXTS)

choise = input(f"You have {count_text} texts available."
               f"Choose number of text 1 to {count_text}: "
               )

# check if the input is number and validate

if choise.isdigit():
    choise = int(choise)
    if 1<= choise <= count_text:
        selec_text = (TEXTS[choise -1])
        print(f"You choose {choise}"
              f"{selec_text}")
        
        # analyze text
        words = selec_text.split() # split text into word
        count_words = len(words)

        capitalized_count = 0 # Number of words beginning with a capital letter
        for word in words:
            if word[0].isupper():
                capitalized_count += 1 
        
        uppercase_count = 0 # number of words capitalized
        for word in words:
            if word.isupper():
                uppercase_count += 1

        lowercase_count = 0 # number of words in lower case
        for word in words:
            if word.lower():
                lowercase_count += 1

        number_count = 0 #  number of numbers (not digits)
        for number in words:
            if number.isdigit():
                number_count += 1
        sum_of_all_number = 0 #sum of all the numbers (not digits) in the text
        for number in words:
            if number.isdigit():
                sum_of_all_number += int(number)
        
        print(f"There are {count_words} words in the selected text.")
        print(f"There are {capitalized_count} titlecase words.")
        print(f"There are {uppercase_count} uppercase words.")
        print(f"There are {lowercase_count} lowercase words.")
        print(f"There are {number_count} numeric strings.")
        print(f"The sum of all the numbers {sum_of_all_number}")
    else:
        print("The number entered is not in the range of available texts")
else:
    print("Invalid input")

