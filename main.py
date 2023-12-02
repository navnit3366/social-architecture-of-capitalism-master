# -*- coding: utf-8 -*-
"""reto-termo-final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pzzOV_X9Yc3bMVMnXUtvgg5GrCc8HClV

# Implementación de interacciones económicas
Simulación de la evolución de un sistema aisaldo económico definido en "The social architecture of capitalism" de Ian Wright.
"""

# External
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import colour

# Built-int
import math
import random

# Froms
from random import normalvariate, choices
from numpy.random import seed
from numpy.random import normal
from itertools import chain
from colour import Color
from collections import Counter


def entropy_sum(data):
    '''
    Sum formula for entropy calculation
    '''
    sum = 0
    for k in data:
        if k > 0:
            sum += k * np.log(k)
    return sum


def entropy(N, C, data):
    '''
    Entropy within system
    '''
    S = N * np.log(N) - entropy_sum(data)
    return S


mc = 50
a = 1 / mc


def O(M):
    return 1 - np.exp(-a * M)


def commonwealth_function(N, C, bins, people):
    acc = 0
    sum = 0

    for k in bins:
        if k == 0:
            continue

        mk = np.average(people[int(acc): int(acc + k)])
        o = O(mk)
        sum += k * o
        acc += k
    return sum

# Random choice from normal distribution


def normal_choice(lst, mean=None, stddev=None):
    if mean is None:
        # if mean is not specified, use center of list
        mean = (len(lst) - 1) / 2

    if stddev is None:
        # if stddev is not specified, let list be -3 .. +3 standard deviations
        stddev = len(lst) / 6

    counter = 0
    while True:
        index = int(normalvariate(mean, stddev) + 0.5)
        if 0 <= index < len(lst):
            return lst[index]

# Define an economic actor


class Actor:
    def __init__(self, id, coins):
        '''
        Create an actor
        '''
        self.id = id
        self.coins = coins
        self.employer = 0
        self.employees = []
        self.yearly_income = 0

    def is_active(self):
        '''
        Check if actor is active (economically)
        '''
        return self.is_employed() or self.is_employer()

    def is_unemployed(self):
        return self.employer == 0

    def is_employed(self):
        return self.employer != 0

    def is_employer(self):
        return len(self.employees) > 0

    def employ_self(self, employer_id):
        '''
        Set employer index and update ocupation status to employed
        '''
        self.employer = employer_id
        self.employees = []

    def unemploy_self(self):
        '''
        Remove employer index and set occupation to unemployed
        '''
        self.employer = 0
        self.employees = []

    def employ_other(self, id):
        '''
        Add employee index to employee set. Update ocupation status to employer
        '''
        self.employees.append(id)

    def unemploy_other(self, employee_id):
        '''
        Enemploy based on employee index. If firm loses all employees, return True
        '''
        pos = self.employees.index(employee_id)
        self.employees.pop(pos)
        if len(self.employees) == 0:
            return True
        return False

    def random_expenditure(self):
        '''
        Select a random amount to spend
        '''
        a = 0
        b = self.coins

        if b <= 0:
            return 0

        expenditure_interval = list(range(a, math.floor(b) + 1))
        expenditure = normal_choice(expenditure_interval)

        return expenditure

    def add_coins(self, amount):
        self.coins += amount
        self.yearly_income += amount

    def remove_coins(self, amount):
        self.coins -= amount

    def reset_yearly_income(self):
        self.yearly_income = 0

# Define simulation world


