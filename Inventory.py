from collections import defaultdict, Set
import csv
from typing import DefaultDict, Dict, List
from queue import Queue
from pynini import *

POS = 1
NEG = 0
POS_SIGN = "+"
NEG_SIGN = "-"
DEP_SIGN = "?"
WORD_BOUNDARY = "#"
NULL = "0"
ALL = "*"
NON_PHONEMES = {NULL, WORD_BOUNDARY}
PLACE = {"LABIAL", "round", "labiodental", "CORONAL", "anterior", "distributed", "strident", "lateral", "DORSAL",
         "high", "low", "front", "back"}
GEN_PLACE = {"LABIAL", "CORONAL", "DORSAL"}


class Inventory(object):
    # TODO: Add mechanism to prune non-distinctive features
    def __init__(self):
        self.sym_to_feats: DefaultDict[str, dict] = defaultdict(dict, {'0': {}})
        self.feat_to_syms: DefaultDict[str, set] = defaultdict(set)
        self.neg_feat_to_sym: DefaultDict[str, set] = defaultdict(set)
        self.feats: Set[str] = set()
        self.syms: Set[str] = set()
        self.active_sounds: Set[str] = set()
        self.distinctive_features: Set[str] = set()
        self.sym_to_dist_feats: DefaultDict[str, dict] = defaultdict(dict)

    def load_features(self, features_file_path):
        with open(features_file_path, encoding="utf-8") as features:
            self.feats = features.readline().strip().split(',')[1:]
            for f_l in csv.reader(features):
                sym = f_l[0]
                vals = f_l[1:]
                if sym[0] != '_':
                    feat_to_val = dict()

                    self.syms.add(sym)
                    for i in range(0, len(vals)):
                        feat_to_val[self.feats[i]] = bool(int(vals[i]))
                        if feat_to_val[self.feats[i]] == POS:
                            self.feat_to_syms[self.feats[i]].add(sym)
                        else:
                            self.neg_feat_to_sym[self.feats[i]].add(sym)
                    self.sym_to_feats[sym] = feat_to_val
                else:
                    for each_sym in self.syms.copy():
                        feat_to_val = dict()
                        sym_variant = each_sym + sym[1:]
                        self.syms.add(sym_variant)
                        for i in range(0, len(vals)):
                            if vals[i] != '_':
                                feat_to_val[self.feats[i]] = bool(int(vals[i]))
                            else:
                                feat_to_val[self.feats[i]] = self.sym_to_feats[each_sym][self.feats[i]]
                            if feat_to_val[self.feats[i]] == POS:
                                self.feat_to_syms[self.feats[i]].add(sym_variant)
                            else:
                                self.neg_feat_to_sym[self.feats[i]].add(sym_variant)
                        self.sym_to_feats[sym_variant] = feat_to_val
    def has_feature(self, symbol, feature):
        return self.sym_to_feats[symbol][feature] == 1

    def load_active_sounds(self, sounds_file_path):
        with open(sounds_file_path) as sounds_file:
            for sound in sounds_file:
                self.active_sounds.add(sound.strip())

    def generate_distinctive_features(self):
        # gets rid of features that have the same value for every active sound
        def remove_static_features():
            for feature in self.distinctive_features.copy():
                value_set = set([self.sym_to_feats[sound][feature] for sound in self.active_sounds])
                if len(value_set) <= 1:
                    self.distinctive_features.remove(feature)

        # removes feature A if:
        #   - there is a feature B with which feature A always occurs
        #   - feature B does not always occur with feature A
        #   -

        if len(self.active_sounds) == 0:
            raise ValueError("Must load active sounds before running this method")
        else:
            self.distinctive_features = self.feats.copy()
            remove_static_features()
            for active_sound in self.active_sounds:
                for distinctive_feature in self.distinctive_features:
                    if distinctive_feature in self.sym_to_feats[active_sound].keys():
                        self.sym_to_dist_feats[active_sound][distinctive_feature] = self.sym_to_feats[active_sound][
                            distinctive_feature]

    def get_place(self, symbol):
        return {feature: self.sym_to_feats[symbol][feature] for feature in PLACE}

    def get_gen_place(self, symbol):
        return {feature: self.sym_to_feats[symbol][feature] for feature in GEN_PLACE}

    def generate_env(self, environment):
        if environment == [""]:
            return ""
        elif environment == ["#"]:
            return "#"
        else:
            return self.select_active_sounds(environment)

    def select_active_sounds_with_feature(self, feature: str):
        return self.select_active_sounds([feature])

    def select_active_sounds(self, feature_list: List[str]):
        if feature_list == [ALL]:
            return self.active_sounds
        elif feature_list == [NULL]:
            return [""]
        sound_pool: set = self.active_sounds.copy()

        for feature in feature_list:
            if len(feature.split("@")) == 1:
                if isinstance(feature_list, list):

                    if feature[0] == POS_SIGN:
                        sign = True
                    elif feature[0] == NEG_SIGN:
                        sign = False
                    else:
                        raise ValueError("Value of " + feature + "not indicated")

                    feature = feature[1:]
                else:
                    sign = feature_list[feature]
                if sign:
                    sound_pool = sound_pool.intersection(self.feat_to_syms[feature])
                else:
                    sound_pool = sound_pool.intersection(self.neg_feat_to_sym[feature])

        #       for sound in sound_pool:
        #         if self.sym_to_feats[sound][content] == sign:
        #              new_sound_pool.add(sound)
        #     sound_pool = new_sound_pool
        return sound_pool

    def add_active_sound(self, new_sound):
        if new_sound in self.syms:
            self.active_sounds.add(new_sound)
            self.distinctive_features = self.feats
            self.generate_distinctive_features()

        else:
            raise ValueError("Symbol not recognized")

    def get_variant(self, in_sound, changes):
        if changes[0] == NULL:
            return ''
        out_sound_features = self.sym_to_dist_feats[in_sound].copy()
        contents = set()
        eigenschaften = dict()

        for feat_change in changes:
            sign = feat_change[0] == "+"
            content = feat_change[1:]
            contents.add(content)
            out_sound_features[content] = sign
            eigenschaften[content] = sign

        sound_pool = self.select_active_sounds(out_sound_features)
        if len(sound_pool) > 1:
            raise ValueError("Criteria applies to multiple active sounds")
        elif len(sound_pool) == 0:
            pot_variants = self.select_active_sounds(eigenschaften)
            out_sound_features_set = set(out_sound_features.items())
            pvfs = set(self.sym_to_feats[pot_variants.pop()].items())
            for pot_variant in pot_variants:
                pvfs = pvfs.intersection(set(self.sym_to_feats[pot_variant].items()))
            donbother = set(featurepaire[0] for featurepaire in out_sound_features_set.intersection(pvfs))
            mutable_list = list(set(self.distinctive_features).difference(contents).difference(donbother))

            cdb = list(contents.union(donbother))
            attempt = mutable_list.copy()
            to_try = Queue()
            to_try.put(attempt)
            popped = ''
            while len(sound_pool) != 1 and not to_try.empty():
                curr_try = to_try.get()
                curr_features = {key: out_sound_features[key] for key in (curr_try + cdb)}
                for j in range(len(curr_try)):
                    new_features = curr_features.copy()
                    new_features.pop(curr_try[j])
                    new_try = curr_try[0:j] + curr_try[j + 1:]
                    sound_pool = self.select_active_sounds(new_features)
                    if len(sound_pool) == 0:
                        to_try.put(new_try)
                    elif len(sound_pool) == 1:
                        break

        if len(sound_pool) == 1:
            return sound_pool.pop()
        else:
            raise ValueError("Criteria doesn't apply to any active sounds; "
                             "add new active sounds before applying this rule")

    def feature_dict_to_string(self, feature_dict: dict):
        string_list = []
        for feature in feature_dict.keys():
            if feature[feature]:
                string_list.append("+" + feature)
            else:
                string_list.append("-" + feature)
        return str(string_list)