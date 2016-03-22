import random
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator

class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        self.q_values = {}
        self.penalties = []
        self.penalty = 0
    def reset(self, destination=None):
        self.penalties.append(self.penalty)
        self.penalty = 0
        self.planner.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required

    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        inputs = self.env.sense(self)
        deadline = self.env.get_deadline(self)

        # Update state
        curr_state = (self.next_waypoint, inputs['light'], inputs['oncoming'], inputs['left'], inputs['right'])
        self.state = curr_state

        old_q, action = self.choose_best_action(self.state)

        # Execute action and get reward
        reward = self.env.act(self, action)

        # calculate penalties
        if reward < 0:
            self.penalty += 1

        # Sense the environment, and obtain new state
        new_inputs = self.env.sense(self)
        new_state = (self.next_waypoint, new_inputs['light'], new_inputs['oncoming'], new_inputs['left'], new_inputs['right'])

        # Update the Q table
        new_q_val = self.calculate_q_val(new_state, old_q, reward)

        self.q_values[(curr_state, action)] = new_q_val

        print "LearningAgent.update(): deadline = {}, inputs = {}, action = {}, reward = {}, waypoint = {}".format(deadline, inputs, action, reward, self.next_waypoint)  # [debug]

    def get_max_q(self, new_state):
        q = [self.get_q_value(new_state, action) for action in Environment.valid_actions]
        max_q = max(q)
        return max_q, q

    def choose_best_action(self, state):
        max_q, q_lst = self.get_max_q(state)

        # If there are multiple max_q, pick a random one
        if q_lst.count(max_q) > 1:
            max_q_lst = [i for i in range(len(Environment.valid_actions)) if q_lst[i] == max_q]
            idx = random.choice(max_q_lst)
        else:
            idx = q_lst.index(max_q)

        action = Environment.valid_actions[idx]

        return max_q, action

    def get_q_value(self, state, action):
        return self.q_values.get((state, action), 1.0)

    def calculate_q_val(self, new_state, old_q, reward):
        # learning rate
        alpha = 0.5
        # discount factor
        gamma = 0.25
        # learned value
        learned_val = reward + (gamma * self.get_max_q(new_state)[0] - old_q)

        new_q = old_q + alpha * learned_val

        return new_q


def run():
    """Run the agent for a finite number of trials."""

    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=True)  # set agent to track

    # Now simulate it
    sim = Simulator(e, update_delay=0)  # reduce update_delay to speed up simulation
    sim.run(n_trials=100)  # press Esc or close pygame window to quit
    print(a.penalties)

if __name__ == '__main__':
    run()