class MaterialWorld:
    # Fixed wages
    wa = 10
    wb = 90
    wage_interval = list(range(wa, wb + 1))
    wage_avg = (wb - wa) / 2

    # For market redistribution
    market_value = 0

    def __init__(self, N, M):
        '''
        Initialize simulation with initial conditions
        '''
        initial_coins = M / N
        actors = []
        for i in range(N):
            actors.append(Actor(i, initial_coins))

        self.actors = actors
        self.Money = M
        self.N = N
        self.analyzer = Analyzer()

    def select_actor(self):
        '''
        Randomly select an actor. Returns an Actor object.
        '''
        return normal_choice(self.actors)

    def potential_employers(self):
        '''
        Returns list of indices of all employers
        '''
        return list(filter(lambda actor: actor.is_unemployed() or actor.is_employer(), self.actors))

    def select_employer(self):
        '''
        Randomly select an employer. Returns an Actor object.
        '''
        employers = self.potential_employers()
        total_coins = 0
        weights = []

        for e in employers:
            total_coins += e.coins

        for e in employers:
            weights.append(e.coins / total_coins)

        options = random.choices(employers, weights, k=1)
        return options[0]

    def hiring_rule(self, actor):
        '''
        Randomly employ someone
        '''
        # Check if actor already employed
        if actor.is_active():
            return

        # Select employer
        employer = self.select_employer()

        # One cannot employ oneself
        if employer.id == actor.id:
            return

        # If employer has enough money, hire
        if (employer.coins > self.wage_avg):
            employer.employ_other(actor.id)
            actor.employ_self(employer.id)

    def expenditure_rule(self, actor):
        '''
        Random actor expenses
        '''
        # Actors that are not current actor
        b = actor
        while b.id == actor.id:
            b = self.select_actor()

        # Create expenditure
        exp = b.random_expenditure()
        b.remove_coins(exp)

        # Add to market value
        self.market_value += exp

    def random_revenue(self):
        '''
        Select a random revenue to take from market value
        '''
        revenue_interval = list(range(0, self.market_value + 1))
        return normal_choice(revenue_interval)

    def market_sample_rule(self, actor):
        '''
        Random firm revenue M1. Returns Revenue.
        '''
        # Check if actor is not unemployed
        if (actor.is_unemployed()):
            return 0

        # Select random revenue
        random_revenue = self.random_revenue()

        # Depending on actor type, add revenue to firm owner
        if (actor.is_employed()):
            index = actor.employer
            self.actors[index].add_coins(random_revenue)

        if (actor.is_employer()):
            actor.add_coins(random_revenue)

        # Update market value
        self.market_value -= random_revenue

        return random_revenue

    def firing_rule(self, actor):
        '''
        Fire based on max money. Returns if firm is bankrupt.
        '''
        # If actor not employer, do nothing
        if (not actor.is_employer()):
            return False

        # Amount of average wages
        u = math.ceil(len(actor.employees) - (actor.coins / self.wage_avg))

        # Count how many average wages cannot be payed
        if u <= 0:
            return False

        # Enemploy randomly
        firm_demise = False

        for i in range(u):
            id = normal_choice(actor.employees)
            firm_demise = actor.unemploy_other(id) or firm_demise
            self.actors[id].unemploy_self()

            if firm_demise:
                break

        return firm_demise

    def random_wage(self):
        '''
        Get a random wage based on parameters
        '''
        return normal_choice(self.wage_interval)

    def wage_payment_rule(self, actor):
        '''
        Pay wages to all employees. Return total wage bill
        '''
        wage_bill = 0
        wage = self.random_wage()

        for i in actor.employees:
            # Get random wage
            if (actor.coins - wage < 0):
                wage = actor.random_expenditure()

            self.actors[i].add_coins(wage)
            actor.remove_coins(wage)
            wage_bill += wage

        return wage_bill

    def simulation_rule(self):
        '''
        Excecute all rules based on random actor
        '''
        actor = self.select_actor()

        self.hiring_rule(actor)

        self.expenditure_rule(actor)

        revenue = self.market_sample_rule(actor)

        firm_demise_flag = self.firing_rule(actor)

        wage_bill = self.wage_payment_rule(actor)

        return [firm_demise_flag, revenue, wage_bill]

    def one_month_rule(self):
        '''
        Excecute simulation N times, allowing every actor to have an opportunity to act
        '''
        firm_demise_counter = 0
        revenue_counter = 0
        total_wage_bill = 0

        for i in range(self.N):
            [firm_demise, revenue, wage_bill] = self.simulation_rule()

            revenue_counter += revenue
            total_wage_bill += wage_bill

            if firm_demise:
                firm_demise_counter += 1

        self.analyzer.firm_size_measure(self.actors)

        return [firm_demise_counter, revenue_counter, total_wage_bill]

    def one_year_rule(self):
        '''
        Repeat a month 12 times
        '''
        total_revenue = 0
        total_wage_bill = 0

        for i in range(12):
            [firm_demises, revenue, wage_bill] = self.one_month_rule()
            total_revenue += revenue
            total_wage_bill += wage_bill

            self.analyzer.firm_demise_measure(firm_demises)

        self.analyzer.add_yearly_revenue(total_revenue)
        self.analyzer.add_yearly_wage_bill(total_wage_bill)
        self.analyzer.class_size_measure(self.actors)
        self.analyzer.incomes_and_wealth_measure(self.actors)

    def run_sim(self, years):
        '''
        Excecute a simulation rule for arbitrary year number
        '''
        print(f'Starting simulation for {years} years')
        for i in range(years):
            if i % 10 == 0:
                print(f"year {i} running")
            self.one_year_rule()

        print('Doing futher analysis (GDP, ...)')
        self.analyzer.gdp_growth_measures()


