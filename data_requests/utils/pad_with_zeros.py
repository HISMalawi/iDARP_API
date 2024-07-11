import random
import string


class PadZeros:

    @staticmethod
    def pad(number):
        # Convert the number to a string
        number_str = str(number)

        # Calculate the number of zeros needed to pad to 6 digits
        zeros_needed = 6 - len(number_str)

        # Pad the string with zeros in front
        padded_number = '0' * zeros_needed + number_str

        return padded_number

    @staticmethod
    def generate_random_string(length):
        characters = string.ascii_letters + string.digits  # Letters and digits
        random_string = ''.join(random.choice(characters) for _ in range(length))
        return random_string
