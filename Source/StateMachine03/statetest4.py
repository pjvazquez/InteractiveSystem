from transitions import Machine
import random

class Matter(object):
    heat = False
    attempts = 0
    def count_attempts(self): self.attempts += 1
    def is_really_hot(self): return self.heat
    def is_cold(self): return self.heat
    def heat_up(self): self.heat = random.random() > 0.5
    def heat_down(self): self.heat = random.random() < 0.5
    def stats(self): print('It took you %i attempts to melt the lump!' %self.attempts)

states=['solid', 'liquid', 'gas', 'plasma']

transitions = [
    { 
        'trigger': 'melt', 
        'source': 'solid', 
        'dest': 'liquid', 
        'prepare': ['heat_up', 'count_attempts'], 
        'conditions': 'is_really_hot', 
        'after': 'stats'
        },
    { 
        'trigger': 'melt', 
        'source': 'liquid', 
        'dest': 'gas', 
        'prepare': ['heat_up', 'count_attempts'], 
        'conditions': 'is_really_hot', 
        'after': 'stats'
        },
    { 
        'trigger': 'melt', 
        'source': 'gas', 
        'dest': 'plasma', 
        'prepare': ['heat_up', 'count_attempts'], 
        'conditions': 'is_really_hot', 
        'after': 'stats'
        },
    { 
        'trigger': 'melt', 
        'source': 'plasma', 
        'dest': 'solid', 
        'prepare': ['heat_down', 'count_attempts'], 
        'conditions': 'is_cold', 
        'after': 'stats'
        },


]

lump = Matter()
machine = Machine(lump, states, transitions=transitions, initial='solid')
for i in range(0,50):
    print("iteration: {}".format(i) , "\tState: ", lump.state, "\theat: ", lump.heat)
    lump.melt()
