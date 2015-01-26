import inspect

from domain.layer_generator import LayerGenerator
from infrastructure import print_test_layer_generators


class TestPrintAPI(object):
    def __init__(self):
        self.test_prints = self._get_test_prints()

    def test_print_names(self):
        return self.test_prints.keys()

    def get_test_print(self, name, height, width, layer_height, speed=100):
        return self.test_prints[name](height, width, layer_height, speed)

    def _get_test_prints(self):
        available_prints = {}
        for name in dir(print_test_layer_generators):
            obj = getattr(print_test_layer_generators, name)
            if inspect.isclass(obj):
                if issubclass(obj, LayerGenerator):
                    if hasattr(obj, 'name'):
                        available_prints[obj.name] = obj
        return available_prints
