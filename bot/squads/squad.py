"""
任何一个单位都需要在一个squad种
"""

from sc2.unit import Unit


class Squad():
    def __init__(self) -> None:
        self.is_done = False

    def on_submit(self):
        pass
    
    def step(self):
        pass

    def on_building_construction_complete(self, unit: Unit):
        pass

    def debug_string(self) -> str:
        return "Squad"
