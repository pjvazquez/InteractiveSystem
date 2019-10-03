from statemachine import StateMachine, State

class TrafficLightMachine(StateMachine):
    "A traffic light machine"
    green = State('Green', initial=True)
    yellow = State('Yellow')
    red = State('Red')

    slowdown = green.to(yellow)
    stop = yellow.to(red)
    go = red.to(green)

    def on_slowdown(self):
        print('Calma, lá!')

    def on_stop(self):
        print('Parou.')

    def on_go(self):
        print('Valendo!')

class TrafficLightMachine2(StateMachine):
    "\n\nA NEW CYCLE traffic light machine"
    green = State('Green', initial=True)
    yellow = State('Yellow')
    red = State('Red')

    cycle = green.to(yellow) | yellow.to(red) | red.to(green)

    def on_enter_green(self):
        print('Valendo!')

    def on_enter_yellow(self):
        print('Calma, lá!')

    def on_enter_red(self):
        print('Parou.')


if __name__ == "__main__":
    stm = TrafficLightMachine()
    stm.slowdown()
    print( stm.current_state )
    stm.stop()
    print(stm.current_state)
    stm.go()

    stm2 = TrafficLightMachine2()
    stm2.cycle()
    print( stm.current_state )
    stm2.cycle()
    print( stm.current_state )
    stm2.cycle()
    print( stm.current_state )



