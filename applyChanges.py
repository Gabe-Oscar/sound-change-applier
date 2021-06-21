from typing import Tuple, List, Set

from Inventory import Inventory
import pynini
import pynini.lib.rewrite as rewrite


class SoundChangeSeries(object):
    def __init__(self, changes_path, inventory):
        self.inventory = inventory

        self.formula = self.load_sound_changes(changes_path)

    def load_sound_changes(self, file_path):
        """loads sound changes from file"""

        def process_feature_stuff(text):
            text = text.replace(" ", "")
            text = text.replace("][", "|")[1:len(text) - 1]
            final_text = [feature_bundle.split(",") for feature_bundle in text.split("|")]
            return final_text

        def process_target(target_text):
            if target_text == "NULL":
                target_text = "[*]"
            target_strings = process_feature_stuff(target_text)
            targets = [self.inventory.select_active_sounds(target_string) for target_string in target_strings]
            return targets

        def gen_in_to_out(input_sets, output_text):
            output_strings = process_feature_stuff(output_text)
            output_dict = dict()
            for input_sounds, output_string in zip(input_sets, output_strings):
                for input_sound in input_sounds:
                    output_dict[input_sound] = self.inventory.get_variant(input_sound, output_string)
            return output_dict.items()

        def process_envs(env_text):
            env_texts = env_text.split('_')
            for i in range(len(env_texts)):
                if env_texts[i] == "":
                    env_texts[i] = "[*]"
                elif env_texts[i] == "#":
                    env_texts[i] = "[#]"

            processed_envs = [process_feature_stuff(env) for env in env_texts]
            return [[self.inventory.generate_env(env_string) for env_string in env] for env in processed_envs]

        def generate_formula(in_to_out: List[Tuple[str]], envs: Tuple[Set[str]]):
            sigma_star = pynini.closure(pynini.union(*self.inventory.active_sounds.union("#"))).optimize()
            string_map = pynini.string_map(in_to_out).closure().optimize()
            env_formulas = []
            for env in envs:
                env_formula = pynini.union(*env[0])
                for i in range(1, len(env)):
                    env_formula = env_formula + pynini.union(*env[i])
                env_formulas.append(env_formula)
            return pynini.cdrewrite(string_map, env_formulas[0], env_formulas[1], sigma_star).optimize()

        def combine_formulas(formulas: list):
            combined_formula = formulas[0]
            for formula in formulas[1:]:
                combined_formula = pynini.compose(combined_formula, formula).optimize()

            return combined_formula

        def main():
            formulas = list()
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

                    # create a dictionary mapping inputs to outputs
                    in_to_out = gen_in_to_out(process_target(variables[0]), variables[1])

                    # generate formula reflecting sound change and add it to list of formulas
                    formulas.append(generate_formula(in_to_out, envs))

                sound_change_file.close()
                return combine_formulas(formulas)
        return main()

    def apply_sound_changes(self, corpus_file_path):
        """applies loaded sound changes to a corpus"""

        out_words = []
        with open(corpus_file_path, "r", encoding="utf8") as corpus:
            for word in ["#" + raw_word.strip() + "#" for raw_word in corpus]:
                out_word = rewrite.one_top_rewrite(word, self.formula)
                print(out_word)
                out_words.append(out_word)
        corpus.close()

    #    with open("output.txt", "w", encoding="utf8") as f:
   #         for out_word in out_words:
    #            print(out_word)
  #              f.write("%s\n" % out_word)
   #     f.close()


if __name__ == '__main__':
    inventory = Inventory()
    inventory.load_features("distinctive features.csv")
    inventory.load_active_sounds("active sounds")
    inventory.generate_distinctive_features()
    series = SoundChangeSeries('changes', inventory)
    series.apply_sound_changes('corpus')
