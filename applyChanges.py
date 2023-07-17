from typing import Tuple, List, Set
import re
from Inventory import Inventory
from Inventory import NULL
import pynini
import pynini.lib.rewrite as rewrite
import cProfile

BOUND = "#"

class SoundChangeSeries(object):
    def __init__(self, changes_path, inventory):
        self.inventory = inventory
        self.insertion_count = 0
        pynini.default_token_type("utf-8")

        self.sigma_star = pynini.closure(pynini.union(*self.inventory.syms.union(BOUND)).optimize()).optimize()

        self.formula = self.load_sound_changes(changes_path)

    def load_sound_changes(self, file_path):
        """loads sound changes from file"""

        def process_feature_stuff(text):
            text = re.sub("\s", "", text)
            text = re.sub("]\[", "|", text)
            text = re.sub("[\[\]]", "", text)
            final_text = [feature_bundle.split(",") for feature_bundle in text.split("|")]
            return final_text

        def process_target(target_text):
            if NULL in target_text:
                self.insertion_count += 1
            target_strings = process_feature_stuff(target_text)
            targets = [self.inventory.select_active_sounds(target_string) for target_string in target_strings]
            return targets

        def gen_in_to_out(input_sets, output_text):
            output_strings = process_feature_stuff(output_text)
            output_dicts = [{} for sub in range(len(input_sets))]
            for i in range(len(input_sets)):
                for input_sound in input_sets[i]:
                    output = self.inventory.get_variant(input_sound, output_strings[i])
                    if i >= 1:
                        for prev_input_sound in output_dicts[i - 1]:
                            output_dicts[i][prev_input_sound + input_sound] = output_dicts[i - 1][
                                                                                  prev_input_sound] + output
                    else:
                        output_dicts[i][input_sound] = output

            return list(output_dicts[len(output_dicts) - 1].items())

        def process_envs(env_text):
            env_texts = env_text.split('_')
            for i in range(len(env_texts)):
                if env_texts[i] == "":
                    env_texts[i] = "[]"
                elif env_texts[i] == BOUND:
                    env_texts[i] = "[" + BOUND + "]"
            processed_envs = [process_feature_stuff(env) for env in env_texts]
            return [[self.inventory.generate_env(env_string) for env_string in env] for env in processed_envs]

        def generate_formula(in_to_out: List[Tuple[str]], envs: Tuple[Set[str]]):
            env_formulas = list()
            for i in range(len(envs)):
                if envs[i] != [""] and (len(envs[i]) > 1 or in_to_out[0][0] != '' or i > 0):
                    env_formula = pynini.union(*envs[i][0]).optimize()
                    for j in range(1, len(envs[i]) - int(in_to_out[0][0] == '' and i == 0)):
                        env_formula = (env_formula + pynini.union(*envs[i][j])).optimize()
                else:
                    env_formula = pynini.accep("")
                env_formulas.append(pynini.rmepsilon(env_formula.optimize()))

            if in_to_out[0][0] == '':
                str_map: pynini.Fst = pynini.string_map(
                    (e_v, e_v + in_to_out[0][1]) for e_v in envs[0][len(envs[0]) - 1])
                return pynini.cdrewrite(str_map.ques, env_formulas[0], env_formulas[1], self.sigma_star,
                                        direction="ltr").optimize()
            else:
                str_map: pynini.Fst = pynini.string_map(in_to_out).ques.rmepsilon().optimize()

            return pynini.cdrewrite(str_map.ques, env_formulas[0], env_formulas[1], self.sigma_star,
                                    direction="ltr").optimize()

        def combine_formulas(formulas: list):
            combined_formula = formulas[0]
            for formula in formulas[1:]:
                combined_formula = pynini.compose(combined_formula, formula).optimize()
            return combined_formula

        def main():
            formulas = list()

            with open(file_path, "r", encoding="utf-8") as sound_change_file:
                for sound_change in sound_change_file:
                    # if the "sound change" consists of adding new potential phonemes to the language
                    if sound_change[:3] == "add":
                        new_sounds = sound_change.strip().split(" ")[1].split(",")
                        for sound in new_sounds:
                            self.inventory.add_active_sound(sound)
                    else:
                        variables = sound_change.strip().split('/')
                        # create a tuple whose first element consists of the sound sequence composing the preceding environment
                        # and whose second element consists of the sound sequence composing the following following environment
                        envs = tuple(process_envs(variables[2]))

                        # create a dictionary mapping inputs to outputs
                        in_to_out = gen_in_to_out(process_target(variables[0]), variables[1])

                        # generate formula reflecting sound change and add it to list of formulas
                        formulas.append(generate_formula(in_to_out, envs))

                sound_change_file.close()
                return combine_formulas(formulas)

        return main()

    def apply_sound_changes(self, corpus_file_path):
        """applies loaded sound changes to a corpus"""

        def process_word(word):
            processed_word = word.strip()
            processed_word = BOUND + processed_word + BOUND
            return processed_word

        with open(corpus_file_path, "r", encoding="utf-8") as corpus:
            for word in corpus:
                word = process_word(word)
                word = rewrite.one_top_rewrite(word, self.formula)
                print(word.replace(BOUND,""))
        corpus.close()



if __name__ == '__main__':
    profiler = cProfile.Profile()
    profiler.enable()

    inventory = Inventory()
    inventory.load_features("distinctive features.csv")
    inventory.load_active_sounds("active sounds")
    inventory.generate_distinctive_features()
    series = SoundChangeSeries('changes', inventory)
    series.apply_sound_changes('corpus')

    profiler.disable()
    profiler.print_stats(sort='time')
