import pickle
class User:
    def __init__(self):
        self.nama = "kosong"
        self.alamat = "kosong"
        self.noSim = "kosong"
        self._matakantuk = 0
        self._menguap = 0

    def tambahmatakantuk(self, jumlah):
        jumlah = 4
        self._matakantuk = jumlah
        self.simpan()

    def tambahmenguap(self,jumlah):
        jumlah = 4 
        self._menguap = jumlah
        self.simpan();

    def simpan(self):
        with open ('user_data.pkl', 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load():
        try:
            with open('user_data.pkl', 'rb') as f:
                return pickle.load()
        except:
            return User()
    
