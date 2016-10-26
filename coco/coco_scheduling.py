from constraint import *
import math


# select a day,time and room for a course
class CourseDomain:
    def __init__(self, day, time, room):
        self.day = day
        self.time = time
        self.room = room


# lectures must not fall on the same day
def not_sameday(a, b):
    if a[0] == b[0]:
        return False
    else:
        return True


def not_redtime(*args):
    for a in args:
        if a[3] < 2:
            return False
        return True


# a is a tuple (day, time slot, lecture hall, pref_code)
def not_bias(*args):
    for a in args:
        if a[3] != 3:
            return False
        return True


# lectures must not fall on the same time
def not_sametime(*args):
    for a in args:
        for b in args:
            if (a != b) and (a[0] == b[0]) and (a[1] == b[1]):
                return False
    return True


# this is a helper function to one_day_interval function,
# input of this function a string representation of a day in the week between monday to friday
# output of this function is a numerical representation of the days of the week
def day_map(a):
    if a.lower() == "monday":
        return 1
    elif a.lower() == "tuesday":
        return 2
    elif a.lower() == "wednesday":
        return 3
    elif a.lower() == "thursday":
        return 4
    elif a.lower() == "friday":
        return 5


# this function ensures a one day constraint between two time slots for a given course
def one_day_interval(a, b):
    temp1 = day_map(a[0])
    temp2 = day_map(b[0])
    if math.fabs(temp1 - temp2) > 1:
        return True
    else:
        return False


def add_variables(problem, variables):
    for var in variables:
        problem.addVariable(var[0], var[1])


def add_func_constraint(problem, constraint, vars=None):
    if vars is None:
        problem.addConstraint(FunctionConstraint(constraint))
    else:
        problem.addConstraint(FunctionConstraint(constraint), vars)


def add_all_constraint(problem):
    problem.addConstraint(AllDifferentConstraint())


problem = Problem()


# for each the solutions we get from the the above schedule
# populate them into our calender, this becomes our base calender
# block entries that are related to vc time slot in our base collection (base collection contains all possible triples
# of time slots lecturer has selected in a week )
# the result of the above becomes our domain
# we redo all different constraints on the new domain; this means we will have multiple results
# replicate our base calender with the solutions. this way we can have multiple results per base calender
