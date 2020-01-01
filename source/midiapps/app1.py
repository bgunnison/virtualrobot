"""
MIDI effects app
"""
import queue
import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

from midi import *

def fatal_exit(msg):
    print(msg)
    exit(0)

class Effect:
    def __init__(self):
        pass

    def run(self):
        pass # override

class EchoEffect(Effect):
    def __init__(self, note_manager):
        self.note_manager = note_manager
        self.delay_ticks = 24
        self.echoes = 3
        self.new_echoes = 3
        self.end_velocity = 10

    def __str__(self):
        return f'Echo effect - Echoes: {self.echoes}, Delay: {self.delay_ticks}'

    def control_echoes(self, control):
        """
        All controls are 0 - 127 per CC
        """
        control += 1
        control /= 4
        self.new_echoes = int(control)
        log.info(f"echoes: {self.new_echoes}")

    def control_delay_tick(self, control):
        """
        All controls are 0 - 127 per CC
        """
        self.delay_ticks = control
        log.info(f"delay ticks: {self.delay_ticks}")

    def run(self, tick, midiout, message):
        """
        note events are added to note manager at future times
        """
        midiout.send_message(message)  # send original note event

        note = MidiNoteMessage(message)
        if note.velocity <= self.end_velocity:
            return

        # if we change number of echoes in the middle of echoing notes
        # we could miss note off events. 
        if self.new_echoes != self.echoes:
            if self.note_manager.empty():
                self.echoes = self.new_echoes


        # divide the velocity range to get to min from original v
        ov = note.velocity
        dv = (ov - self.end_velocity)/float(self.echoes)
        #log.info(f"tick: {tick}, dv: {dv}")
        # subsequent echos 
        echo_num = 1
        while True:
            ntick = tick + (echo_num * self.delay_ticks)
            note.velocity = int(ov - (echo_num * dv))
            if note.velocity < self.end_velocity:
                break
            self.note_manager.add(ntick, note.get_message())
            echo_num += 1
            if echo_num > self.echoes:
                break

class ChordInfo:
    """
    Info about chords
    """
    def __init__(self):
        self.info = {  'major':[4,7],
                        'minor':[3,7],
                        'diminished':[3,6],
                        'major seventh':[4,7,11],
                        'minor seventh':[3,7,10],
                        'dominant seventh':[4,7,10],
                        'suspended2':[2,7],
                        'suspended4':[5,7],
                        'augmented':[4,8]
                        }

    def get_intervals(self, name):
        return self.info.get(name)

    def get_names(self):
        return list(self.info.keys())



class Chord:
    """
    We can iterate over the midi note produced by the chord type and width
    """
    def __init__(self, tonic=60, name='major', width=3):
        self.midi_notes = [] # a list of midi chord notes sans tonic
        width -= 1 # only generate the other chord notes
        chords = ChordInfo()
        intervals = chords.get_intervals(name)
        if intervals is None:
            log.critical()
            raise Exception(f'Unrecognized chord name: {name}')

        iindex = 0
        for i in range(width):
            self.midi_notes.append(tonic + intervals[iindex])
            iindex += 1

            if len(self.midi_notes) == width:
                break

            if iindex == len(intervals):
                tonic += 12
                self.midi_notes.append(tonic)   # octave up
                iindex = 0

            if len(self.midi_notes) == width:
                break


    def notes(self):
        return self.midi_notes



class ChordEffect(Effect):
    def __init__(self):
        self.chord_name = 'major'   # default a 3 note major chord 
        self.new_chord_name = self.chord_name
        self.chord_width = 3
        self.new_chord_width = self.chord_width

    def __str__(self):
        return f'Chord effect - Type: {self.chord_name}, Notes: {self.chord_width}'

    def control_chord_name(self, control):
        """
        All controls are 0 - 127 per CC
        """
        names = ChordInfo().get_names()
        n = len(names)
        s = int(control/n)
        if s > n - 1:
            s = n - 1

        self.new_chord_name = names[s]
        log.info(f"Chord: {self.new_chord_name}")

    def control_chord_width(self, control):
        """
        All controls are 0 - 127 per CC
        """
        # a polyphony issue, limit to 12
        width = control/10
        if width < 1:
            width = 1

        self.new_chord_width = int(width)
        log.info(f"Chord width: {self.new_chord_width}")

    def run(self, tick, midiout, message):
        """
        generate the added notes for the chord
        """
        if midiout.get_notes_pending() == 0:    # if we change in the middle of a chord playing we get stuck notes
            if self.chord_name != self.new_chord_name:
                self.chord_name = self.new_chord_name
            if self.chord_width != self.new_chord_width:
                self.chord_width = self.new_chord_width


        midiout.send_message(message)  # send original note event

        onote = MidiNoteMessage(message)
        chord = Chord(tonic=onote.note, name=self.chord_name, width=self.chord_width)

        for note in chord.notes():
            onote.note = note
            midiout.send_message(onote.get_message())

        
        

        


