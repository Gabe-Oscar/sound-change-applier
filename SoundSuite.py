import re

from Sounds import *
from Syllable import Syllable, Shell, Nucleus


class Phones(object):
    def __init__(self, attributes_path, modifiers_path):
        self.sounds: Set[Phone] = set()
        self.modifiers: Set[Modifier] = set()
        self.to_modifier: Dict[str, Modifier] = dict()
        self.code_to_sound: Dict[str, Phone] = dict()
        self.symbol_to_sound: Dict[str, Phone] = dict()
        self.load_attributes(attributes_path)
        self.load_modifiers(modifiers_path)
        self.next_cat_symbol = 65

    def load_attributes(self, file_path):
        with open(file_path, "r", encoding="utf8") as attributes_file:
            attributes_file.__next__()
            for line in attributes_file:
                attributes = line.strip().split(',')[1]
                symbol = line[0]
                sound = Phone(symbol, attributes)
                self.sounds.add(sound)
                self.code_to_sound[attributes] = sound
                self.symbol_to_sound[symbol] = sound

        attributes_file.close()

    def load_modifiers(self, file_path):
        with open(file_path, "r", encoding="utf8") as modifiers_file:
            modifiers_file.__next__()
            for line in modifiers_file:
                split_line = line.strip().split(',')
                symbol = split_line[0]
                is_diacritic = split_line[1]
                modifier = Modifier(symbol, is_diacritic)
                self.modifiers.add(modifier)
                self.to_modifier[modifier.get_symbol()] = modifier

    def __contains__(self, item) -> bool:
        return self.sounds.__contains__(item)

    def has_code(self, pot_code: str):
        return self.code_to_sound.keys().__contains__(pot_code)

    def has_symbol(self, pot_symbol: str):
        return self.symbol_to_sound.keys().__contains__(pot_symbol)

    def to_codes(self, symbols: List[str]):
        return [self.symbol_to_sound[symbol].code for symbol in symbols]

    def get_unique_symbol(self) -> str:
        while self.symbol_to_sound.keys().__contains__(chr(self.next_cat_symbol)):
            self.next_cat_symbol += 1
        return chr(self.next_cat_symbol)

    def add_category(self, code: str) -> Phone:
        if self.has_code(code):
            return self.code_to_sound[code]
        else:
            category = Phone(self.get_unique_symbol(), code)
            self.sounds.add(category)
            self.symbol_to_sound[chr(self.next_cat_symbol)] = category
            return category

    def to_sound(self, k: str, stress: str = '*'):
        if k[0] == '{':
            code = k[1:k.index('}')]
            modifiers = k[k.index('}') + 1:len(k)]
            return self.to_sound(self.add_category(code).symbol + modifiers, stress)
        elif self.has_symbol(k[0]):
            base_phone = self.symbol_to_sound[k[0]]
            return RichPhone(base_phone.symbol, base_phone.code,
                             set(self.to_modifiers(k[1:len(k)]) if len(k) > 1 else []), stress)
        elif SYMBOL_TO_SPEC_SOUND.keys().__contains__(k):
            return SYMBOL_TO_SPEC_SOUND[k]
        else:
            raise ValueError("No sound corresponding to this symbol or code: " + k)

    def to_sounds(self, keys: str):
        if keys == '':
            return [NULL]
        else:
            return [self.to_sound(key[1:], key[0]) for key in self.tokenize(keys, inc_stress=True)]

    def to_template_sound(self, k: str, stress='*'):
        mod_to_add = set()
        mod_to_remove = set()
        if k[0] == '{':
            code = k[1:k.index('}')]
            modifiers = k[k.index('}') + 1:len(k)]
            return self.to_template_sound(self.add_category(code).symbol + modifiers)
        elif self.has_symbol(k[0]):
            base_phone = self.symbol_to_sound[k[0]]
        index = 1
        while index < len(k):
            if k[index] == '+':
                mod_to_add.add(self.to_modifier[k[index + 1]])
            elif k[index] == '-':
                mod_to_remove.add(self.to_modifier[k[index + 1]])
            else:
                raise ValueError(k[index])
            index += 2

        return TemplatePhone(base_phone.symbol, base_phone.code, mod_to_add, mod_to_remove, stress)

    def to_template_sounds(self, keys: str):
        if keys == '':
            return [NULL_TEMP_PHONE]
        else:
            return [self.to_template_sound(key[1:], key[0]) for key in self.tokenize(keys, inc_stress=True)]

    def to_modifiers(self, keys: str):
        return [self.to_modifier[key] for key in keys]

    def tokenize(self, input_string: str, inc_stress=False) -> List[str]:
        output_list = []
        index = 0
        stress = '*' if inc_stress else ''
        while index < len(input_string):
            if STRESSES.__contains__(input_string[index]):
                stress = input_string[index]
                index += 1
            if self.has_symbol(input_string[index]) or input_string[index] in SYMBOL_TO_SPEC_SOUND.keys():
                output_list.append(stress + input_string[index])
            elif input_string[index] == '{':
                end_index = input_string.find("}", index) + 1
                output_list.append(stress + input_string[index:end_index])
                index = end_index - 1
            elif input_string[index] in {'+', '-'}:
                output_list[len(output_list) - 1] += input_string[index:index + 2]
                index += 2
            elif self.to_modifier.keys().__contains__((input_string[index])):
                output_list[len(output_list) - 1] += input_string[index]
            else:
                raise ValueError("invalid token: " + input_string[index])
            index += 1
        return output_list
