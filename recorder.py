from jnius import autoclass
from kivy import Logger, platform
from datetime import datetime
import os

from sharedstorage import SharedStorage
#
PythonActivity = None
if platform == "android":
    from android import mActivity, autoclass, api_version
    from android.permissions import request_permissions
    PythonActivity = autoclass("org.kivy.android.PythonActivity").mActivity
    Context = autoclass('android.content.Context')

# =========================================================== #
#                   class Recorder                         #
# =========================================================== #

class Recorder():

    required_permissions = [
            "android.permission.WRITE_EXTERNAL_STORAGE",
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.RECORD_AUDIO",
        ]
    
    mp3Filename = ''
    
    def __init__(self, **kwargs):
        super(Recorder, self).__init__(**kwargs)

        if not platform == "android":
            return
        
        self.MediaRecorder = autoclass('android.media.MediaRecorder')
        self.AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
        self.OutputFormat = autoclass('android.media.MediaRecorder$OutputFormat')
        self.AudioEncoder = autoclass('android.media.MediaRecorder$AudioEncoder')
        #
        self.mp3_filename = ''
        self.config = dict()
        self.EMAIL_USERNAME = ''
        self.EMAIL_PASSWORD = ''
        self.EMAIL_SENDER = ''
        self.EMAIL_RECEIVER = ''
        self.SERVER_HOST = ''
        self.SERVER_PORT = 0
        self.configInit()
        
    # ----------------- configInit ------------------------ #        
    def configInit(self):
        csvFn = 'Mp3Recorder.csv'
        with open(csvFn) as f:
            content_list = f.readlines()
        f.close()
        
        self.config.clear()
        
        for item in content_list:
            itemList = []
            try:
                itemList = item.replace(' ','').split(',')
            except ValueError:
                continue
            if len(itemList) > 1 and itemList[0][0] != '#':
                # cleanup NL etc
                for i,s in enumerate(itemList):
                    itemList[i] = s.strip()
                k = itemList[0].strip()
                v = itemList[1:]
                self.config[k] = v
                print(f'k[{k}], v[{v}]')
                
        if self.config['Username']:
            self.EMAIL_USERNAME = str(self.config['Username'][0])
        if self.config['Password']:
            self.EMAIL_PASSWORD = str(self.config['Password'][0])
        if self.config['Sender']:
            self.EMAIL_SENDER = str(self.config['Sender'][0])
        if self.config['Receiver']:
            self.EMAIL_RECEIVER = (','.join(self.config['Receiver']))
        if self.config['Host']:
            self.SERVER_HOST = str(self.config['Host'][0])
        if self.config['Port']:
            self.SERVER_PORT = int(self.config['Port'][0])
        
    # ----------------- permissions ------------------------ #        
    def check_permission(permission, activity=None):
        if platform == "android":
            activity = PythonActivity
        if not activity:
            return False

    #   permission_status = ContextCompat.checkSelfPermission(activity,permission)
        permission_status = 0
        Logger.info(permission_status)
        permission_granted = 0 == permission_status
        Logger.info("Permission Status: {}".format(permission_granted))
        return permission_granted

    def ask_permission(permission):
        PythonActivity.requestPermissions([permission])

    def ask_permissions(self):
        request_permissions(self.required_permissions)

    def check_required_permission(self):
        permissions = self.required_permissions
        #
        has_permissions = True
        for permission in permissions:
            if not self.check_permission(permission):
                has_permissions = False
        return has_permissions
            
    def create_recorder(self):
        now = datetime.now()
        dt_string = now.strftime("%d%b%Y_%H%M%S")
        self.mp3Filename = f'Mp3Recorder_{dt_string}.mp3'

        self.recorder = self.MediaRecorder()
        self.recorder.setAudioSource(self.AudioSource.MIC)
        self.recorder.setOutputFormat(self.OutputFormat.MPEG_4)
        self.recorder.setOutputFile(self.mp3Filename)
        self.recorder.setAudioEncoder(self.AudioEncoder.AAC)
        self.recorder.prepare()

    def get_recorder(self):
        if not hasattr(self, "recorder"):
            self.create_recorder()
        return self.recorder

    def remove_recorder(self):
        delattr(self, "recorder")
   
    # ----------------- record_start ------------------------ #
    def record_start(self):
        self.get_recorder()
        if self.check_required_permission():
            # - new
            self.create_recorder()
            # - 
            self.recorder.start()
        else:
            self.ask_permissions()

    # ----------------- record_stop ------------------------ #
    def record_stop(self):
        self.get_recorder()
        self.recorder.stop() 
      
        # Copy the mp3 to Main Storage:
        ss = SharedStorage()
        share = ss.copy_to_shared(self.mp3Filename)
        path = ss.copy_from_shared(share)
        self.mp3_filename = path

        self.recorder.reset()
        self.recorder.release()
        # we need to do this in order to make the object reusable
        self.remove_recorder()
                
    # ======================
    #       record 
    # ======================
    def record(self,state):
        if state == 'ready':
            state = 'recording'
            self.record_start()
        elif state == 'recording':
            state = 'ready'
            self.record_stop()
        return state, self.mp3_filename

    # ======================
    #       email 
    # ======================

    def send_email(self, filename):
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        from os.path import exists

        if filename == None or not exists(filename):
            return f' Error: [{filename}] does not exist.'
        
        basefn = os.path.basename(filename)
        
        # set up the SMTP server
        server = smtplib.SMTP(self.SERVER_HOST, self.SERVER_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        print(f'SERVER_HOST |{self.SERVER_HOST}|')
        print(f'SERVER_PORT |{self.SERVER_PORT}|')
        print(f'EMAIL_USERNAME |{self.EMAIL_USERNAME}|')
        print(f'EMAIL_PASSWORD |{self.EMAIL_PASSWORD}|')
        print(f'EMAIL_RECEIVER |{self.EMAIL_RECEIVER}|')
        
        server.login(self.EMAIL_USERNAME, self.EMAIL_PASSWORD)
        
        # setup payload
        msg = MIMEMultipart()
        msg['From'] = self.EMAIL_SENDER
        msg['To'] = self.EMAIL_RECEIVER

        # Subject
        msg['Subject'] = f'[{basefn}] From Mp3Recorder'

        # Body
        body = f'[{basefn}] From Mp3Recorder'
        msg.attach(MIMEText(body, 'plain'))

        # file attachment
        attachment = open(filename, "rb")
        p = MIMEBase('application', 'octet-stream')
        p.set_payload((attachment).read())
        encoders.encode_base64(p)
        p.add_header('Content-Disposition', "attachment; filename= %s" % basefn)
        msg.attach(p)
        
        #Send the mail
        text = msg.as_string()
        server.sendmail(self.EMAIL_SENDER, self.EMAIL_RECEIVER, text)
        server.quit()        
        
        return f'[{basefn}] email complete.'
    
    # ======== email ========
    def email(self, filename):
        return self.send_email(filename)

    # ======================
    #       exit 
    # ======================
    def exit(self):
        quit()

