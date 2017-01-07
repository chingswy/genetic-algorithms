from __future__ import absolute_import
import random

from genetic_algorithms import GeneticAlgorithms, IndividualGA


class BinaryGeneticAlgorithms(GeneticAlgorithms):
    def __init__(self, data=None, fitness_func=None, optim=u'max', selection=u"rank", mut_prob=0.05, mut_type=1,
                 cross_prob=0.95, cross_type=1, elitism=True, tournament_size=None):
        u"""
        Args:
            data (list): A list with elements whose combination will be binary encoded and
                evaluated by a fitness function. Minimum amount of elements is 4.
            fitness_func (function): This function must compute fitness value of an input combination of the given data.
                Function parameters must be: list of used indices of the given data (from 0), list of data itself.
            optim (str): What an algorithm must do with fitness value: maximize or minimize. May be 'min' or 'max'.
                Default is "max".
            selection (str): Parent selection type. May be "rank" (Rank Wheel Selection),
                "roulette" (Roulette Wheel Selection) or "tournament". Default is "rank".
            tournament_size (int): Defines the size of tournament in case of 'selection' == 'tournament'.
                Default is None.
            mut_prob (float): Probability of mutation. Recommended values are 0.5-1%. Default is 0.05.
            mut_type (int): This parameter defines how many random bits of individual are inverted (mutated).
                Default is 1.
            cross_prob (float): Probability of crossover. Recommended values are 80-95%. Default is 0.95.
            cross_type (int): This parameter defines crossover type. The following types are allowed:
                single point (1), two point (2) and multiple point (2 < cross_type <= len(data)).
                The extreme case of multiple point crossover is uniform one (cross_type == len(data)).
                The specified number of bits (cross_type) are crossed in case of multiple point crossover.
                Default is 1.
            elitism (True, False): Elitism on/off. Default is True.
        """
        super(BinaryGeneticAlgorithms, self).__init__(fitness_func, optim, selection,
                         mut_prob, mut_type, cross_prob, cross_type,
                         elitism, tournament_size)
        self._data = data

        if self._data is not None:
            self._bin_length = len(self._data)

        self._check_parameters()

    def _check_parameters(self):
        if self._data is None or self._bin_length < 4 or \
                self.mut_type > self._bin_length or \
                self.cross_type > self._bin_length:
            print u'Wrong value of input parameter.'
            raise ValueError

    def _invert_bit(self, individ, bit_num):
        u"""
        This function mutates the appropriate bits from bit_num of the individual
        with the specified mutation probability.

        Args:
            individ (list): Binary encoded individual (it contains positions of bit 1 according to self.data).
            bit_num (list): List of bits' numbers to invert.

        Returns:
            mutated individual as binary representation (list)
        """
        for bit in bit_num:
            if random.uniform(0, 1) <= self.mutation_prob:
                # mutate
                if bit in individ:
                    # 1 -> 0
                    individ.remove(bit)
                else:
                    # 0 -> 1
                    individ.append(bit)

        return individ

    def _replace_bits(self, source, target, start, stop):
        u"""
        Replace target bits with source bits in interval (start, stop) (both included)
        with the specified crossover probability.

        Args:
            source (list): Values in source are used as replacement for target.
            target (list): Values in target are replaced with values in source.
            start (int): Start point of an interval (included).
            stop (int): End point of an interval (included).

        Returns:
             target with replaced bits with source one in the interval (start, stop) (both included)
        """
        if start < 0 or start >= self._bin_length or \
                stop < 0 or stop < start or stop >= self._bin_length:
            print u'Interval error:', u'(' + unicode(start) + u', ' + unicode(stop) + u')'
            raise ValueError

        if start == stop:
            if random.uniform(0, 1) <= self.crossover_prob:
                # crossover
                if start in source:
                    # bit 'start' is 1 in source
                    if start not in target:
                        # bit 'start' is 0 in target
                        target.append(start)
                else:
                    # bit 'start' is 0 in source
                    if start in target:
                        # bit 'start' is 1 in target
                        target.remove(start)
        else:
            tmp_target = [0] * self._bin_length
            tmp_source = [0] * self._bin_length
            for index in target:
                tmp_target[index] = 1
            for index in source:
                tmp_source[index] = 1

            if random.uniform(0, 1) <= self.crossover_prob:
                # crossover
                tmp_target[start: stop+1] = tmp_source[start: stop+1]

            target = []
            for i in xrange(self._bin_length):
                if tmp_target[i] == 1:
                    target.append(i)

        return target

    def _compute_fitness(self, individ):
        u"""
        This function computes fitness value of the given individual.

        Args:
            individ (list): A binary encoded individual of genetic algorithm.
                Defined fitness function (self.fitness_func) must deal with this individual.

        Returns:
            fitness value of the given individual
        """
        return self.fitness_func(individ, self._data)

    def _get_bit_positions(self, number):
        u"""
        This function gets a decimal integer number and returns positions of bit 1 in
        its binary representation. However, these positions are transformed the following way: they
        are mapped on the data list (self.data) "as is". It means that LSB (least significant bit) is
        mapped on the last position of the data list (e.g. self._bin_length - 1), MSB is mapped on
        the first position of the data list (e.g. 0) and so on.

        Args:
            number (int): This decimal number represents binary encoded combination of the input data (self.data).

        Returns:
             list of positions with bit 1 (these positions are mapped on the input data list "as is" and thus,
             LSB is equal to index (self._bin_length - 1) of the input data list).
        """
        binary_list = []

        for i in xrange(self._bin_length):
            if number & (1 << i):
                binary_list.append(self._bin_length - 1 - i)

        return binary_list

    def init_random_population(self, size=None):
        u"""
        Initializes a new random population of the given size.

        Args:
            size (int): Size of a new random population. If None, the size is set to (2**self._bin_length) / 10, because
                self._bin_length is a number of bits. Thus, a new population of size 10% of all possible solutions
                (or of size 4 in case of self._bin_length < 5) will be created.
        """
        max_num = 2 ** self._bin_length

        if size is None:
            if max_num < 20:
                size = 4
            else:
                # 10% of all possible solutions
                size = max_num // 10
        elif size < 2 or size >= max_num:
            print u'Wrong size of population:', size
            raise ValueError

        # generate population
        number_list = self._random_diff(max_num, size, start=1)

        self.population = []
        for num in number_list:
            individ = self._get_bit_positions(num)
            fit_val = self._compute_fitness(individ)

            self.population.append(IndividualGA(individ, fit_val))

        self._sort_population()

