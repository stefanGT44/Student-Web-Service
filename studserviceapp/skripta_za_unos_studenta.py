import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "untitled1.settings")
import django
django.setup()
from studserviceapp.models import Grupa, Nalog, Student

def uneti_studenta(ime, prezime, username, lozinka, oznaka_grupe, broj_indeksa, godina_upisa, smer):
    nalog = Nalog(username=username, ime=ime, prezime=prezime, lozinka=lozinka, uloga='student')
    nalog.save()
    grupa = Grupa.objects.filter(oznaka_grupe=oznaka_grupe)
    if not grupa.exists():
        nalog.delete()
        raise Exception('Uneta grupa ne postoji!')
    grupa = grupa[0]
    student = Student(ime=nalog.ime, prezime=nalog.prezime, broj_indeksa=broj_indeksa, godina_upisa=godina_upisa, smer=smer, nalog=nalog, grupa=grupa)
    student.save()




