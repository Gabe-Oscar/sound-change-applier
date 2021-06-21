from collections import defaultdict, Set
import csv
from typing import DefaultDict, Dict

POS = 1
NEG = 2
N_A = 0
WORD_BOUNDARY = "#"


class Inventory(object):
    # TODO: Add mechanism to prune non-distinctive features
    def __init__(self):
        self.sym_to_feats: dict = dict()
        self.feat_to_syms: defaultdict = defaultdict(list)
        self.neg_feat_to_sym: defaultdict = defaultdict(list)
        self.feats: set = set()
        self.syms: set = set()

        self.active_sounds: set = set()
        self.distinctive_features: set = set()

    def load_features(self, features_file_path):
        with open(features_file_path) as features:
            self.feats = features.readline().strip().split(',')[1:]
            for f_l in csv.reader(features):
                feat_to_val = dict()
                sym = f_l[0]
                self.syms.add(sym)
                for i in range(0, len(f_l) - 1):
                    feat_to_val[self.feats[i]] = bool(int(f_l[i + 1]))
                    if feat_to_val[self.feats[i]] == POS:
                        self.feat_to_syms[self.feats[i]].append(sym)
                    else:
                        self.neg_feat_to_sym[self.feats[i]].append(sym)
                self.sym_to_feats[sym] = feat_to_val

    def has_feature(self, symbol, feature):
        return self.sym_to_feats[symbol][feature] == 1

    def load_active_sounds(self, sounds_file_path):
        with open(sounds_file_path) as sounds_file:
            for sound in sounds_file:
                self.active_sounds.add(sound.strip())

    def generate_distinctive_features(self):
        # gets rid of features that have the same value for every active sound
        def remove_static_features(feature_set):
            output_set = set()
            for feature in feature_set:
                value_set = set([self.sym_to_feats[sound][feature] for sound in self.active_sounds])
                if len(value_set) > 1:
                    output_set.add(feature)
            return output_set

        if len(self.active_sounds) == 0:
            raise ValueError("Must load active sounds before running this method")
        else:
            self.distinctive_features = remove_static_features(self.feats)


    def generate_env(self, environment):
        if environment == ["*"]:
            return self.active_sounds.union(WORD_BOUNDARY)
        elif environment == ["#"]:
            return "#"
        else:
            return self.select_active_sounds(environment)

    def select_active_sounds(self, feature_list):
        if feature_list == ["*"]:
            return self.active_sounds
        sound_pool = self.active_sounds.copy()
        for feature in feature_list:
            new_sound_pool = set()
            if isinstance(feature_list, list):
                sign = feature[0] == "+"
                content = feature[1:]
            else:
                sign = feature_list[feature]
                content = feature
            for sound in sound_pool:
                if self.sym_to_feats[sound][content] == sign:
                    new_sound_pool.add(sound)
            sound_pool = new_sound_pool
        return sound_pool

    def select_active_sound(self, feature_list):
        sound_pool = self.select_active_sounds(feature_list)
        if len(sound_pool) > 1:
            raise ValueError("Criteria applies to multiple active sounds")

        if len(sound_pool) == 0:
            raise ValueError("Criteria doesn't apply to any active sounds; "
                             "add new active sounds before applying this rule")
        else:
            return sound_pool.pop()

    def add_active_sound(self, new_sound):
        if new_sound in self.syms:
            self.active_sounds.append(new_sound)

        else:
            raise ValueError("Symbol not recognized")

    def get_variant(self, in_sound, changes):
        out_sound_features = self.sym_to_feats[in_sound].copy()
        for feat_change in changes:
            sign = feat_change[0] == "+"
            content = feat_change[1:]
            out_sound_features[content] = sign

        return self.select_active_sound(out_sound_features)
