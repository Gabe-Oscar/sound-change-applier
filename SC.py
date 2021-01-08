from collections import defaultdict
from typing import List

import applyChanges


class SoundChange(object):
    def __init__(self, i_s: str, o_s: str, env: str, series: applyChanges.SoundChangeSeries):
        self.series = series
        self.cat_to_symbols = {}
        self.cat_to_attrs = {}
        self.extract_categories(i_s + o_s + env)
        self._input_sound = self.tokenize(i_s)
        self._output_sound = self.tokenize(o_s, True)
        env_parts = env.split('_')
        self._prec_env = self.tokenize(env_parts[0])
        self._fol_env = self.tokenize(env_parts[1])
        self._surface_form = i_s + ', ' + o_s + ', ' + env
        self._underlying_form = ''.join(self._prec_env) + ''.join(self._input_sound) + ''.join(self._fol_env)

    def extract_categories(self, full_string: str):
        for symbol in full_string:
            if self.series.get_categories().__contains__(symbol):
                self.cat_to_symbols[symbol] = self.series.cat_to_symbols[symbol]

    def tokenize(self, sounds: str, change=False) -> List[str]:
        cat_number = 65
        tokens_list = []
        index = 0

        while index < len(sounds):
            if sounds[index] == '{':
                new_index = sounds.find('}', index)

                attributes_list = [tuple(attribute_to_value.split('=')) for attribute_to_value in
                                   sounds[index + 1:new_index].split('&')]

                while self.cat_to_symbols.keys().__contains__(chr(cat_number)):
                    cat_number += 1
                self.cat_to_symbols[chr(cat_number)] = self.series.get_symbols_of_att(attributes_list)
                self.cat_to_attrs[chr(cat_number)] = attributes_list

                tokens_list.append(chr(cat_number))
                index = new_index + 1
            else:
                tokens_list.append(sounds[index])
                index = index + 1
        return tokens_list

    def get_in(self):
        return ''.join(self._input_sound)

    def get_out(self):
        return ''.join(self._output_sound)

    def get_prec_env(self):
        return ''.join(self._prec_env)

    def get_fol_env(self):
        return ''.join(self._fol_env)

    def get_in_len(self):
        if self.get_in().__contains__('0'):
            return len(self._input_sound)-1
        else:
            return len(self._input_sound)

    def get_prec_len(self):
        return len(self._prec_env)

    def get_fol_len(self):
        return len(self._fol_env)

    def get_full_string(self):
        return self.surface_form

    def in_cat(self, sound, category):
        return self.cat_to_symbols[category].__contains__(sound)

    def applies_to(self, symbol_seq: str) -> bool:
        if len(symbol_seq) != len(self._underlying_form):
            return False
        else:
            for index in range(len(symbol_seq)):
                if symbol_seq[index] != self._underlying_form[index] and not \
                        (self.cat_to_symbols.keys().__contains__(self._underlying_form[index])
                         and self.in_cat(symbol_seq[index], self._underlying_form[index])):
                    return False
        return True

    def check_match(self, sound_1, sound_2):
        return sound_1 == sound_2 or self.in_cat(sound_1, sound_2)

    def find_match(self, word: str, start_index: int = 0):
        match_count = 0
        index = 0
        while (index < len(word) & match_count < len(self._input_sound)):
            if self.check_match(word[index], self._input_sound[match_count]):
                match_count += 1
            else:
                match_count = 0
            index += 1
        if match_count == len(self._input_sound):
            return index
        else:
            return -1

    def process(self, word: str):
        prec_len = self.get_prec_len()
        in_len = self.get_in_len()
        fol_len = self.get_fol_len()
        #in_pos = self.find_match(word)
        in_pos = 1
        seq_start = in_pos - prec_len
        seq_end = in_pos + in_len + fol_len
        output = '#'
        while len(word) > in_pos:
            if seq_end < len(word) and seq_start > -1:
                actual_sounds = word[seq_start:seq_end]
                if self.get_in() == '0':
                    actual_sounds = actual_sounds[:prec_len] + '0' + actual_sounds[prec_len:]
                if self.applies_to(actual_sounds):
                    for index in range(len(self.get_in())):
                        if self.get_out()[index] != '0':
                            if self.cat_to_symbols.keys().__contains__(self.get_out()[index]):
                                attributes = self.series.symbol_to_atts[actual_sounds[prec_len+index]].copy()
                                for new_attribute in self.cat_to_attrs[self.get_out()[index]]:
                                    attributes[new_attribute[0]] = new_attribute[1]

                                output += self.series.get_symbols_of_att([(k, v) for k, v in attributes.items()])[0]
                            else:
                                output += self.get_out()[index]
                    if self.get_in() == '0':
                        output += word[in_pos]
                else:
                    output = output + word[in_pos]
            else:
                output = output + word[in_pos]

            in_pos += max(in_len, 1)
            seq_start = in_pos - prec_len
            seq_end = in_pos + in_len + fol_len
        return output

    def __str__(self):
        return self._surface_form

