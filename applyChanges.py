from tokenize import String
from typing import List, Dict, Set

from Inventory import Inventory
from SoundSuite import Phones
from Sounds import *
import pyninico

class SoundChangeSeries(object):
    def __init__(self, distinctive_features_path, changes_path, inventory: Inventory):
        self.inventory = inventory
        self.sound_changes: List[SoundChange] = list()
        self.inventory.load_features(distinctive_features_path)
        self.load_sound_changes(changes_path)

    def load_sound_changes(self, file_path):
        """loads sound changes from file"""

        def process_feature_stuff(text: String):
            text = text.replace(" ", "")
            text = text.replace("][", "|")[1:len(text) - 1]
            final_text = [feature_bundle.split(",") for feature_bundle in text.split("|")]
            return final_text

        def process_target(target_text: String):
            target_strings = process_feature_stuff(target_text)
            targets = [self.inventory.select_active_sounds(target_string) for target_string in target_strings]
            return targets

        def process_output(inputs: Set, output_text: String) -> Dict:
            output_strings = process_feature_stuff(output_text)
            output_dict = dict()
            for input in inputs:
                output_dict[input] = self.inventory.get_variant(input, output_strings)
            return output_dict

        def process_envs(env_text: String):
            env_texts = env_text.split('_')
            if env_texts[0] == "":
                env_texts[0] = "[*]"
            if env_texts[1] == "":
                env_texts[1] = "[*]"
            return process_target(env_texts[0]), process_target(env_texts[1])

        with open(file_path, "r", encoding="utf8") as sound_change_file:
            for sound_change in sound_change_file:
                if sound_change[:3] == "add":
                    new_sounds = sound_change.split(" ")[1].split(",")
                    for sound in new_sounds:
                        self.inventory.add_active_sound(sound)

                variables = sound_change.strip().split('/')
                # create a tuple whose first element consists of the sound sequence composing the preceding environment
                # and whose second element consists of the sound sequence composing the following following environment
                envs = tuple(process_envs(variables[2]))

                # create the sequence of sound templates composing the input
                i_s = process_target(variables[0])
                # crate the sequence of sounnd templates composing the output
                o_s = process_output(i_s, variables[1])
                self.sound_changes.append(
                    SoundChange(i_s, o_s, envs, self.sounds))
        sound_change_file.close()

    def apply_sound_changes(self, corpus_file_path):
        """applies loaded sound changes to a corpus"""

        def make_processable(raw_word: str):
            # removes any invalid characters (i.e. any characters for which there is no information)
            all_valid_characters = VALID_CHARACTERS.union(self.sounds.symbol_to_sound.keys())
            valid_chars = []
            invalid_characters = []
            for character in raw_word:
                if all_valid_characters.__contains__(character):
                    valid_chars.append(character)
                else:
                    invalid_characters.append(character)
            if len(invalid_characters) > 0:
                print('Following unknown characters in ' + raw_word + ' ignored: ' + invalid_characters.__str__())
            return valid_chars

        word_evolution: List[str] = []
        with open(corpus_file_path, "r", encoding="utf8") as corpus:
            for word in [raw_word.strip() for raw_word in corpus]:
                stages: str = word
                out_word: List[Phone] = [WORD_BOUNDARY] + self.sounds.to_sounds(make_processable(word)) + [
                    WORD_BOUNDARY]
                for sound_change in self.sound_changes:
                    new_out_word = sound_change.process(out_word)
                    if new_out_word != out_word:  # if the word has changed as a result of the sound channge
                        stages += '->' + to_symbols(new_out_word[1:len(new_out_word) - 1])
                    out_word = new_out_word
                word_evolution.append(stages)
        corpus.close()

        with open("output.txt", "w", encoding="utf8") as f:
            for out_word in word_evolution:
                print(out_word)
                f.write("%s\n" % out_word)
        f.close()


