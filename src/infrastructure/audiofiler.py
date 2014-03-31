import numpy
from scipy.spatial import distance_matrix

class PathToAudio(object):
    def __init__(self, samples_per_second, x_range_mm, y_range_mm):
        self.samples_per_second = samples_per_second
        self.x_range_mm = x_range_mm
        self.y_range_mm = y_range_mm

    def _distance(self, a, b): 
        return distance_matrix([a],[b])[0][0]

    def _get_points(self, start, end, points):
        start = self._to_deflection(start)
        end = self._to_deflection(end)
        x_points = numpy.linspace(start[0], end[0], num=points)
        y_points = numpy.linspace(start[1], end[1], num=points)
        return numpy.column_stack((x_points, y_points))

    def _to_deflection(self, (x ,y)):
        x_deflection = (x / (self.x_range_mm / 2) / 2 ) + 0.5
        y_deflection = (y / (self.y_range_mm / 2) / 2 ) + 0.5
        return (x_deflection,y_deflection)

    def process(self, start, end, speed):
        distance  = self._distance(start, end)
        seconds = distance / speed
        samples = self.samples_per_second * seconds

        return self._get_points(start,end,samples)