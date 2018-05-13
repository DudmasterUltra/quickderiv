import math, random

OPERATORS = {
  
  '+': lambda x, y: x + y,
  '-': lambda x, y: x - y,
  '/': lambda x, y: x / y,
  '*': lambda x, y: x * y,
  '^': math.pow
  
}
SPLIT_OPERATORS = (

    OPERATORS['+'],
    OPERATORS['-']

)

def removeall(seq, sub):
    for item in sub:
        if item in seq:
            seq.remove(item)

def count(seq, pred):
    return sum(1 for v in seq if pred(v))

def randombool():
    return bool(random.getrandbits(1))

def tryint(val):
    try:
        return int(val)
    except:
        return val

def splitlist(data, *separators):
    result = [list()]
    for i in data:
        if i in separators:
            result.append(list())
        else:
            result[-1].append(i)
    return result

def joinlist(data, separator):
    result = list()
    for i in data:
        if i:
            result.extend(i)
            result.append(separator)
    if len(result) > 0:
        del result[-1]
    return result

class Expression:
    def __init__(self, parse=None, data=None):
        if data is None:
            data = list()
        self.data = data
        if parse is not None:
            buf = str()
            invert = False
            if len(parse) > 0 and parse[0] == '-':
                parse = parse[1:]
                invert = True
            for c in parse:
                if c in OPERATORS:
                    cop = OPERATORS[c]
                    self._append(buf)
                    invert = cop == OPERATORS['-']
                    self.data.append(cop)
                    buf = str()
                elif not c.isspace():
                    if c.isalpha():
                        self._append(buf, invert)
                        if len(self.data) > 0 and self.data[-1] not in OPERATORS.values():
                            self.data.append(OPERATORS['*'])
                        self.data.append(c)
                        buf = str()
                    else:
                        buf += c
            self._append(buf)

    def collect_terms(self):
        self.data = self._like_terms(self.data)
        self.data = self._remove_zeroes(self.data)

    def _append(self, buf, invert=False):
        if buf:
            i = tryint(buf.strip())
            if invert and (isinstance(i, int) or isinstance(i, float)):
                i *= -1
            self.data.append(i)

    def tokenize_terms(self, exp=None):
        return splitlist(self.data if exp is None else exp, *SPLIT_OPERATORS)

    @staticmethod
    def _evaluate(exp, *test):
        i = 0
        while i < len(exp):
            if i != 0 and exp[i] in test:
                one = exp[i - 1]
                two = exp[i + 1]
                if not isinstance(one, str) and not isinstance(two, str):
                    exp[i - 1] = exp[i](one, two)
                    del exp[i]
                    del exp[i]
                else:
                    return False
                    i += 1
            else:
                i += 1
        return True

    @classmethod
    def _evaluate_list(cls, exp, **kwargs):
        for i in range(len(exp)):
            if exp[i] in kwargs:
                exp[i] = kwargs[exp[i]]
        cls._evaluate(exp, OPERATORS['^'])
        cls._evaluate(exp, OPERATORS['*'], OPERATORS['/'])
        cls._evaluate(exp, OPERATORS['+'], OPERATORS['-'])

    def evaluate(self, **kwargs):
        exp = self.data[:]
        self._evaluate_list(exp, **kwargs)
        return exp[0] if len(exp) == 1 else exp

    @staticmethod
    def get_order(exp):
        if OPERATORS['^'] in exp:
            return exp[exp.index(OPERATORS['^']) + 1]
        else:
            return len(list(filter(lambda x: isinstance(x, str), exp)))

    @classmethod
    def get_coefficient(cls, exp, duplicate=True):
        if len(exp) == 1:
            return (1, exp[0]) if isinstance(exp[0], str) else exp[0]
        if duplicate:
            exp = exp[:]
        c = 0
        if OPERATORS['*'] in exp:
            mul_index = exp.index(OPERATORS['*'])
            if mul_index + 1 > len(exp) and isinstance(exp[mul_index + 1], int):
                c = exp[mul_index + 1]
                del exp[mul_index]
                del exp[mul_index]
            if mul_index - 1 <= 0 and isinstance(exp[mul_index - 1], int):
                c = exp[mul_index - 1]
                del exp[mul_index - 1]
                del exp[mul_index - 1]
        if c == 0:
            return 0
        recurse = cls.get_coefficient(exp, duplicate=False)
        return (c + recurse if isinstance(recurse, int) else c, exp)

    def _like_terms(self, exp):
        split = self.tokenize_terms(exp)
        if len(split) <= 0:
            return list()
        if len(split) == 1:
            return exp[:]
        result = list()
        i = 0
        while i < len(split):
            item = split[i]
            item_order = self.get_order(item)
            if item_order == 0:
                co = self.get_coefficient(item)
            else:
                co, ex = self.get_coefficient(item)
            matchings = list(filter(lambda x: x is not item and self.get_order(x) == item_order, split))
            for matching in matchings:
                matching_co = self.get_coefficient(matching)
                co += matching_co if isinstance(matching_co, int) else matching_co[0]
            if item_order > 0:
                if co > 1:
                    append = [co, OPERATORS['*']]
                    append.extend(ex)
                    result.append(append)
                else:
                    result.append([ex])
            else:
                result.append([co])
            removeall(split, matchings)
            i += 1
        return joinlist(result, OPERATORS['+'])

    def _remove_zeroes(self, exp):
        return joinlist(filter(lambda x: self.get_coefficient(x) != 0,
                               self.tokenize_terms(exp)), OPERATORS['+'])
        
    def _remove_constants(self, exp):
        return joinlist(filter(lambda x: len(list(filter(lambda y: isinstance(y, str), x))) != 0,
                               self.tokenize_terms(exp)), OPERATORS['+'])
