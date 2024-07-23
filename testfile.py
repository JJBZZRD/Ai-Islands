def combine_numbers(a, b):
    if a % 2 == 0 and b % 2 == 0:  # both numbers are even
        return a + b
    elif a % 2 != 0 and b % 2 != 0:  # both numbers are odd
        return a - b
    else:  # one even, one odd
        return a * b