from django.db import models

# Create your models here.
from django.db import models

class Semestar(models.Model):
    vrsta = models.CharField(max_length=20)  # parni/neparni
    skolska_godina_pocetak = models.IntegerField()  # primer 2018
    skolska_godina_kraj = models.IntegerField()  # primer 2019

class Nalog(models.Model):
    username = models.CharField(max_length=200)
    ime = models.CharField(max_length=20)
    prezime = models.CharField(max_length=20)
    lozinka = models.CharField(max_length=100, null=True)  # google login, necemo koristiti password
    uloga = models.CharField(max_length=50)  # student, nastavnik, sekretar, administrator

class Grupa(models.Model):
    oznaka_grupe = models.CharField(max_length=10)
    smer = models.CharField(max_length=20, null=True)
    semestar = models.ForeignKey(Semestar, on_delete=models.DO_NOTHING)

class Predmet(models.Model):
    naziv = models.CharField(max_length=200)
    espb = models.IntegerField(null=True)
    semestar_po_programu = models.IntegerField(null=True)  # redni broj semestra u kom se slusa predmet
    fond_predavanja = models.IntegerField(null=True)
    fond_vezbe = models.IntegerField(null=True)

class Student(models.Model):
    ime = models.CharField(max_length=200)
    prezime = models.CharField(max_length=200)
    broj_indeksa = models.IntegerField()
    godina_upisa = models.IntegerField()
    smer = models.CharField(max_length=20)
    nalog = models.ForeignKey(Nalog, on_delete=models.CASCADE, default=0)
    grupa = models.ForeignKey(Grupa, on_delete=models.CASCADE)
    slika = models.FileField(upload_to='D:/DjangoProjectImageRepository')

    def __str__(self):
        return self.ime + " " + self.prezime

class Nastavnik(models.Model):
    ime = models.CharField(max_length=200)
    prezime = models.CharField(max_length=200)
    titula = models.CharField(max_length=20, null=True)
    zvanje = models.CharField(max_length=40, null=True)
    nalog = models.ForeignKey(Nalog, on_delete = models.CASCADE)
    predmet = models.ManyToManyField(Predmet)

class RasporedNastave(models.Model):
    datum_unosa = models.DateTimeField()
    semestar = models.ForeignKey(Semestar, on_delete=models.PROTECT)


class Termin(models.Model):
    oznaka_ucionice = models.CharField(max_length=50)
    pocetak = models.TimeField()
    zavrsetak = models.TimeField()
    dan = models.CharField(max_length=15)
    tip_nastave = models.CharField(max_length=20)  # predavanja, vezbe, praktikum
    nastavnik = models.ForeignKey(Nastavnik, on_delete=models.DO_NOTHING)
    predmet = models.ForeignKey(Predmet, on_delete=models.DO_NOTHING)
    grupe = models.ManyToManyField(Grupa)
    raspored = models.ForeignKey(RasporedNastave, on_delete=models.CASCADE)

class IzbornaGrupa(models.Model):
    oznaka_grupe = models.CharField(max_length=20)
    oznaka_semestra = models.IntegerField()
    kapacitet = models.IntegerField()
    smer = models.CharField(max_length=20)
    aktivna = models.BooleanField()
    za_semestar = models.ForeignKey(Semestar, on_delete=models.DO_NOTHING)
    predmeti = models.ManyToManyField(Predmet)

class IzborGrupe(models.Model):
    ostvarenoESPB = models.IntegerField()
    upisujeESPB = models.IntegerField()
    broj_polozenih_ispita = models.IntegerField()
    upisuje_semestar = models.IntegerField()  # redni broj semestra
    prvi_put_upisuje_semestar = models.BooleanField()
    nacin_placanja = models.CharField(max_length=30)
    nepolozeni_predmeti = models.ManyToManyField(Predmet)
    student = models.ForeignKey(Student,on_delete=models.DO_NOTHING)
    izabrana_grupa = models.ForeignKey(IzbornaGrupa,on_delete=models.CASCADE)
    upisan = models.BooleanField()  # na pocetku staviti false

class Obavestenje(models.Model):
    postavio = models.ForeignKey(Nalog, on_delete=models.DO_NOTHING)
    datum_postavljanja = models.DateTimeField()
    tekst = models.CharField(max_length=1000)
    fajl = models.FileField(upload_to='D:/DjangoProjectImageRepository')

class RasporedPolaganja(models.Model):
    kolokvijumska_nedelja = models.CharField(max_length=30)

class TerminPolaganja(models.Model):
    predmet = models.ForeignKey(Predmet, on_delete=models.DO_NOTHING)
    nastavnik = models.ForeignKey(Nastavnik, on_delete=models.DO_NOTHING)
    ucionice = models.CharField(max_length=50)
    pocetak = models.TimeField()
    kraj = models.TimeField()
    dan = models.CharField(max_length=20)
    datum = models.DateField()
    raspored_polaganja = models.ForeignKey(RasporedPolaganja, on_delete=models.DO_NOTHING)