class Analyzer:
    def __init__(self):
        # Per year
        self.class_measures = []
        self.revenues = []
        self.gdp_growth = [1]
        self.recessions = []
        self.wage_bills = []
        self.wage_shares = []
        self.profit_shares = []
        self.actor_incomes = []
        self.actor_wealths = []

        self.capitalist_incomes = []
        self.capitalist_wealths = []
        self.worker_incomes = []
        self.worker_wealths = []

        self.commonwealths = []

        # Per month
        self.firm_sizes = []
        self.firm_demises = []

    def class_size_measure(self, actors):
        '''
        Sepparate by classes
        '''
        unemployed = 0
        workers = 0
        capitalists = 0
        undef = 0
        capitalist_incomes = []
        capitalist_wealths = []
        worker_incomes = []
        worker_wealths = []

        for actor in actors:
            if (actor.is_employer()):
                capitalists += 1
                capitalist_incomes.append(actor.yearly_income)
                capitalist_wealths.append(actor.coins)
            elif (actor.is_employed()):
                workers += 1
                worker_incomes.append(actor.yearly_income)
                worker_wealths.append(actor.coins)
            elif (actor.is_unemployed()):
                unemployed += 1
            else:
                undef += 1
        data = [unemployed, workers, capitalists, undef]

        self.capitalist_incomes.append(capitalist_incomes)
        self.capitalist_wealths.append(capitalist_wealths)
        self.worker_incomes.append(worker_incomes)
        self.worker_wealths.append(worker_wealths)
        self.class_measures.append(data)

    def firm_size_measure(self, actors):
        '''
        Measures firm size
        '''
        for actor in actors:
            if actor.is_employer():
                size = len(actor.employees)
                self.firm_sizes.append(size)

    def firm_demise_measure(self, demises):
        '''
        Appends demises to list
        '''
        self.firm_demises.append(demises)

    def add_yearly_revenue(self, revenue):
        '''
        Add revenue per year
        '''
        self.revenues.append(revenue)

    def add_yearly_wage_bill(self, wage_bill):
        '''
        Adds total wages payed to workers.
        '''
        self.wage_bills.append(wage_bill)

    def gdp_growth_measures(self):
        '''
        Measures GDP growth, compared to previous year.
        Also measures recessions.
        '''
        revenues = self.revenues
        wages = self.wage_bills

        recession_duration = 0
        for i in range(1, len(revenues)):
            gdp_growth = revenues[i] / revenues[i - 1]
            wage_share = wages[i] / revenues[i]
            profit_share = 1 - wage_share

            if gdp_growth < 1:
                recession_duration += 1

            if gdp_growth > 1 and recession_duration != 0:
                self.recessions.append(recession_duration)
                recession_duration = 0

            self.gdp_growth.append(gdp_growth-1)
            self.wage_shares.append(wage_share)
            self.profit_shares.append(profit_share)

    def incomes_and_wealth_measure(self, actors):
        '''
        Collect yearly incomes and add to dataset.
        '''
        incomes = []
        wealths = []

        for actor in actors:
            incomes.append(actor.yearly_income)
            wealths.append(actor.coins)
            actor.reset_yearly_income()

        self.actor_incomes.append(incomes)
        self.actor_wealths.append(wealths)

    def entropy_analysis(self, N, wealth_cap=0):
        classes = 100
        min_wealth = 0
        max_wealth = wealth_cap

        if wealth_cap == 0:
            max_wealth = max(max(self.actor_wealths))

        d = max_wealth / classes
        bins = range(0, math.ceil(max_wealth) + 1, math.ceil(d))
        print(bins)

        entropy_evolution = []

        for yearly_actor_wealths in self.actor_wealths:
            class_count = [0] * classes
            (h, _, _) = plt.hist(yearly_actor_wealths, bins=bins)
            s = entropy(N, classes, h)
            entropy_evolution.append(s)

        return entropy_evolution

    def aggregated_income_analysis(self):
        # General income ccdf
        income_aggregation = np.sum(self.actor_incomes, 0)
        data = income_aggregation
        general_values, general_base = np.histogram(data, bins=100)
        general_cum = np.cumsum(general_values)

        # Income ccdf by class
        capitalist = list(chain(*self.capitalist_incomes))
        worker = list(chain(*self.worker_incomes))

        capitalist_incomes = np.array(capitalist)
        worker_incomes = np.array(worker)

        capitalist_values, capitalist_base = np.histogram(
            capitalist_incomes, bins=100)
        worker_values, worker_base = np.histogram(worker_incomes, bins=100)

        capitalist_cum = np.cumsum(capitalist_values) / N
        worker_cum = np.cumsum(worker_values) / N

        # Lower regime income distribution

        # Higher regime ccdf

        # Plot figure
        figure, axis = plt.subplots(2, 2)

        # Plot income ccdf in log-log scale
        axis[0, 0].set_xscale('log')
        axis[0, 0].set_yscale('log')
        axis[0, 0].plot(general_base[:-1], len(data) - general_cum, c='green')

        # Plot income ccdf by class in log-log scale
        axis[0, 1].set_xscale('log')
        axis[0, 1].set_yscale('log')
        axis[0, 1].plot(capitalist_base[:-1],
                        len(capitalist_incomes) - capitalist_cum, c='green')
        axis[0, 1].plot(worker_base[:-1],
                        len(worker_incomes) - worker_cum, c='blue')

        # Plot lower regime income dist in log-lin scale
        axis[1, 0].set_xscale('log')
        d = pd.DataFrame(income_aggregation).value_counts()
        d.plot(ax=axis[1, 0], kind='bar')

        # Plot higher regime ccdf in log-log scale
        plt.show()

    def disaggregated_income_analysis_per_year(self, years, step):
        figure, axis = plt.subplots(1, 2)

        green = Color("green")
        blue = Color("blue")

        green_range = list(green.range_to(blue, years))

        for i in range(0, years, step):
            # Income ccdf by class
            capitalist = self.capitalist_incomes[i]
            worker = self.worker_incomes[i]

            capitalist_incomes = np.array(capitalist)
            worker_incomes = np.array(worker)

            capitalist_values, capitalist_base = np.histogram(
                capitalist_incomes, bins=100)
            worker_values, worker_base = np.histogram(worker_incomes, bins=100)

            capitalist_cum = np.cumsum(capitalist_values) / N
            worker_cum = np.cumsum(worker_values) / N

            # Lower regime income distribution

            # Plot income ccdf by class in log-log scale
            c = green_range[i].get_rgb()
            axis[0].plot(capitalist_base[:-1],
                         len(capitalist_incomes) - capitalist_cum, c=c)
            axis[1].plot(worker_base[:-1],
                         len(worker_incomes) - worker_cum, c=c)

        axis[0].set_xscale('log')
        axis[0].set_yscale('log')
        axis[1].set_xscale('log')
        axis[1].set_yscale('log')
        plt.show()

    def aggregated_wealth_analysis(self):
        # General income ccdf
        income_aggregation = np.sum(self.actor_wealths, 0)
        data = income_aggregation
        general_values, general_base = np.histogram(data, bins=100)
        general_cum = np.cumsum(general_values)

        # Income ccdf by class
        capitalist = list(chain(*self.capitalist_wealths))
        worker = list(chain(*self.worker_wealths))

        capitalist_incomes = np.array(capitalist)
        worker_incomes = np.array(worker)

        capitalist_values, capitalist_base = np.histogram(
            capitalist_incomes, bins=100)
        worker_values, worker_base = np.histogram(worker_incomes, bins=100)

        capitalist_cum = np.cumsum(capitalist_values) / N
        worker_cum = np.cumsum(worker_values) / N

        # Lower regime income distribution

        # Higher regime ccdf

        # Plot figure
        figure, axis = plt.subplots(2, 2)

        # Plot income ccdf in log-log scale
        axis[0, 0].set_xscale('log')
        axis[0, 0].set_yscale('log')
        axis[0, 0].plot(general_base[:-1], len(data) - general_cum, c='green')

        # Plot income ccdf by class in log-log scale
        axis[0, 1].set_xscale('log')
        axis[0, 1].set_yscale('log')
        axis[0, 1].plot(capitalist_base[:-1],
                        len(capitalist_incomes) - capitalist_cum, c='green')
        axis[0, 1].plot(worker_base[:-1],
                        len(worker_incomes) - worker_cum, c='blue')

        # Plot lower regime income dist in log-lin scale
        axis[1, 0].set_xscale('log')
        d = pd.DataFrame(income_aggregation).value_counts()
        d.plot(ax=axis[1, 0], kind='bar')

        # Plot higher regime ccdf in log-log scale
        plt.show()

    def commonwealth_analysis(self, N, classes, wealth_cap=0):
        max_wealth = wealth_cap

        if wealth_cap == 0:
            max_wealth = max(max(self.actor_wealths))

        d = max_wealth / classes
        bins = range(0, math.ceil(max_wealth) + 1, math.ceil(d))
        print(bins)

        for yearly_actor_wealths in self.actor_wealths:
            (h, _, _) = plt.hist(yearly_actor_wealths, bins=bins)
            commonwealth = commonwealth_function(
                N, classes, h, yearly_actor_wealths)
            self.commonwealths.append(commonwealth)

        # Plot commonwealth evolution
        years = range(0, 100)
        figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)
        plt.plot(years, self.commonwealths)
        plt.show()


