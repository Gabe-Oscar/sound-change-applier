from collections import defaultdict
import csv
from typing import DefaultDict, Dict, List, Set
from queue import Queue
from pynini import *

POS = 1
NEUT = 0
NEG = -1
POS_SIGN = "+"
NEG_SIGN = "-"

BOUND = "#"
NULL = "0"
ALL = "*"
NON_PHONEMES = {NULL, BOUND}


class Inventory(object):
    def __init__(self):
        self.sym_to_feats: DefaultDict[str, set] = defaultdict(set, {NULL: {}})  # symbol of sound to features of sound
        self.feat_to_syms: DefaultDict[str, set] = defaultdict(set)  # feature to symbols of sounds with the feature
        self.feature_names: set[str] = set()  # features
        self.syms: set[str] = set()  # symbols
        self.active_sounds: set[str] = set()  # sounds currently being used

    def load_features(self, features_file_path):
        def read_value(value: str) -> int:
            if value == '0':
                return NEG
            elif value == '1':
                return POS
            else:
                return NEUT

        with open(features_file_path, encoding="utf-8") as features:
            feat_names_ordered_list = features.readline().strip().split(',')[
                                      1:]
            self.feature_names = set(feat_names_ordered_list)  # feats = list of features from first line of file
            for f_l in csv.reader(features):
                sym = f_l[0]
                feature_values = [read_value(feature_number) for feature_number in f_l[
                                                                                   1:]]  # the values of each feature for the given sound (i.e. whether the sound has that feature)
                if sym[0] != '_':  # if the symbol isn't a modifier
                    feats = set()
                    self.syms.add(sym)
                    for feature_name, feature_value in zip(feat_names_ordered_list, feature_values):
                        feature = (POS_SIGN if feature_value == POS else NEG_SIGN) + feature_name
                        feats.add(feature)
                        self.feat_to_syms[feature].add(sym)
                    self.sym_to_feats[sym] = feats
                else:  # create versions of each sound with this modification
                    for each_sym in self.syms.copy():
                        sym_variant = each_sym + sym[1:]
                        self.syms.add(sym_variant)
                        feats = self.sym_to_feats[each_sym].copy()

                        for feature_name, feature_value in zip(feat_names_ordered_list, feature_values):
                            if feature_value != NEUT:  # if this is one of the features that this modifier modifies, change the value of the variant's feature accordingly
                                feature = (POS_SIGN if feature_value == POS else NEG_SIGN) + feature_name
                                feats.add((POS_SIGN if feature_value == POS else NEG_SIGN) + feature_name)
                                feats.discard(POS_SIGN if feature_value != POS else NEG_SIGN + feature_name)
                                self.feat_to_syms[feature].add(sym_variant)
                            self.sym_to_feats[sym_variant] = feats

    def has_feature(self, symbol, feature):
        return feature in self.sym_to_feats[symbol][feature]

    def load_active_sounds(self, sounds_file_path):
        with open(sounds_file_path) as sounds_file:
            for sound in sounds_file:
                self.active_sounds.add(sound.strip())

    def generate_env(self, environment):
        if environment == [""]:
            return ""
        elif environment == [BOUND]:
            return BOUND
        else:
            return self.select_active_sounds(environment)

    def select_active_sounds_with_feature(self, feature: str):
        return self.select_active_sounds([feature])

    def select_active_sounds(self, feature_list: set[str]):
        if feature_list == [ALL]:
            return self.active_sounds
        elif feature_list == [NULL]:
            return [""]
        sound_pool: set = self.active_sounds.copy()

        for feature in feature_list:
            sound_pool = sound_pool.intersection(self.feat_to_syms[feature])
        return sound_pool

    def add_active_sound(self, new_sound):
        if new_sound in self.syms:
            self.active_sounds.add(new_sound)

        else:
            raise ValueError("Symbol not recognized")

    def get_variant(self, in_sound, changes):
        if changes[0] == NULL:
            return ''

        sound_pool = self.select_active_sounds(set(changes))
        best_choice = sound_pool.pop()
        best_intersection_size = len(
            set.intersection(self.sym_to_feats[in_sound], self.sym_to_feats[best_choice]))
        while sound_pool:
            pot_choice = sound_pool.pop()
            intersection_size = len(
                set.intersection(self.sym_to_feats[in_sound], self.sym_to_feats[pot_choice]))
            if intersection_size > best_intersection_size:
                best_intersection_size = intersection_size
                best_choice = pot_choice
        return best_choice

