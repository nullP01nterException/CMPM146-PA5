import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
from heapq import heappop, heappush
from math import inf

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
        curr_state = state.copy()
        if "Requires" in rule.keys():
            for item in rule["Requires"]:
                if curr_state[item] <= 0:
                    return False

        if "Consumes" in rule.keys():
            for item in rule["Consumes"]:
                if curr_state[item] < rule["Consumes"][item]:  # fixed this
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
        curr_state = state.copy()
        next_state = None
        if "Consumes" in rule.keys():
            for item in rule["Consumes"]:
                curr_state[item] -= rule["Consumes"][item]

        for keys in rule["Produces"].keys():
            curr_state[keys] += rule["Produces"][keys]
        next_state = curr_state
        return next_state

    return effect


def make_goal_checker(goal):
    # Implement a function that returns a function which checks if the state has
    # met the goal criteria. This code runs once, before the search is attempted.
    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        for key in goal.keys():
            if state[key] < goal[key]:
                return False
        return True
        #for item in state: #Changed back to this one because the other one was causing an error
        #    if goal.get(item) is not None:  # check if this item is the one we want
        #        if state.get(item) >= goal.get(item):  # check if our state has a sufficient amount of it
        #            print(item, "found")
        #            return True
        #return False

    return is_goal


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    #print("stuck in graph?")
    for r in all_recipes:
        if r.check(state):
            yield (r.name, r.effect(state), r.cost)


def heuristic(state, action, rule,Crafting):
    # Implement your heuristic here!
    modifier = 0

    for rules in rule:
        for item in rules["Requires"]:
            if item in Crafting["Recipes"][action]["Produces"]:
                modifier -= 200

            if "Consumes" in Crafting["Recipes"][action]:
                for item in rules["Consumes"]:
                    if item in Crafting["Recipes"][action]["Consumes"]:
                        modifier -= 100



    tools = ["stone_pickaxe","bench","cart","wooden_pickaxe","iron_pickaxe","wooden_axe","stone_axe","iron_axe","furnace"]
    for key in state.keys():
        if key in tools:
            if state[key] > 1:
                return inf
    return modifier

def search(graph, state, is_goal, limit, heuristic, rule, Crafting):

    start_time = time()
    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state
    path = []

    """frontier[] all unexplored nodes (priority queue)
    costsofar{} of costs with key state: value (action, cost)
    exploring = tuple (timecost, actionname, inventorystate)
    graph() finds neighbor of the heappop(state) in frontier

    for actions in graph(current_state)
        calculate timecost
        if timecost not in costsofar or less than prerecorded timecost
            costsofar[next] = newcost
            priority = newcost + heuristic(currstate)
            frontier.heappush(prioirty, action, nextstate)
            camefrom[next] = current
    """
    curr_state = state.copy()
    frontier = []
    came_from = {}
    cost_so_far={}

    frontier.append((0,"Start",curr_state))
    came_from[curr_state] = ("start", None)
    cost_so_far[curr_state] = 0

    #while time() - start_time < limit:
    while frontier and time() - start_time < limit:
        exploring = heappop(frontier)
        #print("explore",exploring[2])
        if is_goal(exploring[2]):

            #print("came from",came_from[exploring[2]])
            prev_state = came_from[exploring[2]]
            #print("previous",came_from[prev_state[1]])
            came_from[exploring[2]] = ("Goal", exploring[2])
            #print("curr",curr_state)
            path = path_find(prev_state, prev_state,path,came_from,0)
            path = [(exploring[2],exploring[1])] + path
            #path.append((curr_state, came_from[curr_state][0]))
            path.reverse()
            print(time() - start_time, 'seconds.')
            return path

            return path
        for next in graph(exploring[2]):
            name, effect, cost = next
            new_cost = cost_so_far[exploring[2]] + cost
            if effect not in cost_so_far.keys() or new_cost < cost_so_far[effect]:
                #print("name",name,"cost",new_cost,"effect",effect)
                #print("cost",new_cost)
                cost_so_far[effect] = new_cost
                priority = new_cost + heuristic(effect, name, rule, Crafting)
                #frontier.append((priority, name, effect))
                heappush(frontier,(priority,name,effect))
                came_from[effect] = (exploring[1],exploring[2])
                #print("came",came_from)
        #print("------------------------")

    # Failed to find a path
    print(time() - start_time, 'seconds.')
    print("Failed to find a path from", state, 'within time limit.')
    return None


def path_find(starting_state, prev_state, path, came_from,count):
    #end = (starting_state, came_from[starting_state])
    #print("end", end)
    #if end not in path:
    #print("starting state",starting_state)
    #print("prev_state",prev_state)
    #print("-")
    if count <= len(came_from):
        #print("appending", prev_state[1], prev_state[0])
        path.append((prev_state[1], prev_state[0]))
        if prev_state[1] not in came_from.keys() or starting_state is prev_state[1]:
            return path
        count += 1
        path_find(starting_state, came_from[prev_state[1]],path,came_from,count)
    return path

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
    req_rule = []

    for name, rule in Crafting['Recipes'].items():
        checker = make_checker(rule)
        effector = make_effector(rule)
        recipe = Recipe(name, checker, effector, rule['Time'])
        all_recipes.append(recipe)

        for key in rule["Produces"]:
            if key in Crafting["Goal"].keys():
                req_rule.append(rule)


    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])

    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']})
    state.update(Crafting['Initial'])

    # Search for a solution
    resulting_plan = search(graph, state, is_goal, 30, heuristic, req_rule, Crafting)

    if resulting_plan:
        # Print resulting plan
        print("All Items")
        print("Initial Inventory",state)
        print("Goal",Crafting['Goal'])
        print("PATH:")
        del resulting_plan[0]
        for state, action in resulting_plan:
            print('\t',state)
            print(action)
