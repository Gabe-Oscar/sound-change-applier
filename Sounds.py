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


