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

NULL_SOUND = Sound('∅', '∅')

ANY_SOUND = Sound('*', '*')

SYMBOL_TO_SPEC_SOUND = {WORD_BOUNDARY.symbol: WORD_BOUNDARY, NULL_SOUND.symbol: NULL_SOUND, ANY_SOUND.symbol: ANY_SOUND}


def to_symbols(sounds: List[Sound]):
    return ''.join(sound.symbol for sound in sounds)


class Sounds(object):
    def __init__(self, attributes_path):
        self.sounds: Set[Sound] = set()
        self.atts_to_sound: Dict[str, Sound] = dict()
        self.symbols_to_sounds: Dict[str, Sound] = dict()
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
                self.symbols_to_sounds[symbol] = sound
        attributes_file.close()

    def __contains__(self, item) -> bool:
        return self.sounds.__contains__(item)

    def to_codes(self, symbols: List[str]):
        return [self.symbols_to_sounds[symbol].attributes for symbol in symbols]

    def from_symbols_to_sounds(self, symbols: List[str]):
        if symbols == ['']:
            return [NULL_SOUND]
        else:
            return [(self.symbols_to_sounds[symbol] if self.symbols_to_sounds.keys().__contains__(symbol) else
                    SYMBOL_TO_SPEC_SOUND[symbol] )for symbol in symbols]

    def from_codes_to_sounds(self, codes: List[str]):
        if codes == ['']:
            return [NULL_SOUND]
        else:
            return [
                self.atts_to_sound[code] if self.atts_to_sound.keys().__contains__(code) else SYMBOL_TO_SPEC_SOUND[code]
                for code in codes]


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
                if self.sounds.symbols_to_sounds.keys().__contains__(character):
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


def sequences_match(actual_sounds: List[Sound], codes: List[str]):
    if len(actual_sounds) != len(codes):
        return False
    else:
        for index in range(len(actual_sounds)):
            if not (codes[index] == ANY_SOUND.attributes or actual_sounds[index].is_match(codes[index])):
                return False
    return True


class SoundChange(object):
    def __init__(self, i_s: List[str], o_s: List[str], envs: List[List[str]], sounds: Sounds):
        def change_if_empty(input_list, pot_replacement):
            return input_list if input_list != [''] else [pot_replacement]

        self.sounds = sounds

        self.cat_to_symbols = {}
        self.cat_to_attrs = {}
        self._input_sounds = change_if_empty(i_s, NULL_SOUND.symbol)
        self._output_sounds = change_if_empty(o_s, NULL_SOUND.symbol)

        self._prec_env = change_if_empty(envs[0], ANY_SOUND.symbol)
        self._fol_env = change_if_empty(envs[1], ANY_SOUND.symbol)

    def get_in(self):
        return self._input_sounds

    def get_out(self):
        return self._output_sounds

    def get_prec_env(self):
        return self._prec_env

    def get_fol_env(self):
        return self._fol_env

    def get_in_len(self):
        if self.get_in().__contains__(NULL_SOUND.symbol):
            return len(self._input_sounds) - 1
        else:
            return len(self._input_sounds)

    def get_prec_len(self):
        return len(self._prec_env)

    def get_fol_len(self):
        return len(self._fol_env)

    def in_cat(self, sound, category):
        return self.cat_to_symbols[category].__contains__(sound)

    def applies_to(self, pot_prec_env: List[Sound], pot_in: List[Sound], pot_fol_env: List[Sound]) -> bool:
        return sequences_match(pot_prec_env, self._prec_env) and sequences_match(pot_in,
                                                                                 self.get_in()) and sequences_match(
            pot_fol_env, self._fol_env)

    def check_match(self, sound_1, sound_2):
        return sound_1 == sound_2 or self.in_cat(sound_1, sound_2)

    def process(self, word: str):
        prec_len = self.get_prec_len()
        in_len = self.get_in_len()
        fol_len = self.get_fol_len()
        in_pos = 1
        seq_start = in_pos - prec_len
        seq_end = in_pos + in_len + fol_len
        output = WORD_BOUNDARY.symbol
        while len(word) > in_pos:
            if seq_end <= len(word) and seq_start > -1:
                pot_prec_env = word[seq_start:seq_start + prec_len]
                pot_in = NULL_SOUND.symbol if self.get_in()[0] == NULL_SOUND.symbol else word[
                                                                           seq_start + prec_len:seq_start + prec_len + in_len]
                pot_fol_env = word[(seq_start + prec_len + in_len):seq_end]
                if self.applies_to(self.sounds.from_symbols_to_sounds(pot_prec_env),
                                   self.sounds.from_symbols_to_sounds(pot_in),
                                   self.sounds.from_symbols_to_sounds(pot_fol_env)):
                    for index in range(len(self.get_in())):
                        if self.get_out()[index] != NULL_SOUND.symbol:
                            new_sound_code = ''
                            for index_1 in range(len(self.get_out()[index])):
                                if self.get_out()[index][index_1] == '0':
                                    new_sound_code += self.sounds.from_symbols_to_sounds(pot_in)[index].attributes[
                                        index_1]
                                else:
                                    new_sound_code += self.get_out()[index][index_1]
                            new_sound = self.sounds.atts_to_sound[new_sound_code]
                            output += new_sound.symbol
                    if self.get_in()[0] == NULL_SOUND:
                        output += word[in_pos]
                else:
                    output = output + word[in_pos]
            else:
                output = output + word[in_pos]

            in_pos += max(in_len, 1)
            seq_start = in_pos - prec_len
            seq_end = in_pos + in_len + fol_len
        return output


if __name__ == '__main__':
    series = SoundChangeSeries('attributes', 'changes')
    series.apply_sound_changes('corpus')
