import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
import heapq
Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])


class State(OrderedDict):
    """ This class is a thin wrapper around an OrderedDict, which is simply a dictionary which keeps the order in
        which elements are added (for consistent key-value pair comparisons). Here, we have provided functionality
        for hashing, should you need to use a state as a key in another dictionary, e.g. distance[state] = 5. By
        default, dictionaries are not hashable. Additionally, when the state is converted to a string, it removes
        all items with quantity 0.

        Use of this state representation is optional, should you prefer another.
    """

    def __key(self):
        return tuple(self.items())

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def copy(self):
        new_state = State()
        new_state.update(self)
        return new_state

    def __str__(self):
        return str(dict(item for item in self.items() if item[1] > 0))


def make_checker(rule):
    # Implement a function that returns a function to determine whether a state meets a
    # rule's requirements. This code runs once, when the rules are constructed before
    # the search is attempted.

    def check(state):
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].
        curr_state = state
        """
        print("curr_state",curr_state)
        for item in curr_state:
            print("item is",item)
        print("curr 0", curr_state[0])
        for item in curr_state[0]:
            print("these",item)
        """
        if "Consumes" in rule.keys():
            for item in rule["Consumes"]:
                #print("item",item)
                if curr_state[0][item] <= 0:
                    return False
        if "Requires" in rule.keys():
            for item in rule["Requires"]:
                if curr_state[0][item] <= 0:
                    return False

        return True

    return check


def make_effector(rule):
    # Implement a function that returns a function which transitions from state to
    # new_state given the rule. This code runs once, when the rules are constructed
    # before the search is attempted.

    def effect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].
        curr_state = state
        next_state = None

        if "Consumes" in rule.keys():
            for item in rule["Consumes"]:
                curr_state[0][item] -= rule["Consumes"][item]
        product_type = rule.get("Produces","")
        num_products = 0
        for result in product_type: #increment based on how many items the rule produced
            num_products += product_type[result]
            curr_state[0][result] += num_products
        next_state = curr_state
        return next_state

    return effect


def make_goal_checker(goal):
    # Implement a function that returns a function which checks if the state has
    # met the goal criteria. This code runs once, before the search is attempted.

    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        """If state == goal: return true...?"""
        for item in state:
            if goal.get(item) is not None: #check if this item is the one we want
                if state.get(item) >= goal.get(item): #check if our state has a sufficient amount of it
                    print(item,"found")
                    return True
        return False

    return is_goal


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    for r in all_recipes:
        if r.check(state):
            yield (r.name, r.effect(state), r.cost)


def heuristic(state):
    # Implement your heuristic here!
    print("state heuristic", state)
    return 0

def search(graph, state, is_goal, limit, heuristic):

    start_time = time()
    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state
    start = state.copy()
    print("state",state)
    print("temp",start)
    #end result list of actions to take to craft goal
    path = []

    #possibility of actions to take at a state
    action_list = []

    #the priority queue of actions to evaluate
    frontier = []
    heapq.heappush(frontier,(start,0))
    #frontier.append(start)

    #links state: next_action_from_applying_a_state
    parent = {}

    #time cost to perform an action
    time_cost = {}

    # nodes we have visited
    came_from = {}
    came_from[start] = None

    cost_so_far = {} #keeps track of cost so far
    cost_so_far[start] = 0

    goal_found = False #bool to track if goal was found
    while time() - start_time < limit and len(frontier) > 0:
        current = frontier.pop()
        print("visiting",current)
        if is_goal(current):
            print("found goal")
            goal_found = True
            break
        for (name,next,cost) in graph(current):
            #assuming cost is cost from current to next
            print("cost_so_far",cost_so_far)
            new_cost = cost_so_far[current[0]] + cost
            #print("next",next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost
                #print("is this why+++++++++++")
                #frontier.append(next)
                heapq.heappush(frontier,(next,priority))
                came_from[next] = current
    #return came_from
    # Failed to find a path

    print(time() - start_time, 'seconds.')
    if not goal_found:
        print("Failed to find a path from", state, 'within time limit.')
    else:
        print("We found the thing")
    return None

if __name__ == '__main__':
    with open('Crafting.json') as f:
        Crafting = json.load(f)

    # # List of items that can be in your inventory:
    # print('All items:', Crafting['Items'])
    #
    # # List of items in your initial inventory with amounts:
    #print('Initial inventory:', Crafting['Initial'])
    #
    # # List of items needed to be in your inventory at the end of the plan:
    #print('Goal:',Crafting['Goal'])
    #
    # # Dict of crafting recipes (each is a dict):
    #print('Example recipe:','craft stone_pickaxe at bench ->',Crafting['Recipes']['craft stone_pickaxe at bench'])

    # Build rules
    all_recipes = []
    for name, rule in Crafting['Recipes'].items():
        checker = make_checker(rule)
        effector = make_effector(rule)
        #print("what???????????????")
        recipe = Recipe(name, checker, effector, rule['Time'])
        all_recipes.append(recipe)

    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])

    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']})
    state.update(Crafting['Initial'])

    # Search for a solution
    #print("SEARCHING")
    resulting_plan = search(graph, state, is_goal, 5, heuristic)

    if resulting_plan:
        # Print resulting plan
        for state, action in resulting_plan:
            #print("searching---")
            print('\t',state)
            print(action)
