from typing import List, Dict, Set


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
    def __init__(self, symbol: str):
        self.symbol = symbol


class RichPhone(Phone):
    def __init__(self, symbol: str, attributes: str, modifiers: Set[Modifier]):
        super().__init__(symbol + ''.join(modifier.symbol for modifier in modifiers), attributes)
        self.modifiers = modifiers

    def matches(self, other):
        if isinstance(other, Phone):
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


WORD_BOUNDARY = Phone('#', '#')

NULL = Phone('∅', '∅')

ANY_SOUND = Phone('*', '*')

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
                modifier = Modifier(line.strip())
                self.modifiers.add(modifier)
                self.to_modifier[modifier.symbol] = modifier

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
            symbol = self.get_unique_symbol()
            code = k[1:k.index('}')]
            modifiers = self.to_modifiers(k[k.index('}') + 1:len(k)])
            new_rich_phone = RichPhone(symbol,code,modifiers)
            self.symbol_to_sound[symbol] = new_rich_phone
            return new_rich_phone
        elif self.has_symbol(k[0]):
            base_phone = self.symbol_to_sound[k[0]]
            return RichPhone(base_phone.symbol, base_phone.code, self.to_modifiers(k[1:len(k)]) if len(k) > 1 else [])
        elif self.has_code(k):
            return self.code_to_sound[k]
        elif SYMBOL_TO_SPEC_SOUND.keys().__contains__(k):
            return SYMBOL_TO_SPEC_SOUND[k]
        else:
            raise ValueError("No sound corresponding to this symbol or code: " + k)

    def to_sounds(self, keys: str):
        if keys == '':
            return [NULL]
        else:
            return [self.to_sound(key) for key in self.tokenize(keys)]

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
            elif self.to_modifier.keys().__contains__((input_string[index])):
                output_list[len(output_list) - 1] += input_string[index]
            else:
                raise ValueError("invalid token: " + input_string[index])
            index += 1
        return output_list


class SoundChangeSeries(object):
    def __init__(self, attributes_path, modifiers_path, changes_path):
        self.sound_changes: List[SoundChange] = list()
        self.sounds = Phones(attributes_path, modifiers_path)
        self.load_sound_changes(changes_path)

    def load_sound_changes(self, file_path):
        with open(file_path, "r", encoding="utf8") as sound_change_file:
            for sound_change in sound_change_file:
                variables = sound_change.strip().split(',')
                envs = [self.sounds.to_sounds(variable) for variable in variables[2].split('_')]
                i_s = self.sounds.to_sounds(variables[0])
                o_s = self.sounds.to_sounds(variables[1])
                self.sound_changes.append(
                    SoundChange(i_s, o_s, envs, self.sounds))
        sound_change_file.close()

    def apply_sound_changes(self, corpus_file_path):
        def make_processable(raw_word: str):
            sounds = []
            invalid_characters = []
            for character in raw_word:
                if self.sounds.symbol_to_sound.keys().__contains__(character):
                    sounds.append(self.sounds.to_sound(character))
                else:
                    invalid_characters.append(character)
            if len(invalid_characters) > 0:
                print('Following unknown characters in ' + raw_word + ' ignored: ' + invalid_characters.__str__())
            return sounds

        output_words: List[str] = []
        with open(corpus_file_path, "r", encoding="utf8") as corpus:
            for word in [raw_word.strip() for raw_word in corpus]:
                stages: str = word
                out_word: str = [WORD_BOUNDARY] + make_processable(word) + [WORD_BOUNDARY]
                for sound_change in self.sound_changes:
                    new_out_word = sound_change.process(out_word)
                    if new_out_word != out_word:
                        stages += '->' + to_symbols(new_out_word[1:len(new_out_word) - 1])
                    out_word = new_out_word
                output_words.append(stages)
        corpus.close()

        with open("output.txt", "w", encoding="utf8") as f:
            for out_word in output_words:
                print(out_word)
                f.write("%s\n" % out_word)
        f.close()


