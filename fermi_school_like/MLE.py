import numpy as np
import scipy.optimize
from data_generative_process import DataGenerativeProcess

class Likelihood(object):

    def __init__(self, x, data, model):

        self._x = x
        self._data = data
        self._model = model
        self._original_parameters = self._model.current_parameters
        self._noise_model = None

        assert np.all( (self._data >= 0) ), "Data must be >= 0"

    def _set_noise_model(self, noise_model):

        if noise_model.lower() == 'poisson':

            self._noise_model = 'poisson'

        elif noise_model.lower() == 'gaussian':

            self._noise_model = 'gaussian'

        else:

            raise ValueError("Noise model %s not known. Use 'poisson' or 'gaussian'." % noise_model)

    def _get_noise_model(self):

        return self._noise_model

    noise_model = property(_get_noise_model, _set_noise_model, doc='''Sets or gets the noise model''')

    def _poisson_like(self, parameters):

        prediction = self._model.evaluate(self._x, parameters)

        return np.sum( self._data * np.log(prediction) - prediction)

    def _gaussian_like(self, parameters):

        prediction = self._model.evaluate(self._x, parameters)

        variances = np.sqrt(self._data)

        chisq = np.sum( (self._data - prediction)**2 / variances**2 )

        return -0.5 * chisq

    def maximize(self):

        assert self._noise_model is not None, "You have to set up a noise model first"

        # Scipy minimizes, not maximizes
        if self._noise_model == 'poisson':

            minus_log_like = lambda x: - self._poisson_like(x)

        else:

            minus_log_like = lambda x: - self._gaussian_like(x)

        # Initial value: use the current value for the parameters
        initial_values = self._model.current_parameters

        res = scipy.optimize.minimize(minus_log_like, initial_values)

        return res.x

    def generate_and_fit(self, n_iter):
        """
        Generate data and fit them for the specified number of times

        :param n_iter: number of times
        :return: array of results
        """

        results = []

        for i in range(len(self._model.current_parameters)):

            results.append([])

        for i in range(n_iter):

            # Set back to initial parameters
            self._model.current_parameters = self._original_parameters

            data = DataGenerativeProcess(self._model).generate(self._x)

            this_like = Likelihood(self._x, data, self._model)

            this_like.noise_model = self.noise_model

            this_results = this_like.maximize()

            for i, par in enumerate(this_results):

                results[i].append(par)

        return results