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
                #if curr_state[item] <= 0:
                if curr_state[item] > 0:
                    return False

        if "Consumes" in rule.keys():
            for item in rule["Consumes"]:
                #if curr_state[item] < rule["Consumes"][item]:  # fixed this
                if curr_state[item] >= rule["Consumes"][item]: # SWAPPING THIS??? NOT SURE IF CORRECT
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
                #curr_state[item] -= rule["Consumes"][item] SWAPPING HERE
                curr_state[item] += rule["Consumes"][item]

        for keys in rule["Produces"].keys():
            #curr_state[keys] += rule["Produces"][keys] SWAPPING HERE
            curr_state[keys] -= rule["Produces"][keys]
        next_state = curr_state
        return next_state

    return effect


def make_goal_checker(goal):
    # Implement a function that returns a function which checks if the state has
    # met the goal criteria. This code runs once, before the search is attempted.
    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        state = dict(item for item in state.items() if item[1] > 0)
        for goalItem,stateItem in zip(state, goal):
            if goalItem != stateItem:
                return False
        if len(goal) != len(state):
            return False
        #if state is not goal:
            
            #if state[key] < goal[key]: #changing this form < to >
        #    return False
        return True
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
        if "Requires" in rules:
            for item in rules["Requires"]:
                if item in Crafting["Recipes"][action]["Produces"]:
                    modifier -= 200

                if "Consumes" in Crafting["Recipes"][action]:
                    if "Consumes" in rules:
                        for item in rules["Consumes"]:
                            if item in Crafting["Recipes"][action]["Consumes"]:
                                modifier -= 100

    tools = ["stone_pickaxe","bench","cart","wooden_pickaxe","iron_pickaxe","wooden_axe","stone_axe","iron_axe","furnace"]
    for key in state.keys():
        if key in tools:
            if state[key] > 1:
                #return inf
                return 0
    #return modifier
    return 0

def search(graph, state, is_goal, limit, heuristic, rule, Crafting):
    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state

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
    start_time = time()
    curr_state = state.copy()
    frontier = []  # all unexplored nodes (priority queue)
    came_from = {}
    cost_so_far={} # of costs with key state: value (action, cost)
    path = []

    frontier.append((0,"Start",curr_state))
    came_from[curr_state] = ("start", None)
    cost_so_far[curr_state] = 0


    # flip the variables


    while frontier and time() - start_time < limit:
        exploring = heappop(frontier) #  = tuple (timecost, actionname, inventorystate)
        print("explore",exploring[2],exploring[1])
        if is_goal(exploring[2]): # if the next popped thing is the goal
            # print("came from",came_from[exploring[2]])
            prev_state = came_from[exploring[2]]
            #print("previous",came_from[prev_state[1]])
            #print("curr",curr_state)
            path = path_find(prev_state, prev_state, path, came_from, 0) # finds the path from goal to start
            came_from[exploring[2]] = ("Goal", exploring[2]) # set this action to be the goal - final action
            path = [(exploring[2],exploring[1])] + path # append the goal onto there
            path.reverse() # reverses so it prints in the right order
            print(time() - start_time, 'seconds.')
            return path

        for next in graph(exploring[2]): # finds neighbor of the heappop(state) in frontier
            name, effect, cost = next
            new_cost = 0 - cost_so_far[exploring[2]] - cost #calculate timecost

            # if its not in cost_so_far or its a better time, ...
            if effect not in cost_so_far.keys() or new_cost < cost_so_far[effect]: # changed from < to >
                #print("name",name,"cost",new_cost,"effect",effect)
                cost_so_far[effect] = new_cost # cost_so_far[next] = new_cost
                # print("cost of effect",effect,new_cost)
                priority = new_cost + heuristic(effect, name, rule, Crafting)
                heappush(frontier,(priority,name,effect)) # frontier.heappush(priority, action, next_state)
                came_from[effect] = (exploring[1],exploring[2]) #came_from[next] = current

    # Failed to find a path
    print(time() - start_time, 'seconds.')
    print("Failed to find a path from", state, 'within time limit.')
    return None


def path_find(starting_state, prev_state, path, came_from,count):
    if count <= len(came_from): # a count to make sure we don't accidentally recurse for ever
        # print("appending", prev_state[1], prev_state[0]) # just a debugging statement
        path.append((prev_state[1], prev_state[0])) # add the action to the path
        if prev_state[1] not in came_from.keys() or starting_state is prev_state[1]:
            return path # return if it's not in came_from or we have reached the beginning (starting state)
        count += 1 # increment count
        # The Recursive Part:
        path_find(starting_state, came_from[prev_state[1]],path,came_from,count) # call it on the state that led to this state
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
    # is_goal = make_goal_checker(Crafting['Goal'])
    # To make it backwards: 
    is_goal = make_goal_checker(Crafting["Initial"])

    # Initialize first state from initial inventory
    # state = State({key: 0 for key in Crafting['Items']})
    # state.update(Crafting['Initial'])
    # To make it backwards:
    state = State({key: 0 for key in Crafting['Items']})
    state.update(Crafting['Goal'])


    # Search for a solution
    resulting_plan = search(graph, state, is_goal, 30, heuristic, req_rule, Crafting)

    if resulting_plan:
        # Print resulting plan
        print("All Items:",Crafting["Items"])
        print("Initial Inventory:",Crafting["Initial"])
        print("Goal:",Crafting['Goal'])
        print("PATH:")
        del resulting_plan[0]
        for state, action in resulting_plan:
            print('\t',state)
            print(action)
