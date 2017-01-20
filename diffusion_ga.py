import numpy
import math


TYPE_BINARY = 0
TYPE_REAL = 1


class DiffusionGA:
    """
    This class implements diffusion model of genetic algorithms. The current implementation supports
    four neighbours (up, down, left, right) of an evaluated cell. The standard selection types aren't
    supported (e.g. "rank", "roulette", "tournament"). The currently supported selection type
    is "select a neighbour with the best fitness value".
    """
    def __init__(self, instance):
        """
        A constructor.

        Args:
            instance (BinaryGA, RealGA): An instance of Binary Genetic Algorithm or of Real GA.
                Type of this instance (binary or real GA) determines behaviour of diffusion model.
        """
        self._ga = instance

        if hasattr(self._ga, '_data'):
            self.type = TYPE_BINARY
        else:
            self.type = TYPE_REAL

        self._fitness_arr = None
        self._individ_arr = None

    @property
    def population(self):
        """
        Returns the following tuple: (array of individuals, array of their fitness values).

        Returns:
           array of individuals, array fitness values (tuple): Array of individuals and another array with
                their fitness values.
        """
        return self._individ_arr, self._fitness_arr

    @property
    def best_solution(self):
        """
        Returns tuple in the following form: (best individual, best fitness value).

        Returns:
            tuple with the currently best found individual and its fitness value.
        """
        return self._ga.best_solution

    def _get_neighbour(self, row, column):
        shape = self._individ_arr.shape
        up, down, left, right = (0, 1, 2, 3)
        DIRS = {
            up: ((row - 1) % shape[0], column),
            down: ((row + 1) % shape[0], column),
            left: (row, (column - 1) % shape[1]),
            right: (row, (column + 1) % shape[1])
        }

        arr_size = len(DIRS)
        fit_arr = numpy.empty(arr_size)
        ind_arr = numpy.empty(arr_size)
        for d, i in zip(list(DIRS.keys()), range(arr_size)):
            fit_arr[i] = self._fitness_arr[DIRS[d]]
            ind_arr[i] = self._individ_arr[DIRS[d]]

        coords_best, _ = self._find_critical_values(fit_arr)

        return ind_arr[coords_best]

    def _compute_diffusion_generation(self, individ_arr):
        """
        This function computes a new generation of the diffusion model of GA.

        Args:
            individ_arr (numpy.array): Diffusion array of individuals (binary encoded, float or a list of floats)
                of the current generation.

        Returns:
            new_individ_array, new_fitness_arr (tuple of numpy.array): New diffusion arrays of individuals
                and fitness values of the next generation.
        """
        shape = individ_arr.shape
        new_individ_arr = numpy.empty(shape, dtype=object)
        new_fitness_arr = numpy.empty(shape)

        for row in range(shape[0]):
            for column in range(shape[1]):
                parent1 = individ_arr[row, column]
                parent2 = self._get_neighbour(row, column)

                # cross parents and mutate a child
                # TODO
                new_individ = numpy.nan_to_num(self._ga._mutate(self._ga._cross(parent1, parent2)))

                # try:
                #     dim = len(new_individ)
                #
                #     for num, d in zip(new_individ, range(dim)):
                #         if num < 0:
                #             new_individ[d] = num % -5
                #         else:
                #             new_individ[d] = num % 5
                # except:
                #     if new_individ < 0:
                #         new_individ %= -5
                #     else:
                #         new_individ %= 5
                        
                # compute fitness value of the child
                fit_val = self._ga._compute_fitness(new_individ)

                new_individ_arr[row, column] = new_individ
                new_fitness_arr[row, column] = fit_val

        coords_best, coords_worst = self._find_critical_values(new_fitness_arr)

        if self._ga.elitism:
            # replace the worst solution in the new generation
            # with the best one from the previous generation
            new_individ_arr[coords_worst] = self._ga.best_individ
            new_fitness_arr[coords_worst] = self._ga.best_fitness

        # update the best solution taking into account a new generation
        self._ga._update_solution(new_individ_arr[coords_best], new_fitness_arr[coords_best])

        return new_individ_arr, new_fitness_arr

    def _find_critical_values(self, fitness_arr):
        """
        Finds 1D or 2D array coordinates of the best and the worst fitness values in the given array.
        Returns coordinates of the first occurrence of these critical values.

        Args:
            fitness_arr (numpy.array): Array of fitness values.

        Returns:
            coords_best, coords_worst (tuple): Coordinates of the best and the worst
                fitness values as (index_best, index_worst) in 1D or
                ((row, column), (row, column)) in 2D.
        """
        # get indices of the best and the worst solutions in new generation
        # actually indices of ALL solutions with the best and the worst fitness values
        indices_max = numpy.where(fitness_arr == fitness_arr.max())
        indices_min = numpy.where(fitness_arr == fitness_arr.min())
        dim = len(fitness_arr.shape)

        if dim > 2:
            print('Only 1D or 2D arrays are supported.')
            raise ValueError

        if self._ga.optim == 'min':
            # fitness minimization
            if dim == 1:
                coords_worst = indices_max[0][0]
                coords_best = indices_min[0][0]
            else:
                coords_worst = (indices_max[0][0], indices_max[1][0])
                coords_best = (indices_min[0][0], indices_min[1][0])
        else:
            # fitness maximization
            if dim == 1:
                coords_worst = indices_min[0][0]
                coords_best = indices_max[0][0]
            else:
                coords_worst = (indices_min[0][0], indices_min[1][0])
                coords_best = (indices_max[0][0], indices_max[1][0])

        return coords_best, coords_worst

    def _construct_diffusion_model(self, population):
        """
        Constructs two arrays: first for individuals of GA, second for their fitness values.
        The current implementation supports construction of only square arrays. Thus, an array side is
        a square root of the given population length. If the calculated square root is a fractional number,
        it will be truncated. That means the last individuals in population will not be
        presented in the constructed arrays.

        Args:
            population (list): An individual of GA. Same as in self.init_population(new_population).
        """
        size = int(math.sqrt(len(population)))

        self._individ_arr = numpy.empty((size, size), dtype=object)
        self._fitness_arr = numpy.empty((size, size))

        index = 0
        for row in range(size):
            for column in range(size):
                self._individ_arr[row, column] = population[index]
                self._fitness_arr[row, column] = self._ga._compute_fitness(population[index])

                index += 1

    def _init_diffusion_model(self, population):
        """
        This function constructs diffusion model from the given population
        and then updates the currently best found solution.

        Args:
            population (list): List of GA individuals.
        """
        self._construct_diffusion_model(population)

        coords_best, _ = self._find_critical_values(self._fitness_arr)
        self._ga._update_solution(self._individ_arr[coords_best], self._fitness_arr[coords_best])

    def init_population(self, new_population):
        """
        Initializes population with the given individuals (individual as binary encoded, float or a list of floats)
        of 'new_population'. The fitness values of these individuals will be computed by a specified fitness function.

        It is recommended to have new_population size equal to some squared number (9, 16, 100, 625 etc.)
        in case of diffusion model of GA. Otherwise some last individuals in the given population will be lost
        as the current implementation works only with square arrays of diffusion model.

        Args:
            new_population (list): New initial population of individuals. A single individual in case of binary GA
                is represented as a list of bits' positions with value 1 in the following way:
                LSB (least significant bit) has position (len(self.data) - 1) and
                MSB (most significant bit) has position 0. If it is a GA on real values, an individual is represented
                as a float or a list of floats in case of multiple dimensions.
        """
        if not new_population or len(new_population) < 4:
            print('New population is too few.')
            raise ValueError

        self._init_diffusion_model(new_population)

    def init_random_population(self, size=None, dim=None, interval=None):
        if self.type == TYPE_BINARY:
            max_num = self._ga._check_init_random_population(size)

            number_list = self._ga._generate_random_population(max_num, size)
            population = [self._ga._get_bit_positions(num) for num in number_list]
        else:
            # there is a GA on real values
            self._ga._check_init_random_population(size, dim, interval)

            individs = self._ga._generate_random_population(size, dim, interval)

            if dim == 1:
                population = [ind[0] for ind in individs]
            else:
                population = individs

        self._init_diffusion_model(population)

    def run(self, max_generation):
        """
        Starts a diffusion GA. The algorithm does 'max_generation' generations and then stops.
        Old population is completely replaced with new one.

        Args:
            max_generation (int): Maximum number of GA generations.

        Returns:
            list of average fitness values for each generation (including original population)
        """
        if max_generation < 1:
            print('Too few generations...')
            raise ValueError

        fitness_progress = []
        # we works with numpy arrays in case of diffusion model
        population_size = self._individ_arr.size

        for generation_num in range(max_generation):
            fitness_sum = numpy.sum(self._fitness_arr)

            fitness_progress.append(fitness_sum / population_size)

            self._individ_arr, self._fitness_arr = self._compute_diffusion_generation(self._individ_arr)

        fitness_progress.append(fitness_sum / population_size)

        return fitness_progress