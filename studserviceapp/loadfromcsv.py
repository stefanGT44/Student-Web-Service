import csv
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "untitled1.settings")
import django
import datetime
django.setup()
from studserviceapp.models import Grupa, Nastavnik, Predmet, Nalog, RasporedNastave, Semestar, Termin

#grupe, raspored, semestar, termini

def load_from_csv(file_path):
    with open(file_path, encoding='utf-8') as csvfile:
        raspored_csv = csv.reader(csvfile, delimiter=';')
        #uvek ucitava u poslednje dodat semestar
        sem = Semestar.objects.order_by('-id')[0]
        r = RasporedNastave(datum_unosa=datetime.datetime.now(), semestar=sem)
        r.save()
        i = 0;
        noviPredmet = True
        skipHeader = False
        pred = ''

        for red in raspored_csv:
            if i < 2:
                i = i + 1
                continue
            if not red:
                noviPredmet = True
                continue
            if noviPredmet:
                noviPredmet = False
                p = Predmet(naziv=red[0])
                p.save()
                pred = p
                print('Predmet: ' + red[0])
                skipHeader = True
                continue
            if skipHeader:
                skipHeader = False
                continue
            print(red)
            index = 0
            while index < 4:
                current = red[index * 8 + 1:index * 8 + 8]

                if not current[0]:
                    index = index + 1
                    continue

                grupe = current[2].split(',')

                print(current[0])
                ime = current[0].split(' ')[1]
                prezime = current[0].split(' ')[0]

                ucionica = current[6]
                pocetak = current[5].split('-')[0]
                pocetak = datetime.time(int(pocetak.split(':')[0]), int(pocetak.split(':')[1]))
                kraj = datetime.time(int(current[5].split('-')[1]), 0)
                dan = current[4]

                tipNastave = 'Predavanja'
                if index == 1:
                    tipNastave = 'Praktikum'
                if index == 2:
                    tipNastave = 'Vezbe'
                if index == 3:
                    tipNastave = 'Predavanja i vezbe'

                if ime:
                    nalog = Nalog(username=(ime[0]+prezime), uloga='nastavnik', ime=ime, prezime=prezime)
                else:
                    nalog = Nalog(username=(prezime), uloga='nastavnik', prezime=prezime)

                nastavnik = ''

                if Nalog.objects.filter(ime=ime, prezime=prezime).exists():
                    nalog = Nalog.objects.filter(ime=ime, prezime=prezime)
                    nastavnik = Nastavnik.objects.filter(ime=ime, prezime=prezime)[0]
                else:
                    nalog.save()
                    tit = 'Profesor'
                    if index == 1:
                        tit = 'Praktikant'
                    if index == 2:
                        tit = 'Asistent'
                    nastavnik = Nastavnik(ime=ime, prezime=prezime, titula=tit, zvanje=tit, nalog=nalog)
                    nastavnik.save()

                nastavnik.predmet.add(pred)

                t = Termin(oznaka_ucionice=ucionica, pocetak=pocetak, zavrsetak=kraj, dan=dan, tip_nastave=tipNastave, nastavnik=nastavnik, predmet=pred, raspored=r)
                t.save()

                odeljenja = current[2].split(',')
                for o in odeljenja:
                    if not Grupa.objects.filter(oznaka_grupe=o.strip()).exists():
                        g = Grupa(oznaka_grupe=o.strip(), semestar=sem)
                        g.save()
                        t.grupe.add(g)
                    else:
                        g = Grupa.objects.filter(oznaka_grupe=o.strip())[0]
                        t.grupe.add(g)

                print(current)
                index = index + 1


def printCSV(file_path):
    with open(file_path, encoding='utf-8') as csvfile:
        raspored_csv = csv.reader(csvfile, delimiter=';')
        for red in raspored_csv:
            print(red)




