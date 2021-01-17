from typing import List, Dict, Set
from Sounds import *


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
                o_s = self.sounds.to_template_sounds(variables[1])
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
    def __init__(self, i_s: List[RichPhone], o_s: List[TemplatePhone], envs: List[List[RichPhone]], sounds: Phones):
        def change_if_null(input_list, pot_replacement):
            return input_list if input_list != [NULL] else [pot_replacement]

        self.sounds = sounds

        self._inp_form = i_s
        self._outp_form = o_s
        while len(o_s) < len(i_s):
            o_s.append(NULL_TEMP_PHONE)

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

        def get_new_sound(old_sound: RichPhone, new_sound: TemplatePhone):
            new_code = ['{']
            for index in range(len(new_sound.code)):
                if new_sound.code[index] == '0':
                    new_code.append(old_sound.code[index])
                else:
                    new_code.append(new_sound.code[index])
            new_code.append('}')
            new_code = ''.join(new_code)
            new_modifiers = old_sound.modifiers.union(new_sound.modifiers_to_add).difference(
                new_sound.modifiers_to_remove)
            return RichPhone(sound(new_code).symbol, new_code[1:len(new_code) - 1], new_modifiers)

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
                if self.get_out()[index] != NULL_TEMP_PHONE:
                    output_seq.append(get_new_sound(inp[index], self.get_out()[index]))
            if self.get_in_form()[0] == NULL_TEMP_PHONE:
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

        def applies_to(p_s: List[RichPhone], i_s: List[RichPhone], f_s: List[RichPhone]) -> bool:
            return of_form(p_s, self._prec_form) and of_form(i_s, self._inp_form) and of_form(f_s, self._fol_form)

        def in_range(i):
            return seq_end(i) <= len(word) and seq_start(i) > -1

        def get_out_seq(i):
            return o_s(i)

        def process_input(self):
            i = 1  # position of the index of beginning of the sequence of sounds to potentially be changed
            output = [WORD_BOUNDARY]
            while len(word) > i:
                if in_range(i) and applies_to(p_s(i), i_s(i), f_s(i)):
                    out_seq = get_out_seq(i)
                    output.extend(out_seq)
                    if in_len == 0:
                        output.append(word[i])
                    i += max(in_len, 1)
                else:
                    output.append(word[i])
                    i += 1

            return output

        return process_input(self)

    def __str__(self):
        return to_symbols(self._inp_form) + ' -> ' + to_symbols(self._outp_form) + ' / ' + to_symbols(
            self._prec_form) + '_' + to_symbols(self._fol_form)


if __name__ == '__main__':
    series = SoundChangeSeries('attributes', 'modifiers', 'changes')
    series.apply_sound_changes('corpus')
