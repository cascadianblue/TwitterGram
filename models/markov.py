import random
import re
from collections import deque


class Markov:
    '''Graph-based N-Gram Markov Model
    '''
    def __init__(self, n):
        if type(n) != int:
            raise TypeError("N-gram length must be an integer")
        elif n < 2:
            raise ValueError("N-gram length must be at least 2")
        self.n = n
        self.graph = {}

    def add_ngram(self, *ngram):
        '''Add instance of ngram to model
        e.g.

        ngram.add_ngram('hello', 'there', 'world!')

        would increase the probability of "world!" appearing after "hello" and
        "there" (where ngram is an instance of NGram such that n = 3)
        '''
        if len(ngram) != self.n:
            raise ValueError("ngram input must be of length: %d" % (self.n,))

        # FIXME: joining the source tokens (i.e. the prefix) together like this
        # is a hack to make the internal graph JSON-compliant, and wasn't part
        # of the original design. Really, the "Markov" model should never have
        # had any concept of "n-gram", but instead should have simply focused
        # on connecting prefixes to suffixes. Anyway, this *will* cause bugs
        # if, for example, joining then re-tokenizing a set of tokens is not
        # idempotent. Essentially, this is only gonna work for strings that
        # have been tokenized by a non-information destructive regex search.
        source = ''.join(ngram[:-1])
        destination = ngram[-1]

        # Cases:

        # Source has never been recorded
        if source not in self.graph:
            self.graph[source] = {destination: 1}

        # Source has been recorded, but not preceding destination
        elif destination not in self.graph[source]:
            self.graph[source][destination] = 1

        # Source has been recorded, leading to destination
        else:
            self.graph[source][destination] += 1

    def get_suffixes(self, *prefix):
        '''Return mapping of suffixes to probabilities for a given prefix. The
        mapping will be blank if the given prefix has never been observed.

        "prefix" is the first n-1 elements of the ngram, "suffix" is the last
        element of the ngram.
        '''
        # FIXME: This requires adding up all the occurrences of all suffixes for
        #        the given prefix in order to get the total. That means the time
        #        to get the probability of any particular suffix (i.e. ngram) is
        #        linear to the number of unique suffixes of that prefix. This
        #        model should store the total occurrences of a prefix to get
        #        around this, and make the time per suffix lookup constant.

        if len(prefix) != self.n - 1:
            raise ValueError("prefix must be of length: %d" % (self.n-1,))

        try:
            prefix_string = ''.join(prefix)
        except TypeError:
            raise TypeError('prefix is: %s' % (str(prefix),))

        if prefix_string not in self.graph:
            return {}

        mapping = {}
        total_weight = sum(self.graph[prefix_string].values())
        for suffix, weight in self.graph[prefix_string].items():
            mapping[suffix] = weight / total_weight
        return mapping

    def get_ngrams(self, *prefix):
        '''Return map of ngrams to probabilites (between 0.0 and 1.0) for the
        given prefix (the first n-1 tokens of an ngram).
        '''
        suffix_mapping = self.get_suffixes(*prefix)
        ngram_mapping = {}
        for suffix, probability in suffix_mapping.items():
            ngram_mapping[prefix+(suffix,)] = probability
        return ngram_mapping

    def update(self, markov_model):
        '''Add all of the ngram occurrences represented in markov_model to
        self.
        '''
        if self.n != markov_model.n:
            raise ValueError("N-gram lengths %d and %d do not match!" % (self.n, markov_model.n))

        for prefix, suffixes in markov_model.graph.items():
            if prefix not in self.graph:
                self.graph[prefix] = suffixes.copy()
            else:
                for suffix in suffixes:
                    if suffix not in self.graph[prefix]:
                        self.graph[prefix][suffix] = markov_model.graph[prefix][suffix]
                    else:
                        self.graph[prefix][suffix] += markov_model.graph[prefix][suffix]

    def random_suffix(self, *prefix):
        threshhold = random.random()
        upto = 0.0
        for suffix, probability in self.get_suffixes(*prefix).items():
            upto += probability
            if upto >= threshhold:
                return suffix

    def random_ngram(self, *prefix):
        suffix = self.random_suffix(*prefix)
        return prefix + (suffix,)

    def random_sequence(self, *prefix):
        '''Probabilistically walk through the model, starting at prefix, and
        ending at any prefix with no observed suffixes.
        '''
        prefix_length = self.n - 1
        if len(prefix) != prefix_length:
            raise ValueError("Bad prefix length: %d" % (len(prefix),))

        prefix_queue = deque(prefix, prefix_length)
        sequence = list(prefix_queue)

        while True:
            suffix = self.random_suffix(*prefix_queue)
            sequence.append(suffix)
            if suffix == '':
                return sequence
            prefix_queue.append(suffix)

