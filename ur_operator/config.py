import os

class Config:
    @property
    def DISABLE_INGRESS_HANDLING(self):
        return os.getenv('URO_DISABLE_INGRESS_HANDLING', 'False').lower() in ['true', '1']

    @property
    def UPTIMEROBOT_API_KEY(self):
        return os.environ['UPTIMEROBOT_API_KEY']