##        split = self.tokenize_terms(exp)
##        if len(split) <= 0:
##            return list()
##        elif len(split) == 1:
##            remove = True
##            for c in split[0]:
##                if isinstance(c, str):
##                    remove = False
##                    break
##            return list() if remove else split[0]
##        else:
##            return joinlist([self._remove_constants(x) for x in split], OPERATORS['+'])

    def _power_rule(self, exp):
        split = self.tokenize_terms(exp)
        if len(split) <= 0:
            return list()
        elif len(split) == 1:
            data = split[0]
            i = 0
            while i < len(data):
                if isinstance(data[i], str):
                    if i + 2 < len(data):
                        if data[i + 1] == OPERATORS['^']:
                            power = data[i + 2]
                            data[i + 2] -= 1
                            if data[i + 2] == 1:
                                del data[i + 2]
                                del data[i + 1]
                            if i - 1 >= 0 and data[i - 1] == OPERATORS['*']\
                               and isinstance(data[i - 2], int):
                                data[i - 2] *= power
                                i += 1
                            else:
                                data.insert(i, OPERATORS['*'])
                                data.insert(i, power)
                                i += 2
                        else:
                            del data[i]
                            del data[i]
                    elif i - 1 >= 0:
                        if data[i - 1] == OPERATORS['*'] and isinstance(data[i - 2], int):
                            del data[i - 1]
                            del data[i - 1]
                    else:
                        data[i] = 1
                i += 1
            return data
        else:
            return joinlist([self._power_rule(x) for x in split], OPERATORS['+'])

    def differentiate(self):
        return Expression(data=
                          self._power_rule(
                              self._remove_constants(self.data[:])))

    @staticmethod
    def _exp_to_str(exp):
        result = str()
        for i in exp:
            result += ' '
            if isinstance(i, str):
                result += i
            elif i in OPERATORS.values():
                for key, value in OPERATORS.items():
                    if value == i:
                        result += key
                        break
            else:
                result += str(i)
        return result.strip()

    def __str__(self):
        return self._exp_to_str(self.data)

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            equal = True
            self_terms = self.tokenize_terms()
            other_terms = other.tokenize_terms()
            for self_term in self_terms:
                if self_term in other_terms:
                    other_terms.remove(self_term)
                else:
                    return False
            return len(other_terms) == 0
        return False