class NoteManager:
    """
    A simple priority queue of note events
    These are added at clock tick priority and examined 
    if it is their time to be sent out
    """

    def __init__(self, app):
        self.midiout = app.midiout
        self.note_events = queue.PriorityQueue()

    def run(self, tick):
        """
        See if any events are ready to play
        """
        if self.note_events.empty():
            return

        # no peek ;(
        event = self.note_events.get()

        if tick >= event[0]:
            self.midiout.send_message(event[1])
        else:
            self.note_events.put(event)

    def add(self, tick, message):
        """
        Add a message to the priority queue
        """
        self.note_events.put((tick,message))
        #log.info(f"Add: {message}, {tick}")

    def empty(self):
        return self.note_events.empty()

class ZonkerMidiEffect:

    def __init__(self, inport, outport, clockport=None, clock_dir='internal'):
        self.internal_clock_bpm = 60
        self.open_ports(inport, outport, clockport, clock_dir)
        self.note_manager = NoteManager(self)

        # set up desired effect
        self.effect = None
        self.effect_controls = None
        # button CCs are mapped to which effect is well, in effect...
        self.effects = {
                        48:self.set_effect_echo,
                        49:self.set_effect_chord
                       }

    def set_effect_echo(self):
        self.effect = EchoEffect(self.note_manager)
        # VI25 Alesis controller CC knobs start with 21
        self.effect_controls = {    21:[self.effect.control_echoes],
                                    22:[self.effect.control_delay_tick]
                                }  # a dict keyed with CC numbers and a list of control functions mapped to that CC

    def set_effect_chord(self):
        self.effect = ChordEffect()
        # VI25 Alesis controller CC knobs start with 21
        self.effect_controls = {    21:[self.effect.control_chord_name],
                                    22:[self.effect.control_chord_width]
                                }  # a dict keyed with CC numbers and a list of control functions mapped to that CC


    def open_ports(self, inport, outport, clockport, clock_dir):
        """
        open designated inport and outport
        clock is incoming currently
        """
        try:
            self.midiin = MidiIn(inport) # 'VI25 2')
        except:
            fatal_exit(f'Cannot open midi input: {inport}')

        try:
            self.midiout = MidiOut(outport) # 'lma')
        except:
            fatal_exit(f'Cannot open midi output: {outport}')

        self.midiout.panic()

        if clockport is not None and clock_dir is 'external':
            try:
                self.clock_source = MidiIn(target=clockport,q_size_limit=4096, ignore_clock=False) # 'lmb'
            except:
                fatal_exit(f'Cannot open clock midi input: {clockport}')

        if clock_dir is 'internal':
            # we generate our own clock
            # midiout=self.midiout sending clock out same port as notes does not work. 
            clock_midiout = None
            if clockport is not None:
                try:
                    clock_midiout = MidiOut(target=clockport) # 'lmb'
                except:
                    fatal_exit(f'cannot open clock midi output: {clockport}')

            self.clock_source = MidiInternalClock(midiout=clock_midiout, bpm=self.internal_clock_bpm)

        self.clock_source.register_clock_callback(callback=self.clock_callback)   
        self.midiin.register_note_callback(self.note_callback, self.clock_source)
        self.midiin.register_control_callback(callback=self.control_callback)


    def panic(self):
        self.midiout.panic()


    def run(self):
         self.clock_source.run()
         self.midiin.run()
         log.info('Running')
         while True:
             time.sleep(0.2)

    def apply_effects(self, tick, message):
        """
        A list of effect objects act on the incoming note
        and may add note events to the note manager to play in the future
        """
        if self.effect is None:
            self.midiout.send_message(message)  # send original note event
            return

        self.effect.run(tick, self.midiout, message)


    def note_callback(self, message, clock_source):
        """
        invoked by our input when a note is on or off
        """ 
        tick = clock_source.get_tick()
        #log.info(f"Note callback: {message}, {tick}")
        #self.midiout.send_message(message)  # always echo the original note event
        self.apply_effects(tick, message)         # adds note events for the future
        self.note_manager.run(tick)        


    def clock_callback(self, tick, data):
        """
        called at midi clock intervals or at 60 bpm every 42 msec - 24 times per quarter note
        here we run the note manager and it sends or stops notes as queued
        This runs quite fast so no delays...
        """
        #log.info(f"Clock callback: {tick}")
        self.note_manager.run(tick)
    
    def control_callback(self, cc, control):
        """
        A cc button switches effects or
        An effect has controllable parms via CC knobs
        The app maps the CC to the parm(s). This callback has the CC number and control  (0 - 127)
        We use the CC to get the list of effect parm function and call them.
        """
        if self.effects is not None:
            set_effect_func = self.effects.get(cc)
            if set_effect_func is not None:
                if control == 0:
                    self.effect = None
                    self.controls = None
                    return

                if control == 127:
                    set_effect_func()
                    log.info(f"Current effect: {self.effect}")

                return


        if self.effect_controls is None:
            return

        control_funcs = self.effect_controls.get(cc)
        if control_funcs is None:
            return

        for func in control_funcs:
            func(control)




if __name__ == '__main__':
    app = ZonkerMidiEffect(inport='VI25 2', outport='lma', clockport='lmb', clock_dir='internal')
    app.run()
    app.panic()