class SoundChange(object):
    def __init__(self, i_s: List[Phone], o_s: List[Phone], envs: List[List[Phone]], sounds: Phones):
        def change_if_null(input_list, pot_replacement):
            return input_list if input_list != [NULL] else [pot_replacement]

        self.sounds = sounds

        self._inp_form = i_s
        self._outp_form = o_s
        while len(o_s) < len(i_s):
            o_s.append(NULL)

        self._prec_form = change_if_null(envs[0], ANY_SOUND)
        self._fol_form = change_if_null(envs[1], ANY_SOUND)

    def get_in_form(self):
        return self._inp_form

    def get_out(self):
        return self._outp_form

    def get_prec_from(self):
        return self._prec_form

    def get_fol_form(self):
        return self._fol_form

    def get_in_len(self):
        if self.get_in_form().__contains__(NULL):
            return len(self._inp_form) - 1
        else:
            return len(self._inp_form)

    def get_prec_len(self):
        return len(self._prec_form)

    def get_fol_len(self):
        return len(self._fol_form)

    def process(self, word: str):
        sound = self.sounds.to_sound
        prec_len = self.get_prec_len()
        in_len = self.get_in_len()
        fol_len = self.get_fol_len()

        def get_new_sound(old_sound: RichPhone, new_sound: RichPhone):
            new_code = ''
            for index in range(len(new_sound.code)):
                if new_sound.code[index] == '0':
                    new_code += old_sound.code[index]
                else:
                    new_code += new_sound.code[index]
            return RichPhone(sound(new_code).symbol, new_code, new_sound.modifiers)

        def seq_start(i):
            return i - prec_len

        def seq_end(i):
            return i + in_len + fol_len

        def i_s(i):
            start = seq_start(i) + prec_len
            end = start + in_len
            return [NULL] if self.get_in_form()[0].symbol == NULL.symbol else word[start:end]

        def p_s(i):
            return word[seq_start(i):seq_start(i) + prec_len]

        def f_s(i):
            return word[i + in_len:seq_end(i)]

        def o_s(i):
            output_seq = []
            inp = i_s(i)
            for index in range(len(self.get_in_form())):
                if self.get_out()[index] != NULL:
                    output_seq.append(get_new_sound(inp[index], self.get_out()[index]))
            if self.get_in_form()[0] == NULL:
                output_seq.append(word[i])
            return output_seq

        def of_form(actual_sounds: List[Phone], form_sounds: List[Phone]):
            if len(actual_sounds) != len(form_sounds):
                return False
            else:
                for index in range(len(actual_sounds)):
                    if not (form_sounds[index] == ANY_SOUND or actual_sounds[index].matches(form_sounds[index])):
                        return False
            return True

        def applies_to(p_s: List[Phone], i_s: List[Phone], f_s: List[Phone]) -> bool:
            return of_form(p_s, self._prec_form) and of_form(i_s, self._inp_form) and of_form(f_s, self._fol_form)

        def in_range(i):
            return seq_end(i) <= len(word) and seq_start(i) > -1

        def get_out_seq(i):
            return word[i] if not in_range(i) or not applies_to(p_s(i), i_s(i), f_s(i)) else o_s(i)

        def process_input():
            i = 1  # position of the index of beginning of the sequence of sounds to potentially be changed
            output = [WORD_BOUNDARY]
            while len(word) > i:
                if in_range(i) and applies_to(p_s(i), i_s(i), f_s(i)):
                    out_seq = get_out_seq(i)
                    output.extend(out_seq)
                    i += max(in_len, 1)
                else:
                    output.append(word[i])
                    i += 1

            return output

        return process_input()

    def __str__(self):
        return to_symbols(self._inp_form) + ' -> ' + to_symbols(self._outp_form) + ' / ' + to_symbols(self._prec_form) + '_' + to_symbols(self._fol_form)

if __name__ == '__main__':
    series = SoundChangeSeries('attributes', 'modifiers', 'changes')
    series.apply_sound_changes('corpus')
