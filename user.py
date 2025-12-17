import pickle
class User:
    def __init__(self):
        self.nama = "kosong"
        self.alamat = "kosong"
        self.noSim = "kosong"
        self._matakantuk = []
        self._menguap = []

    def tambahmatakantuk(self, jumlah):
        jumlah = 4
        total = self._matakantuk = jumlah
        self._matakantuk(total)

    def tambahmenguap(self,jumlah):
        jumlah = 4 
        total = self._menguap + jumlah
        self._menguap.append(total)

  