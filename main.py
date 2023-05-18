from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
import time

from recorder import Recorder

class Mp3Recorder(BoxLayout):
    
    def __init__(self, **kwargs):
        super(Mp3Recorder, self).__init__(**kwargs)
        #
        self.mp3_filename = ''
        self.state = 'ready'
        self.info = ''
        self.time_started = False
        self.recorder = Recorder()
        self.recorder.ask_permissions()

    # ----------------- timer   ------------------------ #
    def timer(self, *args):
        self.ids['time_label'].text = time.asctime()

    def start_time(self):
        Clock.schedule_interval(self.timer, 1)
        self.time_started = True

    # ======================
    #       record 
    # ======================
    def record(self):
        self.state, self.mp3_filename = self.recorder.record(self.state)
        self.update_labels()

    # ======================
    #       email 
    # ======================
    def email(self):
        if self.state != 'ready':
            self.info = 'Recording in progress.'
        else:
            self.info = self.recorder.email(self.mp3_filename)

        self.update_labels()

    # ======================
    #       exit 
    # ======================
    def exit(self):
        self.recorder.exit()

    # ======================
    #       update_labels
    # ======================
    def update_labels(self):
       
        from os.path import basename, exists
        basefn = 'none'
        if exists(self.mp3_filename):
            basefn = basename(self.mp3_filename)
            
        self.ids['info_label'].text = f'''
        Info : {self.info}\n
        Audio: {self.state}\n
        Recorded file :: {basefn}
        '''

        if self.state == 'ready':
            self.ids['record_button'].text = 'Start Recording'
            self.ids['email_button'].text = f'Email {basefn}'

        if self.state == 'recording':
            self.ids['record_button'].text = 'Stop Recording'
            self.ids['email_button'].text = 'Email'
            
        if not self.time_started:
            self.start_time()

class Mp3RecorderApp(App):
    def build(self):
        return Mp3Recorder()

if __name__ == '__main__':
    Mp3RecorderApp().run()
