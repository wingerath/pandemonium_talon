from talon import actions, cron, Context, Module, ctrl
from typing import Callable, Tuple, TypedDict
from dataclasses import dataclass, asdict
from talon.screen import Screen, main_screen
import time

@dataclass
class DirectionActions:
    cancel_type: str
    up: Callable[[float], None]
    left: Callable[[float], None]
    right: Callable[[float], None]
    down: Callable[[float], None]
    forward: Callable[[float], None]
    backward: Callable[[float], None]

def noop_key(ts: float):
    pass

def print_key(key: str):
    return lambda ts: print("Pressed key " + key)

def action_key(action):
    return lambda ts: action()
    
def keypress_key(key):
    return lambda ts: actions.key(key)

def mouse_move_action(x_offset: float, y_offset: float):
    return lambda ts, x_offset=x_offset, y_offset=y_offset: actions.user.mouse_relative_move(x_offset, y_offset)


direction_exclusion_mono = "mono" # Cancels all directions when a new direction is set
direction_exclusion_diagonal = "opposite" # Cancels only the opposite direciton when a new directoin is set
class HummingBird:
    
    job = None
    current_directions = []
    directions = None
    
    def __init__(self):
        self.directions = DirectionActions(
        	"mono",
            keypress_key("up"),
            keypress_key("left"),
            keypress_key("right"),
            keypress_key("down"),
            action_key(actions.core.repeat),
            action_key(actions.edit.undo)
        )
        
    def set_direction_actions(self, da: DirectionActions):
        self.directions = da
        
    def start_continuous_job(self):
        self.end_continuous_job()	
        self.job = cron.interval("16ms", self.tick_directions)

    def tick_directions(self):
        ts = time.time()
        for direction in self.current_directions:
            if direction == "up":
	            self.directions.up(ts)
            elif direction == "left":
                self.directions.left(ts)
            elif direction == "right":
                self.directions.right(ts)
            elif direction == "down":
                self.directions.down(ts)

    def end_continuous_job(self):
        cron.cancel(self.job)
        self.job = None
		
    def set_direction(self, new_direction):
        if (self.directions.cancel_type == "mono"):
            self.clear_directions()
        elif (self.directions.cancel_type == "opposite"):
            if self.current_directions == "up" and "down" in self.current_directions:
                self.current_directions.remove("down")
            elif self.current_directions == "down" and "up" in self.current_directions:
                self.current_directions.remove("up")
            elif self.current_directions == "left" and "right" in self.current_directions:
                self.current_directions.remove("right")
            elif self.current_directions == "right" and "left" in self.current_directions:
                self.current_directions.remove("left")
        
        if new_direction not in self.current_directions:
            self.current_directions.append(new_direction)

    def clear_directions(self):
        self.current_directions = []

    def up(self, ts: float, set_directions=True):
        if set_directions:
            self.set_direction("up")
        
        if not self.job:
            self.directions.up(ts)
    
    def left(self, ts: float, set_directions=True):
        if set_directions:
            self.set_direction("left")
        if not self.job:
            self.directions.left(ts)
    
    def right(self, ts: float, set_directions=True):
        if set_directions:
            self.set_direction("right")
            
        if not self.job:
            self.directions.right(ts)
        
    def down(self, ts: float, set_directions=True):
        if set_directions:
            self.set_direction("down")
    
        if not self.job:
            self.directions.down(ts)
    
    def forward(self, ts: float):
        if len(self.current_directions) > 0:
            for direction in self.current_directions:
                if direction == "up":
                    self.up(ts, False)
                elif direction == "left":
                    self.left(ts, False)
                elif direction == "right":
                    self.right(ts, False)
                elif direction == "down":
                    self.down(ts, False)
        else:
            self.directions.forward(ts)
            
    def backward(self, ts: float):
        if len(self.current_directions) > 0:
            for direction in self.current_directions:
                if direction == "up":
                    self.down(ts, False)
                elif direction == "left":
                    self.right(ts, False)
                elif direction == "right":
                    self.left(ts, False)
                elif direction == "down":
                    self.up(ts, False)
        else:
            self.directions.backward(ts)
        
hb = HummingBird()

hummingbird_directions = {
    "arrows": DirectionActions(
    	"mono",
        keypress_key("up"),
        keypress_key("left"),
        keypress_key("right"),
        keypress_key("down"),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo)
    ),
	"arrows_word": DirectionActions(
	    "mono",
        keypress_key("up"),
        action_key(actions.edit.word_left),
        action_key(actions.edit.word_right),
        keypress_key("down"),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo)
    ),
	"select": DirectionActions(
	    "mono",
        action_key(actions.edit.extend_up),
        action_key(actions.edit.extend_left),
        action_key(actions.edit.extend_right),
        action_key(actions.edit.extend_down),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo)
    ),
	"select_word": DirectionActions(
		"mono",
        action_key(actions.edit.extend_up),
        action_key(actions.edit.extend_word_left),
        action_key(actions.edit.extend_word_right),
        action_key(actions.edit.extend_down),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo)
    ),    
    "cursor": DirectionActions(
        "mono",
        mouse_move_action(0, -6),
        mouse_move_action(-6, 0),
        mouse_move_action(6, 0),
        mouse_move_action(0, 6),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo)
    ),
    "jira": DirectionActions(
    	"mono",    	
        keypress_key("k"),
        keypress_key("p"),
        keypress_key("n"),
        keypress_key("j"),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo)
    )
}

ctx = Context()
mod = Module()
mod.tag("humming_bird", desc="Tag whether or not humming bird should be used")
mod.tag("humming_bird_overrides", desc="Tag to override knausj commands to interlace humming bird overrides in them")

@mod.action_class
class Actions:
                
    def hummingbird_up(ts: float):
        """Activate the action related to the up direction of the humming bird"""
        global hb
        hb.up(ts)
                
    def hummingbird_left(ts: float):
        """Activate the action related to the left direction of the humming bird"""
        global hb
        hb.left(ts)
        
    def hummingbird_right(ts: float):
        """Activate the action related to the right direction of the humming bird"""
        global hb
        hb.right(ts)
        
    def hummingbird_down(ts: float):
        """Activate the action related to the down direction of the humming bird"""
        global hb
        hb.down(ts)
        
    def hummingbird_forward(ts: float):
        """Repeats the current directions, or repeats the last command"""
        global hb
        hb.forward(ts)
        
    def hummingbird_backward(ts: float):
        """Reverses the current directions, or undoes the last edit"""
        global hb
        hb.backward(ts)
        
    def hummingbird_continuous():
        """Starts a continuous job that triggers the directions at 60Hz"""
        global hb
        hb.start_continuous_job()
        
    def hummingbird_stop():
        """Ends the continuous job"""
        global hb
        hb.end_continuous_job()
        
    def hummingbird_clear():
        """Clears all current directions"""
        global hb
        hb.clear_directions()
        
    def hummingbird_set(type: str):
        """Sets the hummingbird control type"""
        global hb, hummingbird_directions
        hb.set_direction_actions(hummingbird_directions["arrows"] if type not in hummingbird_directions else hummingbird_directions[type])
        
    def mouse_relative_move(x_offset: float, y_offset: float):
        """Moves the mouse in the given direction relative to the current cursor position"""
        x, y = ctrl.mouse_pos()
        ctrl.mouse_move(x + x_offset, y + y_offset) 