class SoundChange(object):
    def __init__(self, i_s: List[TemplatePhone], o_s: List[TemplatePhone], envs: List[List[RichPhone]], sounds: Phones):
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
        """returns the formula defining the attributes of a valid input"""
        return self._inp_form

    def get_out(self):
        """returns the formula defining the attributes of an output"""
        return self._outp_form

    def get_prec_from(self):
        """returns the formula defining the attributes of a valid preceding environment"""
        return self._prec_form

    def get_fol_form(self):
        """returns the formula defining the attributes of a valid following environoment"""
        return self._fol_form

    def __get_in_len(self):

        if len(self.get_in_form()) == 1 and NULL_TEMP_PHONE.matches(self.get_in_form()[0]):  # if input is null
            return 0
        else:
            return len(self._inp_form)

    def __get_prec_len(self):
        return len(self._prec_form)

    def __get_fol_len(self):
        return len(self._fol_form)

    def process(self, word: str):
        """scans a word for sequences constituting valid inputs and makes changes to such sequences as specified by the
        output form"""

        sound = self.sounds.to_sound
        prec_len = self.__get_prec_len()
        in_len = self.__get_in_len()
        fol_len = self.__get_fol_len()

        def get_new_sound(old_sound: RichPhone, output_form: TemplatePhone):
            # generates a sound based upon the sound being changed and the output formula
            new_code = ['{']
            for index in range(len(output_form.code)):
                if output_form.code[index] == '0':  # if no specific attribute is stipulated
                    new_code.append(old_sound.code[index])
                else:
                    new_code.append(output_form.code[index])
            new_code.append('}')
            new_code = ''.join(new_code)
            new_modifiers = old_sound.modifiers.union(output_form.modifiers_to_add).difference(
                output_form.modifiers_to_remove)
            return RichPhone(sound(new_code).symbol, new_code[1:len(new_code) - 1], new_modifiers, old_sound.stress)

        def seq_start(input_start_index):  # returns the index of the first sound of the preceding environment
            return input_start_index - prec_len

        def seq_end(input_start_index):  # returns the index of the last sound of the following environment
            return input_start_index + in_len + fol_len

        def get_input_sequence(
                input_start_index):  # returns the subsequence of the sequence to be examined corresponding to the input
            return [NULL] if in_len == 0 else word[input_start_index:input_start_index + in_len]

        def get_prec_env_sequence(
                input_start_index):  # returns the subsequence of the sequence to be examined corresponding to the preceding environment
            return word[seq_start(input_start_index):input_start_index]

        def get_fol_env_sequence(
                input_start_index):  # returns the subsequence of the sequence to be examined corresponding to the following environment
            return word[input_start_index + in_len:seq_end(input_start_index)]

        def get_output_sequence(
                i):  # generates an output sequence based upon the given input sequence (derived from the starting index
            # of that sequence)
            output_seq = []
            input_sequence = get_input_sequence(i)
            for index in range(len(self.get_in_form())):
                if self.get_out()[index] != NULL_TEMP_PHONE:
                    output_seq.append(get_new_sound(input_sequence[index], self.get_out()[index]))

            return output_seq

        def of_form(actual_sounds: List[Phone], form_sounds: List[Phone]):
            # returns whether each sound in the list matches the corresponding formula
            if len(actual_sounds) != len(form_sounds):
                return False
            else:
                for index in range(len(actual_sounds)):
                    if not (form_sounds[index] == ANY_SOUND or actual_sounds[index].matches(form_sounds[index])):
                        return False
            return True

        def applies_to(p_s: List[RichPhone], i_s: List[RichPhone], f_s: List[RichPhone]) -> bool:
            # returns whether the preceding environment, input, and following environment
            # fulfill all the requirements of the sound change
            return of_form(p_s, self._prec_form) and of_form(i_s, self._inp_form) and of_form(f_s, self._fol_form)

        def in_range(input_start_index):
            # returns whether there are enough sounds preceding and following the beginning of the potential input sequence
            # for it to be possible that all of the requirements of the sound change are fulfilled
            return seq_end(input_start_index) <= len(word) and seq_start(input_start_index) > -1

        def main():  # calls all of the functions to determine what the output (if applicable) will be
            i = 1  # position of the index of beginning of the sequence of sounds to potentially be changed
            output = [WORD_BOUNDARY]
            while len(word) > i:
                if in_range(i) and applies_to(get_prec_env_sequence(i), get_input_sequence(i), get_fol_env_sequence(i)):
                    out_seq = get_output_sequence(i)
                    output.extend(out_seq)
                    if in_len == 0:  # if the input is null, ensure that the character at the index is preserved
                        # in the output word
                        output.append(word[i])
                    i += max(in_len, 1)
                else:
                    output.append(word[i])
                    i += 1

            return output

        return main()

    def __str__(self):
        return to_symbols(self._inp_form) + ' -> ' + to_symbols(self._outp_form) + ' / ' + to_symbols(
            self._prec_form) + '_' + to_symbols(self._fol_form)


if __name__ == '__main__':
    inventory = Inventory()
    inventory.load_features("distinctive features.csv")
    inventory.load_active_sounds("active sounds")
    series = SoundChangeSeries('distinctive features.csv', 'changes',inventory)
    series.apply_sound_changes('corpus')