# Simulation conditions
N = 1_000
M = 100_000
world = MaterialWorld(N, M)

# Run 100 years
world.run_sim(100)

analyzer = world.analyzer

print(analyzer.class_measures)

print(analyzer.firm_sizes)

max(analyzer.firm_sizes)

print(analyzer.firm_demises)

print(analyzer.gdp_growth)

print(analyzer.recessions)

# sum(analyzer.recessions)

print(analyzer.wage_shares)

print(analyzer.profit_shares)

sum = 0
for p in world.actors:
    sum += p.coins
    if p.coins < 0:
        print(p.id)
        print(p.coins)

print(f'total money: {sum}')

print(max(max(analyzer.actor_incomes)))

print(max(max(analyzer.actor_wealths)))

ent = analyzer.entropy_analysis(N)

years = range(0, 100)
plt.plot(years, ent)

ent = analyzer.entropy_analysis(N, 1000)

years = range(0, 100)
plt.plot(years, ent)

ent = analyzer.entropy_analysis(N, 2000)

years = range(0, 100)
plt.plot(years, ent)

ent = analyzer.entropy_analysis(N, 5000)

years = range(0, 100)
plt.plot(years, ent)

analyzer.aggregated_income_analysis()

analyzer.aggregated_wealth_analysis()

analyzer.commonwealth_analysis(N, 20, 1000)

