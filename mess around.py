
import string
import pynini
from pynini.lib import rewrite
letters = string.ascii_lowercase
letters_and_more = string.ascii_lowercase + "_" + " "
sigma_star = pynini.closure(pynini.union(*letters_and_more)).optimize()

rotated_letters = letters[1:] + letters[0]
cipher_pairs = zip(letters, rotated_letters)

cipher = pynini.string_map(cipher_pairs).closure().optimize()

