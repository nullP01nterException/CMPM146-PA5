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
    for key in goal.keys():
        print("key",key)
    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        for key in goal.keys():
            if state[key] < goal[key]:
                return False
            #print("key!!",key)
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


def heuristic(state, action, rule, Crafting, consumed, required, goals):
    # Implement your heuristic here!
    #print("////////////",action)
    modifier = 0

    for product in Crafting["Recipes"][action]["Produces"]:
        if product in goals:
            if product not in required and product not in consumed:
                modifier -= 400
            modifier -= 300
        elif product in required or product in consumed:
            if product is "stick" and state[product] <= 2:
                modifier -= 100
            elif product is "wood" and state[product] <= 4:
                modifier -= 100
            elif product is "coal" and state[product] <= 2:
                modifier -= 100
            if product is "rail" and state[product] <= 36:
                modifier -= 100
            elif state[product] <= 8:
                modifier -= 100
        

    for rules in rule:
        if "Requires" in rules:
            for item in rules["Requires"]:
                if item in Crafting["Recipes"][action]["Produces"]:
                    modifier -= 300
                    # modifier += 0

                if "Consumes" in Crafting["Recipes"][action]:
                    if "Consumes" in rules:
                        for item in rules["Consumes"]:
                            if item in Crafting["Recipes"][action]["Consumes"]:
                                modifier -= 50

    tools = ["stone_pickaxe","bench","cart","wooden_pickaxe","iron_pickaxe","wooden_axe","stone_axe","iron_axe","furnace"]
    best_tools = ["iron_pickaxe","iron_axe"]
    good_tools = ["stone_pickaxe","stone_axe"]
    usable_tools = ["wooden_pickaxe","wooden_axe"]

    for key in state.keys():
        if key in best_tools and state[key] == 1:
            #print("00000000000000000000key", key, "--action", action)
            if key is "iron_pickaxe" and ("stone_pickaxe for" in action or "wooden_pickaxe for" in action):
                return inf
            elif key is "iron_axe" and ("stone_axe for" in action or "wooden_axe for" in action):
                return inf
        elif key in good_tools and state[key] == 1:
            #print("00000000000000000000key", key, "--action", action)
            if key is "stone_pickaxe" and "wooden_pickaxe for" in action:
                #print("here")
                return inf
            elif key is "stone_axe" and "wooden_axe for" in action:
                return inf
        elif key in usable_tools and "punch" in action:
            #print("00000000000000000000key", key, "--action", action)
            return inf

        if key in tools and state[key] > 2:
            return inf

    return modifier

def search(graph, state, is_goal, limit, heuristic, rule, Crafting, consumed, required, goals):

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

    #cost = 0
    frontier.append((0,"Start",curr_state))
    came_from[curr_state] = ("start", None)
    cost_so_far[curr_state] = 0

    while frontier and time() - start_time < limit:
        exploring = heappop(frontier)
        #print("explore",exploring)
        if is_goal(exploring[2]):

            prev_state = came_from[exploring[2]]
            came_from[exploring[2]] = ("Goal", exploring[2])
            path = path_find(prev_state, prev_state,path,came_from,0)
            path = [(exploring[2],exploring[1])] + path
            path.reverse()
            print(time() - start_time, 'seconds.')
            return path

        for next in graph(exploring[2]):
            name, effect, cost = next
            new_cost = cost_so_far[exploring[2]] + cost
            if effect not in cost_so_far.keys() or new_cost < cost_so_far[effect]:
                cost_so_far[effect] = new_cost
                priority = new_cost + heuristic(effect, name, rule, Crafting, consumed, required, goals)
                #if priority < 1000:
                    #print("name", name, "cost", new_cost, "effect", effect, "priority", priority)
                    #cost = new_cost
                heappush(frontier,(priority,name,effect))
                came_from[effect] = (exploring[1],exploring[2])
        #print("------------------------")

    # Failed to find a path
    print(time() - start_time, 'seconds.')
    #print("cost",cost)
    print("Failed to find a path from", state, 'within time limit.')
    return None


def path_find(starting_state, prev_state, path, came_from,count):
    if count <= len(came_from):
        path.append((prev_state[1], prev_state[0]))
        if prev_state[1] not in came_from.keys() or starting_state is prev_state[1]:
            return path
        count += 1
        path_find(starting_state, came_from[prev_state[1]],path,came_from,count)
    return path


def required_for_goal(Crafting, action, required, consumed):
    #the first action will be the one that makes the goal  
    if "Requires" in Crafting["Recipes"][action]: #if the action  requires something
        for required_item in Crafting["Recipes"][action]["Requires"]: # for item that (the action) requires
            #print ("required item",required_item)
            for product_action in Crafting["Recipes"]:
                if required_item in Crafting["Recipes"][product_action]["Produces"]:
                    #print("product",required_item)
                    if required_item not in required:
                        required.append(required_item) # put it into the requires list
                        # check what that items creation requires
                        required2, consumed2 = required_for_goal(Crafting,product_action,required,consumed)
                        for new_items in required2:
                            if new_items not in required:
                                required.append(new_items)
    # exact same thing for consumes
    if "Consumes" in Crafting["Recipes"][action]:
        for consumed_item in Crafting["Recipes"][action]["Consumes"]:
            #print ("consumed item",consumed_item)
            for product_action in Crafting["Recipes"]:
                if consumed_item in Crafting["Recipes"][product_action]["Produces"]:
                    #print("product",consumed_item)
                    if consumed_item not in consumed:
                        consumed.append(consumed_item)
                        required2, consumed2 = required_for_goal(Crafting,product_action,required,consumed)
                        for new_items in consumed2:
                            if new_items not in consumed:
                                consumed.append(new_items)
    return required, consumed

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
    print('Goal:',Crafting['Goal'])
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

    # Traceback the actions leading to the goal
    required = []
    consumed = []
    goals = []
    best_action = None
    smallest = 999
    for rule in Crafting["Recipes"]:
        for goal in Crafting["Goal"]:
            if goal in Crafting["Recipes"][rule]["Produces"]:
                if "Requires" in Crafting["Recipes"][rule]:
                    req = len(Crafting["Recipes"][rule]["Requires"])
                else:
                    req = 0
                if "Consumes" in Crafting["Recipes"][rule]:
                    con = len(Crafting["Recipes"][rule]["Consumes"])
                else:
                    con = 0
                if req + con < smallest: # finds the action with the smallest list of required/consumed items
                # this could be modified to consider that wooden pickaxe is an easier item to get than iron_pixaxe and
                # prefer the rule that uses wooden_pickaxe
                    best_action = rule
                    smallest = req + con
    #print("best_action",best_action)
    required, consumed = required_for_goal(Crafting, best_action, required, consumed)
    for item in Crafting["Goal"]:
        goals.append(item)
        if "Requires" in Crafting["Recipes"][best_action]: #if the action  requires something
            for required_item in Crafting["Recipes"][best_action]["Requires"]: # for item that (the action) requires
                goals.append(required_item)
        if "Consumes" in Crafting["Recipes"][best_action]: #if the action  requires something
            for consumed_item in Crafting["Recipes"][best_action]["Consumes"]: # for item that (the action) requires
                goals.append(consumed_item)

    print("required",required)
    print("consumed",consumed)
    print("goals",goals)
    # Search for a solution
    resulting_plan = search(graph, state, is_goal, 300, heuristic, req_rule, Crafting, consumed, required, goals)
    # resulting_plan = False
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
