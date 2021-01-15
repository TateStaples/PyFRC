class Interpolator:
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def estimate(self, point):
        previous_item = None
        for item in self.dictionary:
            # if you
            if item < point:
                previous_item = item
                continue
            if item == point: return self.dictionary[point]  # if exactly equal to datum
            if previous_item is None: return self.dictionary[point]  # if lower then lowest datum

            nearest_vals = self.dictionary[previous_item], self.dictionary[previous_item]  # the value of low and high point
            distances = point-previous_item, point-item  # how far the point is from each datum
            return weighted_average(values=nearest_vals, weights=distances)
        return self.dictionary.vals()[-1]  # higher than highest datum


def coerce(min, max, val):
    if val < min: return min
    if val > max: return max
    return val


def apply_sign(num, reference):
    return abs(num) * (-1 if reference < 0 else 1)


def average(*args):
    return sum(args) / len(args)


def weighted_average(values, weights):
    return sum(value * weight for value, weight in zip(values, weights))