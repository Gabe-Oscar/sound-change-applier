from typing import List, Dict, Set


class Sound(object):
    def __init__(self, symbol: str, attributes: str):
        self.symbol = symbol
        self.attributes = attributes

    def is_match(self, attributes: str):
        if len(attributes) != len(self.attributes):
            return attributes == ANY_SOUND
        for index in range(len(attributes)):
            if attributes[index] != '0' and attributes[index] != self.attributes[index]:
                return False
        return True

    def __str__(self):
        return self.symbol


WORD_BOUNDARY = Sound('#', '#')

NULL = Sound('∅', '∅')

ANY_SOUND = Sound('*', '*')

SYMBOL_TO_SPEC_SOUND = {WORD_BOUNDARY.symbol: WORD_BOUNDARY, NULL.symbol: NULL, ANY_SOUND.symbol: ANY_SOUND}


def to_symbols(sounds: List[Sound]):
    return ''.join(sound.symbol for sound in sounds)


class Sounds(object):
    def __init__(self, attributes_path):
        self.sounds: Set[Sound] = set()
        self.atts_to_sound: Dict[str, Sound] = dict()
        self.symbol_to_sound: Dict[str, Sound] = dict()
        self.load_attributes(attributes_path)

    def load_attributes(self, file_path):
        with open(file_path, "r", encoding="utf8") as attributes_file:
            attributes_file.__next__()
            for line in attributes_file:
                attributes = line.strip().split(',')[1]
                symbol = line[0]
                sound = Sound(symbol, attributes)
                self.sounds.add(sound)
                self.atts_to_sound[attributes] = sound
                self.symbol_to_sound[symbol] = sound
        attributes_file.close()

    def __contains__(self, item) -> bool:
        return self.sounds.__contains__(item)

    def has_code(self, pot_code: str):
        return self.atts_to_sound.keys().__contains__(pot_code)

    def has_symbol(self, pot_symbol: str):
        return self.symbol_to_sound.keys().__contains__(pot_symbol)

    def to_codes(self, symbols: List[str]):
        return [self.symbol_to_sound[symbol].attributes for symbol in symbols]

    def to_sound(self, k: str):
        return self.symbol_to_sound[k] if self.has_symbol(k) else self.atts_to_sound[k] if self.has_code(k) \
            else SYMBOL_TO_SPEC_SOUND[k]

    def to_sounds(self, keys: List[str]):
        if keys == ['']:
            return [NULL]
        else:
            return [self.to_sound(key) for key in keys]


class SoundChangeSeries(object):

    def __init__(self, attributes_path, changes_path):
        self.sound_changes: List[SoundChange] = list()
        self.sounds = Sounds(attributes_path)
        self.load_sound_changes(changes_path)

    def load_sound_changes(self, file_path):
        with open(file_path, "r", encoding="utf8") as sound_change_file:
            for sound_change in sound_change_file:
                variables = sound_change.strip().split(',')
                envs = [variable.split('.') for variable in variables[2].split('_')]
                self.sound_changes.append(
                    SoundChange(variables[0].split('.'), variables[1].split('.'), envs, self.sounds))
        sound_change_file.close()

    def apply_sound_changes(self, corpus_file_path):
        def make_processable(raw_word: str):
            valid_characters = []
            invalid_characters = []
            for character in raw_word:
                if self.sounds.symbol_to_sound.keys().__contains__(character):
                    valid_characters.append(character)
                else:
                    invalid_characters.append(character)
            if len(invalid_characters) > 0:
                print('Following unknown characters in ' + raw_word + ' ignored: ' + invalid_characters.__str__())
            return ''.join(valid_characters)

        output_words: List[str] = []
        with open(corpus_file_path, "r", encoding="utf8") as corpus:
            for word in [make_processable(raw_word.strip()) for raw_word in corpus]:
                stages: str = word
                out_word: str = WORD_BOUNDARY.symbol + word + WORD_BOUNDARY.symbol
                for sound_change in self.sound_changes:
                    out_word = sound_change.process(out_word)
                    stages += '->' + out_word[1:len(out_word) - 1]
                output_words.append(stages)
        corpus.close()

        with open("output.txt", "w", encoding="utf8") as f:
            for out_word in output_words:
                print(out_word)
                f.write("%s\n" % out_word)
        f.close()


