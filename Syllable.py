import Sounds

STRESSED_SYLLABLE_BREAK = '\''
UNSTRESSED_SYLLABLE_BREAK = '.'
SECONDARY_STRESSED_SYLLABLE_BREAK = 'ˌ'
SYLLABLE_BREAKS = set([STRESSED_SYLLABLE_BREAK, UNSTRESSED_SYLLABLE_BREAK, SECONDARY_STRESSED_SYLLABLE_BREAK])

class Shell(object):
    def __init__(self, phones: Sounds.RichPhone):
        self._phones = phones
        self._symbol = ''.join(Sounds.to_symbols(phones))

    def size(self):
        return len(self.phones)

    def get_phones(self):
        return self._phones

    def get_symbol(self):
        return self._symbol

    def __str__(self):
        return self.get_symbol()


class Nucleus(object):
    def __init__(self, phone: Sounds.RichPhone):
        self._phone = phone
        self._symbol = phone.get_symbol()

    def get_phone(self):
        return self._phone

    def get_symbol(self):
        return self._symbol

    def __str__(self):
        return self.get_symbol()


class Syllable(object):

    def __init__(self, stress_status: str, onset: Shell, nucleus: Nucleus, coda: Shell, prev_syllable=None,
                 next_syllable=None):
        def set_distance_from_front() -> int:
            if not isinstance(prev_syllable, Syllable):
                return 0
            else:
                return prev_syllable.distance_from_front + 1

        self._onset = onset
        self._nucleus = nucleus
        self._coda = coda
        self.stress_status = stress_status
        self._prev_syllable = prev_syllable
        self._next_syllable = next_syllable
        self.symbol = ''.join([stress_status, onset.get_symbol(), nucleus.get_symbol(), coda.get_symbol()])
        self.distance_from_front = set_distance_from_front()
        self.distance_from_back = 0

        for sound in onset.get_phones():
            sound.set_syllable(self)
        for sound in nucleus.get_phones():
            sound.set_syllable(self)
        for sound in coda.get_phones():
            sound.set_syllable(self)

    def get_onset(self):
        return self._onset

    def get_coda(self):
        return self._coda

    def get_nucleus(self):
        return self._nucleus

    def get_stressed_status(self):
        return self.stress_status

    def is_stressed(self):
        return self.stress_status == STRESSED_SYLLABLE_BREAK

    def is_unstressed(self):
        return self.stress_status == UNSTRESSED_SYLLABLE_BREAK

    def is_secondarily_stressed(self):
        return self.stress_status == SECONDARY_STRESSED_SYLLABLE_BREAK

    def distance_from_front(self):
        return self.distance_from_front

    def distance_from_back(self):
        return self.distance_from_back

    def get_previous_syllable(self):
        return self._prev_syllable

    def get_next_syllable(self):
        return self._next_syllable

    def set_next_syllable(self, syllable):
        if syllable.get_previous_syllable() == self:
            self._next_syllable = syllable

    def __str__(self):
        return self.symbol

    def update_distance_from_back(self):
        if self._next_syllable is None:
            if self._prev_syllable is not None:
                self._prev_syllable.set_next_syllable(self)
                self._prev_syllable.update_distance_from_back()
        else:
            self.distance_from_back = self._next_syllable.distance_from_back + 1
            if self._prev_syllable is not None:
                self._prev_syllable.set_next_syllable(self)
                self._prev_syllable.update_distance_from_back()

