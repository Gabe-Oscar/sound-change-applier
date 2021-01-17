from typing import *


class Phone(object):
    def __init__(self, symbol: str, attributes: str):
        self.symbol = symbol
        self.code = attributes
        self.category_status = attributes.__contains__('0')

    def matches(self, other):
        if len(self.code) != len(other.code):
            return self == ANY_SOUND
        for index in range(len(self.code)):
            if self.code[index] != '0' and other.code[index] != '0' and self.code[index] != other.code[index]:
                return False
        return True

    def is_category(self):
        return self.category_status

    def get_code(self):
        return self.code

    def get_symbol(self):
        return self.symbol

    def __str__(self):
        return self.get_symbol()


class Modifier(object):
    def __init__(self, symbol: str, is_diacritic: bool):
        self._symbol = symbol
        self._is_diacritic = is_diacritic

    def get_symbol(self):
        return self._symbol

    def is_diacritic(self):
        return self._is_diacritic


ANY_MODIFIER = Modifier('*', False)


class RichPhone(Phone):
    def __init__(self, symbol: str, attributes: str, modifiers: Set[Modifier]):
        def compare_by_diacritic_status(a: Modifier, b: Modifier) -> int:
            return 0 if a.is_diacritic == b.is_diacritic else -1 if a.is_diacritic else 1

        super().__init__(symbol + ''.join(modifier.get_symbol() for modifier in
                                          sorted(list(modifiers), key=lambda mod: mod.is_diacritic(), reverse=True)),
                         attributes)
        self.modifiers = modifiers

    def matches(self, other):
        if self == ANY_SOUND or other == ANY_SOUND:
            return True
        if not isinstance(other, RichPhone) and isinstance(other, Phone):
            return super().matches(other)
        elif isinstance(other, RichPhone):
            if super(RichPhone, self).matches(other):
                if self.modifiers.__eq__(other.modifiers):
                    return True
                elif self.category_status:
                    return self.modifiers.issubset(other.modifiers)
                elif other.category_status:
                    return other.modifiers.issubset(self.modifiers)
        return False
    #  self.base.matches(other.base) and self.modifiers.__eq__(other.modifiers)


class TemplatePhone(Phone):
    def __init__(self, symbol: str, attributes: str, modifiers_to_add: Set[Modifier],
                 modifiers_to_remove: Set[Modifier]):
        self.modifiers_to_add = modifiers_to_add
        self.modifiers_to_remove = modifiers_to_remove
        modifiers_to_add_symbol = ' '.join([('+' + modifier.get_symbol()) for modifier in modifiers_to_add])
        modifiers_to_remove_symbol = ' '.join([('-' + modifier.get_symbol()) for modifier in modifiers_to_remove])
        super().__init__(symbol + modifiers_to_add_symbol + modifiers_to_remove_symbol, attributes)


NULL_TEMP_PHONE = TemplatePhone('∅', '∅', set(), set())
WORD_BOUNDARY = Phone('#', '#')

NULL = RichPhone('∅', '∅', set())

ANY_SOUND = RichPhone('*', '*', set())

SYMBOL_TO_SPEC_SOUND = {WORD_BOUNDARY.symbol: WORD_BOUNDARY, NULL.symbol: NULL, ANY_SOUND.symbol: ANY_SOUND}


def to_symbols(sounds: List[Phone]):
    return ''.join(sound.symbol for sound in sounds)


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

    def to_sound(self, k: str):
        if k[0] == '{':
            code = k[1:k.index('}')]
            modifiers = k[k.index('}') + 1:len(k)]
            return self.to_sound(self.add_category(code).symbol + modifiers)
        elif self.has_symbol(k[0]):
            base_phone = self.symbol_to_sound[k[0]]
            return RichPhone(base_phone.symbol, base_phone.code,
                             set(self.to_modifiers(k[1:len(k)]) if len(k) > 1 else []))
        elif SYMBOL_TO_SPEC_SOUND.keys().__contains__(k):
            return SYMBOL_TO_SPEC_SOUND[k]
        else:
            raise ValueError("No sound corresponding to this symbol or code: " + k)

    def to_sounds(self, keys: str):
        if keys == '':
            return [NULL]
        else:
            return [self.to_sound(key) for key in self.tokenize(keys)]

    def to_template_sound(self, k: str):
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

        return TemplatePhone(base_phone.symbol, base_phone.code, mod_to_add, mod_to_remove)

    def to_template_sounds(self, keys: str):
        if keys == '':
            return [NULL_TEMP_PHONE]
        else:
            return [self.to_template_sound(token) for token in self.tokenize(keys)]

    def to_modifiers(self, keys: str):
        return [self.to_modifier[key] for key in keys]

    def tokenize(self, input_string: str) -> List[str]:
        output_list = []
        index = 0
        while index < len(input_string):
            if self.has_symbol(input_string[index]) or input_string[index] in SYMBOL_TO_SPEC_SOUND.keys():
                output_list.append(input_string[index])
            elif input_string[index] == '{':
                end_index = input_string.find("}", index) + 1
                output_list.append(input_string[index:end_index])
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