analyzer.disaggregated_income_analysis_per_year(100, 10)

capitalists = []
workers = []
unemployed = []

for [u, w, c, _] in analyzer.class_measures:
    workers.append(w)
    capitalists.append(c)
    unemployed.append(u)

(h, _, _) = plt.hist(unemployed, bins=20)

plt.show()

(h, _, _) = plt.hist(workers, bins=20)
plt.show()

(h, _, _) = plt.hist(capitalists, bins=20)
plt.show()

years = range(0, 99)
profit_share = analyzer.profit_shares
wage_share = analyzer.wage_shares
plt.plot(years, profit_share)
plt.plot(years, wage_share)

firm_demises = analyzer.firm_demises
firm_demises.sort()
count = Counter(firm_demises)
count[0] = 0
df = pd.DataFrame.from_dict(count, orient='index')
df.plot(kind='bar')

recessions = analyzer.recessions
recessions.sort()
count = Counter(recessions)
count[0] = 0
df = pd.DataFrame.from_dict(count, orient='index')
df.plot(kind='bar')

gdp = analyzer.gdp_growth
gdp = list(filter(lambda a: a < 7.5, gdp))
gdp = [round(item, 1) for item in gdp]

gdp.sort()
print(gdp)

count = Counter(gdp)
df = pd.DataFrame.from_dict(count, orient='index')
# plt.xscale('log')
df.plot(kind='bar', logy=True)

incomes = analyzer.worker_incomes[:-1][0]
print(np.mean(incomes))
