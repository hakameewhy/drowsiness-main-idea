import pickle

class User:
    def __init__(self):
        self.nama = "kosong"
        self.alamat = "kosong"
        self.noSim = "kosong"
        self._matakantuk = 0
        self._menguap = 0

    def tambahmatakantuk(self, jumlah):
        self._matakantuk += jumlah

    def tambahmenguap(self,jumlah):
        self._menguap +=  jumlah



    @staticmethod
    def load():
        try:
            with open('user_data.pkl', 'rb') as f:
                return pickle.load()
        except:
            return User()
        
    def save(self):
        with open('user_data.pkl', 'wb') as f:
            pickle.dump(self,f)
    
