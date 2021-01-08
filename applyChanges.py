from collections import defaultdict
import SC
from typing import List, DefaultDict, Tuple
from anytree import Node, RenderTree


class SoundChangeSeries(object):

    def __init__(self, attributes_path, changes_path, categories_path):
        self.sound_changes: List[SC] = list()
        self.cat_to_symbols = {}
        self.symbol_to_cats: DefaultDict[str, List[str]] = defaultdict(list)
        self.symbol_to_atts: DefaultDict[str, DefaultDict[str, str]] = defaultdict(lambda: defaultdict())
        self.atts_to_symbol: DefaultDict = {}

        self.load_attributes(attributes_path)
        self.load_categories(categories_path)
        self.load_sound_changes(changes_path)

    def load_attributes(self, file_path):
        def get_matching_child(node: Node, attribute: str):
            for child in node.children:
                if child.name == attribute:
                    return child
            return None

        with open(file_path, "r", encoding="utf8") as attributes_file:
            titles: List[str] = attributes_file.__next__().strip().split(',')
            for line in attributes_file:
                attributes = line.strip().split(',')
                symbol = line[0]

                for index in range(1, len(attributes)):
                    self.symbol_to_atts[symbol][titles[index]] = attributes[index]

        attributes_file.close()

    def get_symbols_of_att(self, attributes: List[Tuple[str, str]]) -> List[str]:
        dict_pointer = self.atts_to_symbol

        def fits_criteria(symbol: str, attributes_to_check):
            for attr in attributes_to_check:
                if self.symbol_to_atts[symbol][attr[0]] != attr[1]:
                    return False
            return True
        attributes_to_check = []
        symbols_to_check =  self.symbol_to_atts.keys()
        for attribute in attributes:
            attributes_to_check.append(attribute)
            if not dict_pointer.keys().__contains__(attribute[1]):
                dict_pointer[attribute[1]] = dict()
                dict_pointer = dict_pointer[attribute[1]]
                match_list = []
                for potential_match in symbols_to_check:
                    if fits_criteria(potential_match, attributes_to_check):
                        match_list.append(potential_match)
                dict_pointer['*'] = match_list
            else:
                dict_pointer = dict_pointer[attribute[1]]
            symbols_to_check = dict_pointer['*']


        return  dict_pointer['*']

    def load_categories(self, file_path):

        with open(file_path, "r", encoding="utf8") as categories_file:
            for line in categories_file:
                split_line = line.strip().split(',')
                if len(split_line[0]) != 1:
                    raise Exception(
                        (split_line[0] + ' is an invalid category. Categories must be exactly one character.'))
                else:
                    self.cat_to_symbols[split_line[0]] = split_line[1:]
                    for sound in split_line[1:]:
                        self.symbol_to_cats[sound].append(split_line[0])
        categories_file.close()

    def load_sound_changes(self, file_path):
        with open(file_path, "r", encoding="utf8") as sound_change_file:
            for sound_change in sound_change_file:
                variables = sound_change.strip().split(',')
                self.sound_changes.append(SC.SoundChange(variables[0], variables[1], variables[2], self))
        sound_change_file.close()

    def in_category(self, sound, category):
        return self.symbol_to_cats[sound].__contains__(category)

    def get_sounds_of_category(self, category):
        if self.cat_to_symbols.keys().__contains__(category):
            return self.cat_to_symbols[category]
        else:
            return [category]

    def apply_sound_changes(self, corpus_file_path):
        output_words: List[str] = []
        with open(corpus_file_path, "r", encoding="utf8") as corpus:
            for word in corpus:
                stages: str = word.strip()
                out_word: str = "#" + word.strip() + "#"
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

    def get_categories(self):
        return self.cat_to_symbols.keys()

    def get_symbols(self):
        return self.symbol_to_cats.keys()


if __name__ == '__main__':
    series = SoundChangeSeries('attributes', 'changes', 'categories')
    series.apply_sound_changes('corpus')
