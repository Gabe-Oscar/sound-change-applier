from collections import defaultdict
import csv

POS = 1
NEG = 2
N_A = 0


class Inventory(object):

    def __init__(self):
        self.sym_to_feat = dict()
        self.feat_to_sym = defaultdict(list)
        self.neg_feat_to_sym = defaultdict(list)
        self.feats = set()
        self.syms = set()
        self.active_sounds = set()

    def load_features(self, features_file_path):
        with open(features_file_path) as features:
            self.feats = features.readline().strip().split('\t')
            for f_l in csv.reader(features,delimiter='\t'):
                feat_to_val = dict()
                sym = f_l[0]
                self.syms.add(sym)
                for i in range(1, len(f_l)):
                    feat_to_val[self.feats[i - 1]] = int(f_l[i])
                    if feat_to_val[self.feats[i - 1]] == POS:
                        self.feat_to_sym[self.feats[i - 1]].append(sym)
                self.sym_to_feat[sym] = feat_to_val

    def has_feature(self, symbol, feature):
        return self.sym_to_feat[symbol][feature] == 1

    def load_active_sounds(self, sounds_file_path):
        with open(sounds_file_path) as sounds_file:
            for sound in sounds_file:
                self.active_sounds.add(sound.strip())

    def select_active_sounds(self, feature_list):
        if feature_list == ["*"]:
            return self.active_sounds
        sound_pool = self.active_sounds.copy()
        for feature in feature_list:
            new_sound_pool = set()
            sign = feature[0] == "+"
            content = feature[1:]
            for sound in sound_pool:
                if self.sym_to_feat[sound][content] == sign:
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
            return sound_pool[0]

    def add_active_sound(self, new_sound):
        if new_sound in self.syms:
            self.active_sounds.append(new_sound)

        else:
            raise ValueError("Symbol not recognized")

    def get_variant(self, in_sound, changes):
        out_sound_features = self.sym_to_feat(in_sound)
        for change in changes:
            sign = change[0] == "+"
            content = change[1:]
            out_sound_features[content] = sign
        return self.feat_to_sym[out_sound_features]
