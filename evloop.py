# coding: utf-8
import time
import logging
_LOGGER = logging.getLogger("[ELOOP]")

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
            _LOGGER.debug("(@%.2f) executing event (%s) %s - time %.2f" % (_eventloop.time(), self.id, self.desc, self.t))

        if self.callback is not None:
            self.callback(*self.parameters)
            
        if self.repeat is not None:
            self.reprogram(now + self.repeat)

    def next_sched(self, now):
        if self.repeat is None:
            # It only happens one, when t... if now > t then there will not be any other occurrence
            if now > self.t:
                return None
            return self.t
        else:
            return self.t
            #last_called = self.last_called
            #if last_called is None: last_called = 0
            #return last_called + self.repeat + self.t
        
    def reprogram(self, t = None):
        self.t = t

    def __str__(self):
        return "(EVENT %d@%.2f) %s" % (self.id, self.t, self.desc)

class Event(Event_Periodical):
    def __init__(self, t, callback = None, description = None, parameters = [], priority = Event_Periodical.PRIO_NORMAL, mute = False):
        Event_Periodical.__init__(self, t, None, callback, description, parameters, priority, mute)
        
    #def next_sched(self):
    #    last_called = self.last_called        
    #    if last_called is None:
    #        last_called = 0
    #    
    #    last_called = max(self.start, last_called)
    #    return last_called + self.t
    #
    #def call(self):
    #    global _eventloop
    #    self.last_called = _eventloop.time()
    #    Event.call(self)

class EventLoop():
    def __init__(self):
        self.events = {}
        self.t = 0
        
    def set_time(self, t):
        self.t = t
        
    def time(self):
        return self.t
    
    def event_count(self):
        return len(self.events)
    
    def add_event(self, event):
        if event.id in self.events:
            raise Exception("An event with id %s already exists" % event.id)
        self.events[event.id] = event
        return event
    
    def cancel_event(self, event_id):
        if event_id in self.events:
            del self.events[event_id]
            return True
        return False
    
    def _sort_events(self, now):
        forgotten_events = []
        eventqueue = []
        for event_id, event in self.events.items():
            next_sched = event.next_sched(now)
            if next_sched is None:
                forgotten_events.append(event_id)
                
            #
            eventqueue.append((event_id, next_sched, event.priority))
        print sorted(eventqueue, key = lambda x: (x[1], x[2]))
                
        # Clean the events that are not being executed anymore
        for event_id in forgotten_events:
            self.cancel_event(event_id)
    
    def loop(self):
        print str(self)
        self._sort_events(self.t)
        pass
    
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
            
if __name__ == '__main__':
    ev = EventLoop()
    ev.set_time(1)
    ev.add_event(Event_Periodical(0, 1, description = "evento periodico cada 1s"))
    ev.add_event(Event(2, "evento en el segundo 2"))
    ev.add_event(Event(2, "evento repetido en el segundo 2", priority = Event.PRIO_HIGH))
    ev.loop()
    