class SoundChange(object):
    def __init__(self, i_s: List[str], o_s: List[str], envs: List[List[str]], sounds: Sounds):
        def change_if_empty(input_list, pot_replacement):
            return input_list if input_list != [''] else [pot_replacement]

        self.sounds = sounds

        self._inp_form = change_if_empty(i_s, NULL.symbol)
        self._outp_form = change_if_empty(o_s, NULL.symbol)

        self._prec_form = change_if_empty(envs[0], ANY_SOUND.symbol)
        self._fol_form = change_if_empty(envs[1], ANY_SOUND.symbol)

    def get_in_form(self):
        return self._inp_form

    def get_out(self):
        return self._outp_form

    def get_prec_from(self):
        return self._prec_form

    def get_fol_form(self):
        return self._fol_form

    def get_in_len(self):
        if self.get_in_form().__contains__(NULL.symbol):
            return len(self._inp_form) - 1
        else:
            return len(self._inp_form)

    def get_prec_len(self):
        return len(self._prec_form)

    def get_fol_len(self):
        return len(self._fol_form)

    def process(self, word: str):
        sounds = self.sounds.to_sounds
        sound = self.sounds.to_sound
        prec_len = self.get_prec_len()
        in_len = self.get_in_len()
        fol_len = self.get_fol_len()

        def get_new_sound(old_symbol: str, new_code_template: str):
            new_code = ''
            for index in range(len(new_code_template)):
                if new_code_template[index] == '0':
                    new_code += sound(old_symbol).attributes[index]
                else:
                    new_code += new_code_template[index]
            return sound(new_code)

        def seq_start(i):
            return i - prec_len

        def seq_end(i):
            return i + in_len + fol_len

        def i_s(i):
            start = seq_start(i) + prec_len
            end = start + in_len
            return NULL.symbol if self.get_in_form()[0] == NULL.symbol else word[start:end]

        def p_s(i):
            return word[seq_start(i):seq_start(i) + prec_len]

        def f_s(i):
            return word[i + in_len:seq_end(i)]

        def o_s(i):
            output_seq = ''
            inp = i_s(i)
            for index in range(len(self.get_in_form())):
                if self.get_out()[index] != NULL.symbol:
                    output_seq += get_new_sound(inp, self.get_out()[index]).symbol
            if self.get_in_form()[0] == NULL:
                output_seq += word[i]
            return output_seq

        def of_form(actual_sounds: List[Sound], codes: List[str]):
            if len(actual_sounds) != len(codes):
                return False
            else:
                for index in range(len(actual_sounds)):
                    if not (codes[index] == ANY_SOUND.attributes or actual_sounds[index].is_match(codes[index])):
                        return False
            return True

        def applies_to(p_s: List[Sound], i_s: List[Sound], f_s: List[Sound]) -> bool:
            return of_form(p_s, self._prec_form) and of_form(i_s, self._inp_form) and of_form(f_s, self._fol_form)

        def in_range(i):
            return seq_end(i) <= len(word) and seq_start(i) > -1

        def get_out_seq(i):
            return o_s(i) if in_range(i) and applies_to(sounds(p_s(i)), sounds(i_s(i)), sounds(f_s(i))) else \
                word[i]

        def process_input():
            i = 1  # position of the index of beginning of the sequence of sounds to potentially be changed
            output = WORD_BOUNDARY.symbol
            while len(word) > i:
                output += get_out_seq(i)
                i += max(in_len, 1)

            return output

        return process_input()


if __name__ == '__main__':
    series = SoundChangeSeries('attributes', 'changes')
    series.apply_sound_changes('corpus')
