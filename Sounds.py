from typing import *


class Phone(object):
    '''represents a bare sound consisting of a symbol and a code specifying some basic attributes'''
    def __init__(self, symbol: str, attributes: str):
        self.symbol = symbol
        self.code = attributes    #each digit corresponds to a specific variable specified by the attributes file
        self.category_status = attributes.__contains__('0')

    def matches(self, other):
        '''returns whether the attributes of this Phone correspond to those specified by another Phone object'''
        if len(self.code) != len(other.code):
            return self == ANY_SOUND
        for index in range(len(self.code)):
            # '0' means 'unspecified', i.e. that it doesn't matter what the attribute at that position is
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
    '''represents a specific manner in which a sound is articulated that varies from its "base" form'''
    def __init__(self, symbol: str, is_diacritic: bool):
        self._symbol = symbol
        self._is_diacritic = is_diacritic #this is stored to ensure that diacritics appear correctly with symbols

    def get_symbol(self):
        return self._symbol

    def is_diacritic(self):
        return self._is_diacritic


ANY_MODIFIER = Modifier('*', False)


class RichPhone(Phone):
    def __init__(self, symbol: str, attributes: str, modifiers: Set[Modifier], stress: str = '*'):

        super().__init__(symbol + ''.join(modifier.get_symbol() for modifier in
                                          sorted(list(modifiers), key=lambda mod: mod.is_diacritic(), reverse=True)),
                         attributes)
        self.stress = stress
        self.modifiers = modifiers

    def matches(self, other):
        if self == ANY_SOUND or other == ANY_SOUND:
            return True
        if not isinstance(other, RichPhone):
            if isinstance(other, TemplatePhone):
                return other.matches(self)
            elif isinstance(other, Phone):
                return super().matches(other)
        elif isinstance(other, RichPhone):
            if super(RichPhone, self).matches(other):
                if self.stress == other.stress or other.stress == '*' or self.stress == '*':
                    if self.modifiers.__eq__(other.modifiers):
                        return True
                    elif self.category_status:
                        return self.modifiers.issubset(other.modifiers)
                    elif other.category_status:
                        return other.modifiers.issubset(self.modifiers)
        return False
    #  self.base.matches(other.base) and self.modifiers.__eq__(other.modifiers)


class TemplatePhone(Phone):
    def __init__(self, symbol: str, attributes: str, modifiers_to_have: Set[Modifier],
                 modifiers_not_to_have: Set[Modifier], stress='*'):
        self.stress = stress
        self.modifiers_to_add = modifiers_to_have
        self.modifiers_to_remove = modifiers_not_to_have
        modifiers_to_add_symbol = ' '.join([('+' + modifier.get_symbol()) for modifier in modifiers_to_have])
        modifiers_to_remove_symbol = ' '.join([('-' + modifier.get_symbol()) for modifier in modifiers_not_to_have])
        super().__init__(symbol + modifiers_to_add_symbol + modifiers_to_remove_symbol, attributes)

    def matches(self, other):
        if isinstance(other, RichPhone):
            if not [self.stress, other.stress].__contains__('*') and self.stress != other.stress:
                return False
            elif not self.modifiers_to_add.issubset(other.modifiers):
                return False
            elif len(other.modifiers.intersection(self.modifiers_to_remove)) > 0:
                return False
        return super().matches(other)


NULL_TEMP_PHONE = TemplatePhone('∅', '∅', set(), set())
WORD_BOUNDARY = Phone('#', '#')

NULL = RichPhone('∅', '∅', set(), '*')

ANY_SOUND = RichPhone('*', '*', set(), '*')

SYMBOL_TO_SPEC_SOUND = {WORD_BOUNDARY.symbol: WORD_BOUNDARY, NULL.symbol: NULL, ANY_SOUND.symbol: ANY_SOUND}

PRIMARY_STRESS = 'ˈ'
SECONDARY_STRESS = 'ˌ'
UNSTRESSED = '.'

STRESSES = {PRIMARY_STRESS, SECONDARY_STRESS, UNSTRESSED}

VALID_CHARACTERS = set().union((STRESSES)).union(SYMBOL_TO_SPEC_SOUND.keys()).union()


def to_symbols(sounds: List[Phone]):
    return ''.join(sound.symbol for sound in sounds)
