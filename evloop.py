# coding: utf-8
import cpyutils.log
import time
import logging
import math
_LOGGER = cpyutils.log.Log("ELOOP")
# logging.getLogger("[ELOOP]")

class Event_Periodical:
    _id = -1
    
    @staticmethod
    def get_event_id():
        Event._id = Event._id + 1
        return Event._id

    PRIO_LOWER = 100
    PRIO_LOW = 50
    PRIO_NORMAL = 0
    PRIO_HIGH = -50
    PRIO_HIGHER = -100
    
    def __init__(self, t, repeat, callback = None, description = None, parameters = [], priority = PRIO_NORMAL, mute = False):
        self.id = Event.get_event_id()
        self.t = t
        if description is None:
            description = "event %s at %s" % (self.id, self.t)
        self.description = description
        self.callback = callback
        self.parameters = parameters
        self.priority = priority
        self.mute = mute
        self.repeat = repeat
        self.lastcall = None

    def call(self, now):
        self.lastcall = now
        
        if not self.mute:
            _LOGGER.debug("(@%.2f) executing event (%s) %s - time %.2f" % (now, self.id, self.description, self.t))

        if self.callback is not None:
            self.callback(*self.parameters)
            
        if self.repeat is not None:
            self.reprogram(now + self.repeat)

    def next_sched(self, now):
        if self.repeat is None:
            if self.lastcall is not None:
                # If the event was called, the there is not any call more
                return None
            return self.t
        else:
            return self.t
        
    def reprogram(self, t = None):
        self.t = t

    def __str__(self):
        return "(EVENT %d@%.2f) %s" % (self.id, self.t, self.description)

class Event(Event_Periodical):
    def __init__(self, t, callback = None, description = None, parameters = [], priority = Event_Periodical.PRIO_NORMAL, mute = False):
        Event_Periodical.__init__(self, t, None, callback, description, parameters, priority, mute)
        
class EventLoop():
    def __init__(self):
        self.events = {}
        self.t = 0
        self._extra_periodical_events = 5
        self._current_extra_periodical_events = 0
        self._walltime = 1000
        
    #def set_time(self, t):
    #    self.t = t
        
    def time(self):
        return self.t
    
    def event_count(self):
        return len(self.events)
    
    def add_event(self, event):
        if event.id in self.events:
            raise Exception("An event with id %s already exists" % event.id)

        if event.t <= self.t:
            if event.repeat is None:
                # We do not let to include past events (if they are )
                return None
            else:
                next_program = event.t + math.ceil((self.t - event.t) / event.repeat)
                print "next program:", next_program
                event.reprogram(next_program)
            
        self.events[event.id] = event
        return event
    
    def cancel_event(self, event_id):
        if event_id in self.events:
            del self.events[event_id]
            return True
        return False
    
    def _sort_events(self, now):
        forgotten_events = []
        nexteventsqueue = []
        periodical_events = 0
        for event_id, event in self.events.items():
            next_sched = event.next_sched(now)
            if next_sched is None:
                forgotten_events.append(event_id)
            else:
                non_periodical_priority = 0
                if event.repeat is not None:
                    periodical_events += 1
                    non_periodical_priority = 1
                    
                nexteventsqueue.append((event_id, next_sched, event.priority, non_periodical_priority))
                
        nexteventsqueue.sort(key = lambda x: (x[1], x[3], x[2]))
                
        # Clean the events that are not being executed anymore
        for event_id in forgotten_events:
            self.cancel_event(event_id)
            
        return nexteventsqueue, periodical_events
    
    def loop(self):
        print str(self)
        while True:
            now = self.t
            if now > self._walltime:
                _LOGGER.info("walltime %.2f achieved" % self._walltime)
                break
            
            next_events, periodical_events = self._sort_events(now)
            
            if len(next_events) > 0:
                (ev_id, program_t,_ , _) = next_events[0]
                
                # will execute the first event whose time has just passed
                if program_t <= now:
                    self.events[ev_id].call(now)
                    
                    # The maximum of periodical events
                    if periodical_events == len(next_events):
                        self._current_extra_periodical_events += 1
                    else:
                        self._current_extra_periodical_events = 0
                    if self._current_extra_periodical_events >= self._extra_periodical_events:
                        _LOGGER.info("extra periodical events achieved")
                        break
                else:
                    self.t = program_t                    
            else:
                _LOGGER.info("no more events")
                break
                        
    def __str__(self):
        retval = "Current Time: %f, Pending Events: %d" % (self.time(), len(self.events))
        if len(self.events) > 0:
            # retval = "%s, Next Event in %.2f time units\nEvent List:" % (retval, self._events[0].t - self._t)
            for ev_id, ev in self.events.items():
                when = ev.next_sched(self.t)
                if when is not None:
                    when = "%.2f" % when
                else:
                    when = "None"
                retval = "%s\n%s" % (retval, "+%s [%s]" % (when, ev.description))
        return retval

ev = EventLoop()
    
def create_new_event():
    ev.add_event(Event(10, callback = create_new_event, description = "evento en el segundo 10"))
            
if __name__ == '__main__':
    # ev.set_time(1)
    ev.add_event(Event_Periodical(0, 1, description = "evento periodico cada 1s"))
    ev.add_event(Event_Periodical(5, 3, description = "evento periodico que empieza en 5 cada 2s"))
    ev.add_event(Event(2, description = "evento en el segundo 2"))
    ev.add_event(Event(2, callback = create_new_event, description = "evento prioritario en el segundo 2", priority = Event.PRIO_HIGH))
    ev.loop()
    