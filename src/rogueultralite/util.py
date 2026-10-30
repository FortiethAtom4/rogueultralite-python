def choose_an_option(options: list, prompt: str) -> int:
    '''Prompts the user to choose an option from a list of strings. Returns the index of the chosen option.'''
    if len(options) == 0:
        raise Exception("Attempted to choose an option from an empty list")

    if len(options) == 1:
        return 0

    for i in range(len(options)):
        print(f"{i + 1}: {options[i]}")

    chosen: int = -1
    while chosen == -1:
        try:
            chosen = int(input(prompt))
            if chosen <= 0 or chosen > len(options):
                raise Exception

        except:
            print("Please choose a valid option!")
            chosen = -1

    return chosen - 1

