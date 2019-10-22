import csv

from django.core import serializers
from django.contrib.auth import logout as django_logout
from django.shortcuts import render
from django.shortcuts import redirect

# Create your views here.
from django.http import HttpResponse
from django.http import Http404
from django.template import loader
from django.core.files.storage import FileSystemStorage
from studserviceapp.models import *
import datetime
import time
import re
import ast
from studserviceapp import send_gmails, context_processors
import json

def index(request):
    return HttpResponse("Dobrodosli na studentski servis")

def timetableforuser(request, username):
    return HttpResponse("Dobrodosli na studentski servis, raspored za username %s." %username)

def raspored_nastave(request, username):
    nalog = Nalog.objects.filter(username=username)
    if not nalog.exists():
        raise Exception('Invalid username')
    nalog = nalog[0]
    if nalog.uloga == 'student':
        raspored = ''
        student = Student.objects.filter(nalog=nalog)[0]
        print(student.grupa)
        termini = Termin.objects.all()
        for t in termini:
                if student.grupa in t.grupe.all():
                    raspored += t.predmet.naziv + ' - ' + t.pocetak.strftime("%H:%M") + ' - ' + t.zavrsetak.strftime("%H:%M") + ', ' + t.dan + ', ' + t.oznaka_ucionice + ', ' + t.tip_nastave + " ------ "
        return HttpResponse("Raspored za studenta: " + username + " ------ " + raspored)
    else:
        raspored = ''
        nastavnik = Nastavnik.objects.filter(nalog=nalog)[0]
        termini = Termin.objects.all()
        for t in termini:
            if t.nastavnik == nastavnik and t.predmet in nastavnik.predmet.all():
                raspored += t.predmet.naziv + ' - ' + t.pocetak.strftime("%H:%M") + ' - ' + t.zavrsetak.strftime("%H:%M") + ', ' + t.dan + ', ' + t.oznaka_ucionice + " ------ "
        return HttpResponse("Raspored za nastavnika: " + username + " ------ " + raspored)

def nastavnik_details(request, username):
    try:
        qs = Nastavnik.objects.filter(nalog__username= username)
        n = qs[0]
        str = "Ime: "+n.ime + "<br>Prezime:" + n.prezime + "<br>Titula:" + n.titula + "<br>Zvanje:" + n.zvanje
        return HttpResponse("Podaci o nastavniku<br> %s." % str)
    except IndexError:
        raise Http404("Ne postoji nastavnik sa nalogom %s" % username)

def nastavnici(request):
    qs = Nastavnik.objects.all()
    str = ""
    for n in qs:
        str += "Ime: "+n.ime + " Prezime:" + n.prezime + " Titula:" + n.titula + " Zvanje:" + n.zvanje + "<br>"
    return HttpResponse(str)


def nastavnici_template(request):
    qs = Nastavnik.objects.all()
    template = loader.get_template('studserviceapp/nastavnici.html')
    context = { 'nastavnici' : qs}
    return HttpResponse(template.render(context, request))

def unos_obavestenja_form(request, user):
    try:
        n = Nalog.objects.get(username = user)
        if n.uloga == 'sekretar' or n.uloga == 'administrator':
            context = {'nalog':n}
            return render(request, 'studserviceapp/forma.html', context)
        else:
            return HttpResponse('<h1>Korisnik mora biti sekretar ili administrator</h1>')
    except:
        Nalog.DoesNotExist
        return HttpResponse('<h1>Username ' + user + ' not found</h1>')

def save_obavestenje(request):
    tekst = request.POST['tekst']
    postavio = Nalog.objects.get(username=request.POST['postavio'])

    if 'file' in request.FILES.keys():
        uploaded_file = request.FILES['file']
        uploaded_file.name = str(int(round(time.time() * 1000))) + uploaded_file.name;
        obavestenje = Obavestenje(tekst=tekst, postavio=postavio, datum_postavljanja=datetime.datetime.now(), fajl=uploaded_file)
        obavestenje.save()
        print('uso u if')
    else:
        obavestenje = Obavestenje(tekst=tekst, postavio=postavio, datum_postavljanja=datetime.datetime.now(), fajl='null')
        obavestenje.save()
        print('uso u else')

    context = {'nalog':postavio, 'poruka':'Uspesno objavljeno obavestenje'}
    return render(request, 'studserviceapp/forma.html', context)


def dodavanje_izbornih_grupa(request):
    semestri = Semestar.objects.all()
    predmeti = Predmet.objects.all()
    list = []
    for p in predmeti:
        list.append(p)
    list = serializers.serialize("json", list)

    context = {'semestri':semestri, 'predmeti_json':list, 'predmeti':predmeti}
    return render(request, 'studserviceapp/dodavanje_izbornih_grupa.html', context)

def priprema_dodavanje_izbornih_grupa(request, message):
    semestri = Semestar.objects.all()
    predmeti = Predmet.objects.all()
    list = []
    for p in predmeti:
        list.append(p)
    list = serializers.serialize("json", list)

    context = {'semestri': semestri, 'predmeti_json': list, 'predmeti': predmeti, 'message':message}
    return render(request, 'studserviceapp/dodavanje_izbornih_grupa.html', context)

def dodaj_semestar(request):
    vrsta = request.POST['vrsta_semestra']
    skolska_godina_semestra = request.POST['skolska_godina_semestra']
    print(vrsta)
    print(skolska_godina_semestra)
    if vrsta == 'neparni':
        sem = Semestar(vrsta=vrsta, skolska_godina_pocetak=skolska_godina_semestra, skolska_godina_kraj=int(skolska_godina_semestra) + 1)
    else:
        if vrsta == 'parni':
            sem = Semestar(vrsta=vrsta, skolska_godina_pocetak=skolska_godina_semestra, skolska_godina_kraj=skolska_godina_semestra)
        else:
            raise Exception('Nije uneta vrsta semestra')
    sem.save()
    return priprema_dodavanje_izbornih_grupa(request, 'Uspesno dodat semestar')

def dodaj_izbornu(request):
    oznaka_grupe = request.POST['oznaka_grupe']
    oznaka_semestra = request.POST['oznaka_semestra']
    kapacitet = request.POST['kapacitet_grupe']
    smer = request.POST['smer_grupe']
    aktivna = request.POST['aktivnost_grupe']
    semestar_id = request.POST['semestar_id']
    semestar = Semestar.objects.get(id=semestar_id)
    predmeti = request.POST.getlist('lista')

    if int(oznaka_semestra) % 2 == 1 and semestar.vrsta == 'parni':
        raise Exception('Neparna oznaka semestra i paran semestar!')
    if int(oznaka_semestra) % 2 == 0 and semestar.vrsta == 'neparni':
        raise Exception('Parna oznaka semestra i neparan semestar!')

    if aktivna == 'aktivna':
        aktivna = True
    else:
        aktivna = False


    lista = oznaka_grupe.split(',')

    for item in lista:
        izborna_grupa = IzbornaGrupa(oznaka_grupe=item, oznaka_semestra=oznaka_semestra, kapacitet=kapacitet,smer=smer, aktivna=aktivna, za_semestar=semestar)
        izborna_grupa.save()

        for p in predmeti:
            pr = Predmet.objects.get(naziv=p)
            izborna_grupa.predmeti.add(pr)

    return priprema_dodavanje_izbornih_grupa(request, 'Uspesno dodata grupa')


def izmena_izborne_grupe(request, oznaka_grupe):
    grupa = IzbornaGrupa.objects.filter(oznaka_grupe=oznaka_grupe)

    if not grupa.exists():
        return HttpResponse("Izborna grupa ne postoji")

    semestri = Semestar.objects.all()
    predmeti = Predmet.objects.all()
    context = {'grupa':grupa, 'semestri':semestri, 'predmeti':predmeti}
    return render(request, 'studserviceapp/izmena_izborne_grupe.html', context)

def sacuvaj_promene_izborne(request):
    grupa_id = request.POST['grupa_id']
    grupa = IzbornaGrupa.objects.get(id=grupa_id)

    grupa.oznaka_grupe = request.POST['oznaka_grupe']
    grupa.oznaka_semestra = request.POST['oznaka_semestra']
    grupa.kapacitet = request.POST['kapacitet_grupe']
    grupa.smer = request.POST['smer_grupe']

    aktivna = request.POST['aktivnost_grupe']

    if aktivna == 'aktivna':
        grupa.aktivna = True
    else:
        grupa.aktivna = False

    semestar_id = request.POST['semestar_id']
    grupa.za_semestar = Semestar.objects.get(id=semestar_id)

    if int(grupa.oznaka_semestra) % 2 == 1 and grupa.za_semestar.vrsta == 'parni':
        raise Exception('Neparna oznaka semestra i paran semestar!')
    if int(grupa.oznaka_semestra) % 2 == 0 and grupa.za_semestar.vrsta == 'neparni':
        raise Exception('Parna oznaka semestra i neparan semestar!')

    for p in grupa.predmeti.all():
        grupa.predmeti.remove(p)

    predmeti = request.POST.getlist('lista')

    grupa.save()

    for p in predmeti:
        pr = Predmet.objects.get(naziv=p)
        grupa.predmeti.add(pr)

    return HttpResponse('Promene sacuvane!')


def izbor_grupe(request, username):
    try:
        n = Nalog.objects.get(username = username)
        if n.uloga == 'student':
            s = Student.objects.get(nalog_id=n.id)
            godine = Semestar.objects.all()
            poslednji_semestar = Semestar.objects.order_by('-id')[0]
            skup = set()
            for g in godine:
                skup.add(g.skolska_godina_pocetak)

            izborne_grupe = IzbornaGrupa.objects.filter(smer=s.smer, aktivna=True)
            finalne_izborne_grupe = []
            for grupa in izborne_grupe:
                if grupa.kapacitet > IzborGrupe.objects.filter(izabrana_grupa__id = grupa.id).count():
                    finalne_izborne_grupe.append(grupa)
            predmeti = Predmet.objects.all()

            izborne_grupe_json = []
            for izborna in izborne_grupe:
                izborne_grupe_json.append(izborna)
            izborne_grupe_json = serializers.serialize("json", izborne_grupe_json)

            context = {'student':s, 'godine':skup, 'poslednji_semestar':poslednji_semestar, 'izborne_grupe':finalne_izborne_grupe, 'izborne_grupe_json':izborne_grupe_json,
                       'predmeti':predmeti}
            return render(request, 'studserviceapp/izbor_grupe.html', context)
        else:
            return HttpResponse('<h1>Korisnik mora biti student')
    except:
        return HttpResponse('<h1>Username ' + username + ' not found</h1>')


def return_msg_izbor_grupe(request, username, message, tip):
    n = Nalog.objects.get(username=username)
    if n.uloga == 'student':
        s = Student.objects.get(nalog_id=n.id)
        godine = Semestar.objects.all()
        poslednji_semestar = Semestar.objects.order_by('-id')[0]
        skup = set()
        for g in godine:
            skup.add(g.skolska_godina_pocetak)

        izborne_grupe = IzbornaGrupa.objects.filter(smer=s.smer, aktivna=True)
        finalne_izborne_grupe = []
        for grupa in izborne_grupe:
            if grupa.kapacitet > IzborGrupe.objects.filter(izabrana_grupa__id=grupa.id).count():
                finalne_izborne_grupe.append(grupa)
        predmeti = Predmet.objects.all()

        izborne_grupe_json = []
        for izborna in izborne_grupe:
            izborne_grupe_json.append(izborna)
        izborne_grupe_json = serializers.serialize("json", izborne_grupe_json)

        context = {'student': s, 'godine': skup, 'poslednji_semestar': poslednji_semestar,
                   'izborne_grupe': finalne_izborne_grupe, 'izborne_grupe_json': izborne_grupe_json,
                   'predmeti': predmeti, 'messsage':message, 'tip':tip}
        return render(request, 'studserviceapp/izbor_grupe.html', context)


def sacuvaj_grupu(request):
    student = Student.objects.get(id = request.POST['studentId'])
    if IzborGrupe.objects.filter(student__id = student.id).count() ==0:
        ostvarenoESPB = request.POST['ostvareni_ ESPB']
        upisujeESPB = request.POST['upisani_ ESPB']
        broj_polozenih_ispita = request.POST['polozeni_ispiti']
        upisuje_semestar = request.POST.get('semestar', False)
        prvi_put_upisuje_semestar = request.POST.get('prvi_put', False)
        nacin_placanja = request.POST.get('skolarina', False)
        nepolozeni_predmeti = request.POST.getlist('lista')
        oznaka_grupe = request.POST['izabrana_grupa']
        izabrana_grupa = IzbornaGrupa.objects.get(oznaka_grupe=oznaka_grupe)
        upisan = True;
        izbor = IzborGrupe(ostvarenoESPB=ostvarenoESPB, upisujeESPB=upisujeESPB, broj_polozenih_ispita=broj_polozenih_ispita,
                           upisuje_semestar=upisuje_semestar, prvi_put_upisuje_semestar=prvi_put_upisuje_semestar,
                           nacin_placanja=nacin_placanja, student=student, izabrana_grupa=izabrana_grupa, upisan=upisan)
        izbor.save()
        for predmet in nepolozeni_predmeti:
            p = Predmet.objects.get(naziv=predmet)
            izbor.nepolozeni_predmeti.add(p)
        return return_msg_izbor_grupe(request, request.session['user'], 'Uspesno odabrana grupa', 'uspeh')
    else:
        return return_msg_izbor_grupe(request, request.session['user'], 'Vec ste odabrali grupu', 'greska')

def prikaz_izabranih_grupa(request):
    izbori = IzborGrupe.objects.all()
    izabrane_grupe = set()
    for i in izbori:
        izabrane_grupe.add(i.izabrana_grupa)

    lista_grupa = []
    for g in izabrane_grupe:
        lista_grupa.append(g)
    print(lista_grupa)

    semestri = Semestar.objects.all()

    semestri_json = []
    for sem in semestri:
        semestri_json.append(sem)
    semestri_json = serializers.serialize('json', semestri_json)

    izabrane_json = []
    for izabrana in lista_grupa:
        izabrane_json.append(izabrana)
    izabrane_json = serializers.serialize('json', izabrane_json)

    context = {'lista_grupa':lista_grupa, 'semestri':semestri, 'semestri_json':semestri_json, 'izabrane_json':izabrane_json}
    return render(request, 'studserviceapp/izabrane_grupe.html', context)

def detalji_grupe(request, oznaka):
    grupa = IzbornaGrupa.objects.filter(oznaka_grupe=oznaka)
    if not grupa.exists():
        raise Exception('Izborna grupa ne postoji!')
    grupa = grupa[0]
    izborne = IzborGrupe.objects.filter(izabrana_grupa=grupa)
    studenti = []
    for i in izborne:
        studenti.append(i.student)
    predmeti_grupe = grupa.predmeti.all()
    context = {'studenti':studenti, 'predmeti_grupe':predmeti_grupe, 'grupa':grupa}
    return render(request, 'studserviceapp/detalji_grupe.html', context)

def student_profile(request, username):
    nalog = Nalog.objects.filter(username=username)
    if not nalog.exists():
        raise Exception('Student ne postoji')
    nalog = nalog[0]
    student = Student.objects.get(nalog=nalog)
    context = {'student': student, 'nalog': nalog}
    if request.method == 'POST':
        uploaded_file = request.FILES['slika']
        uploaded_file.name = str(int(round(time.time() * 1000))) + uploaded_file.name;
        student.slika = uploaded_file
        student.save()
        context = {'student': student, 'nalog': nalog}
    return render(request, 'studserviceapp/student_profile.html', context)

def nastavnik_raspored(request, username):
    nalog = Nalog.objects.filter(username=username)
    if not nalog.exists():
        raise Exception('Pogresan username')
    nalog = nalog[0]

    if nalog.uloga == 'administrator' or nalog.uloga == 'sekretar':
        predmeti = Predmet.objects.all()
        mapa = {}
        for predmet in predmeti:
            termini = Termin.objects.filter(predmet=predmet)
            mapa[predmet.naziv] = set()
            for t in termini:
               for g in t.grupe.all():
                   mapa[predmet.naziv].add(g);
        semestri = Semestar.objects.all()

        grupe_json = []
        grupe = Grupa.objects.all()
        for g in grupe:
            grupe_json.append(g)
        grupe_json = serializers.serialize('json', grupe_json)

        context = {'mapa':mapa, 'semestri':semestri, 'grupe_json':grupe_json}
        return render(request, 'studserviceapp/nastavnik_raspored.html', context)

    nastavnik = Nastavnik.objects.get(nalog=nalog)
    termini = Termin.objects.filter(nastavnik=nastavnik)
    skup = set()
    for t in termini:
        skup.add(t.predmet)

    mapa = {}
    for p in skup:
        mapa[p.naziv] = set()

    semestri = Semestar.objects.all()
    temp_set = set()

    for t in termini:
        if t.predmet.naziv in mapa.keys():
            for g in t.grupe.all():
                temp_set.add(g);
                mapa[t.predmet.naziv].add(g)

    grupe_json = []
    for g in temp_set:
        grupe_json.append(g)
    grupe_json = serializers.serialize('json', grupe_json)

    context = {'mapa':mapa, 'semestri':semestri, 'grupe_json':grupe_json}
    return render(request, 'studserviceapp/nastavnik_raspored.html', context)

def grupa(request, oznaka):
    grupa = Grupa.objects.filter(oznaka_grupe=oznaka)
    if not grupa.exists():
        raise Exception('Grupa ne postoji')
    grupa = grupa[0]

    studenti = Student.objects.filter(grupa=grupa)

    context = {'grupa':grupa, 'studenti':studenti}
    return render(request, 'studserviceapp/grupa.html', context)

def slika(request, id):
    student = Student.objects.get(id=id)
    context = {'student':student}
    return render(request, 'studserviceapp/slika.html', context)

def import_kolokvijumske_nedelje(request):
    context = {}
    if request.method == 'POST':
        broj_nedelje = request.POST['broj_nedelje']
        if not broj_nedelje:
            return render(request, 'studserviceapp/import_kolokvijumske_nedelje.html', {'greska':'Morate uneti broj kolokvijumske nedelje'})
        if broj_nedelje != '2' and broj_nedelje != '1':
            return render(request, 'studserviceapp/import_kolokvijumske_nedelje.html', {'greska': 'Broj kolokvijumske nedelje moze biti 1 ili 2'})
        if 'raspored' not in request.FILES.keys():
            return render(request, 'studserviceapp/import_kolokvijumske_nedelje.html',{'greska': 'Morate uploadovati raspored'})
        raspored_polaganja = RasporedPolaganja(kolokvijumska_nedelja=broj_nedelje)
        raspored_polaganja.save()
        uploaded_file = request.FILES['raspored']
        fs = FileSystemStorage()
        fs.save(uploaded_file.name, uploaded_file)
        mapa_termina = []
        line = 2
        izvestaj = {}
        losi_redovi = {}
        with open(fs.path(uploaded_file.name), encoding='utf-8') as csvfile:
            raspored = csv.reader(csvfile, delimiter=',')
            skip_header = False
            for red in raspored:
                if not skip_header:
                    skip_header = True
                    continue

                naziv_predmeta = red[0]
                if '-' in naziv_predmeta:
                    naziv_predmeta = naziv_predmeta.split(' - ')[0]
                profesor = red[3]
                ucionice = red[4]

                pocetak = red[5].split('-')[0]
                if ':' in pocetak:
                    pocetak = datetime.time(int(pocetak.split(':')[0]), int(pocetak.split(':')[1]))
                else:
                    pocetak = datetime.time(int(pocetak))
                kraj = red[5].split('-')[1]
                if ':'in kraj:
                    kraj = datetime.time(int(kraj.split(':')[0]), int(kraj.split(':')[1]))
                else:
                    kraj = datetime.time(int(kraj))


                dan = red[6]

                # uvek ucitava u poslednje dodat semestar
                sem = Semestar.objects.order_by('-id')[0]

                datum = ''

                if broj_nedelje == '2' and sem.vrsta == 'neparan':
                    datum = datetime.datetime.strptime(red[7] + str(sem.skolska_godina_kraj), '%d.%m.%Y')
                else:
                    datum = datetime.datetime.strptime(red[7] + str(sem.skolska_godina_pocetak), '%d.%m.%Y')

                #provere
                poruka = ''

                #if not re.fullmatch('([1-9]+|rg[1-9]+\d|RAF[1-9])|(([1-9]+|rg[1-9]+\d|RAF[1-9]).+)', ucionice):
                if not re.fullmatch('((RAF[1-9]+)|(rg[1-9]+)|([1-9]+))(\.((RAF[1-9]+)|(rg[1-9]+)|([1-9]+)))*', ucionice):
                    poruka = str(line) + ': Los format ucionica, ucionice mogu biti predstavljene brojem uz opcioni prefix rg ili RAF i razdvajane tackom ili zarezom, primer: 1.3.rg5.rg6.RAF7.3\n'

                predmet = Predmet.objects.filter(naziv=naziv_predmeta)
                if not predmet.exists():
                    poruka += str(line) + ': Predmet '+naziv_predmeta+' ne postoji\n'
                else:
                    predmet = predmet[0]

                if len(profesor.split(',')) > 1:
                    poruka += str(line) + ': Samo jedan profesor je dozvoljen po terminu polaganja\n'

                else:
                    nastavnik = Nastavnik.objects.filter(ime=profesor.split(' ')[0], prezime=profesor.split(' ')[1])
                    if not nastavnik.exists():
                        poruka += str(line) + ': Profesor '+profesor+' ne postoji\n'
                    else:
                        nastavnik = nastavnik[0]

                #print(naziv_predmeta + ', ' + profesor + ', ' + ucionice + ', ' + pocetak.strftime('%H:%M:%S') + ', '+ kraj.strftime('%H:%M:%S') + ', ' + dan + ', ' + datum.strftime('%d.%m.%Y'))

                if poruka != '':
                    izvestaj[line] = poruka
                    if len(profesor.split(',')) > 1:
                        losi_redovi[line] = red[0] + ',,,"' + red[3] + '",' + red[4] + ',' + red[5] + ',' + red[6] + ',' + red[7]
                    else:
                        losi_redovi[line] = red[0] + ',,,' + red[3]+','+red[4]+','+red[5]+','+red[6]+','+red[7]
                else:
                    termin = TerminPolaganja(predmet=predmet, nastavnik=nastavnik, ucionice=ucionice, pocetak=pocetak, kraj=kraj, dan=dan, datum=datum, raspored_polaganja=raspored_polaganja)
                    termin.save()
                    if mapa_termina.__len__() == 0:
                        mapa_termina.append(raspored_polaganja.id)
                    mapa_termina.append(termin.id)
                line += 1
        if izvestaj:
            context['greske'] = izvestaj
            context['termini'] = mapa_termina
            context['losi_redovi'] = losi_redovi
            context['raspored_id'] = raspored_polaganja.id
            fs.delete(uploaded_file.name)
            return render(request, 'studserviceapp/ispravka_import.html', context)
        else:
            context['uspesno'] = 1

        fs.delete(uploaded_file.name)
    return render(request, 'studserviceapp/import_kolokvijumske_nedelje.html', context)

def ispravka_import(request):
    if request.method == 'POST':
        if 'raspored' not in request.FILES:
            return render(request, 'studserviceapp/ispravka_import.html', {'greska':'Morate uploadovati fajl'})
        lista = request.POST['lista']
        lista = lista[1:-1]
        lista = lista.split(', ')
        counter = 0
        id_rasporeda = 0
        broj_nedelje = 0

        #brisanje podataka iz starog fajla

        for item in lista:
            if counter == 0:
                id_rasporeda = item
                counter += 1
                continue
            termin = TerminPolaganja.objects.get(id=int(item))
            termin.delete()

        raspored_polaganja = RasporedPolaganja.objects.get(id=id_rasporeda)
        broj_nedelje = raspored_polaganja.kolokvijumska_nedelja
        raspored_polaganja.delete()

        uploaded_file = request.FILES['raspored']
        fs = FileSystemStorage()
        fs.save(uploaded_file.name, uploaded_file)

        #unos podataka iz novog fajla

        context = {}
        mapa_termina = []
        line = 1
        izvestaj = {}
        losi_redovi = {}
        fs = FileSystemStorage()
        raspored_polaganja = RasporedPolaganja(kolokvijumska_nedelja=broj_nedelje)
        raspored_polaganja.save()
        with open(fs.path(uploaded_file.name), encoding='utf-8') as csvfile:
            raspored = csv.reader(csvfile, delimiter=',')
            skip_header = False
            for red in raspored:
                if not skip_header:
                    skip_header = True
                    continue
                naziv_predmeta = red[0]
                if '-' in naziv_predmeta:
                    naziv_predmeta = naziv_predmeta.split(' - ')[0]
                profesor = red[3]
                ucionice = red[4]

                pocetak = red[5].split('-')[0]
                if ':' in pocetak:
                    pocetak = datetime.time(int(pocetak.split(':')[0]), int(pocetak.split(':')[1]))
                else:
                    pocetak = datetime.time(int(pocetak))
                kraj = red[5].split('-')[1]
                if ':' in kraj:
                    kraj = datetime.time(int(kraj.split(':')[0]), int(kraj.split(':')[1]))
                else:
                    kraj = datetime.time(int(kraj))

                dan = red[6]

                # uvek ucitava u poslednje dodat semestar
                sem = Semestar.objects.order_by('-id')[0]

                datum = ''

                if broj_nedelje == '2' and sem.vrsta == 'neparan':
                    datum = datetime.datetime.strptime(red[7] + str(sem.skolska_godina_kraj), '%d.%m.%Y')
                else:
                    datum = datetime.datetime.strptime(red[7] + str(sem.skolska_godina_pocetak), '%d.%m.%Y')

                # provere
                poruka = ''

                if not re.fullmatch('((RAF[1-9]+)|(rg[1-9]+)|([1-9]+))(\.((RAF[1-9]+)|(rg[1-9]+)|([1-9]+)))*', ucionice):
                    poruka = str(
                        line) + ': Los format ucionica, ucionice mogu biti predstavljene brojem uz opcioni prefix rg ili RAF i razdvajane tackom ili zarezom, primer: 1.3.rg5.rg6.RAF7.3\n'

                predmet = Predmet.objects.filter(naziv=naziv_predmeta)
                if not predmet.exists():
                    poruka += str(line) + ': Predmet ' + naziv_predmeta + ' ne postoji\n'
                else:
                    predmet = predmet[0]

                nastavnik = Nastavnik.objects.filter(ime=profesor.split(' ')[0], prezime=profesor.split(' ')[1])
                if not nastavnik.exists():
                    poruka += str(line) + ': Profesor ' + profesor + ' ne postoji\n'
                else:
                    nastavnik = nastavnik[0]

                # print(naziv_predmeta + ', ' + profesor + ', ' + ucionice + ', ' + pocetak.strftime('%H:%M:%S') + ', '+ kraj.strftime('%H:%M:%S') + ', ' + dan + ', ' + datum.strftime('%d.%m.%Y'))

                if poruka != '':
                    izvestaj[line] = poruka
                    if len(profesor.split(',')) > 1:
                        losi_redovi[line] = red[0] + ',,,"' + red[3] + '",' + red[4] + ',' + red[5] + ',' + red[6] + ',' + red[7]
                    else:
                        losi_redovi[line] = red[0] + ',,,' + red[3]+','+red[4]+','+red[5]+','+red[6]+','+red[7]
                else:
                    termin = TerminPolaganja(predmet=predmet, nastavnik=nastavnik, ucionice=ucionice, pocetak=pocetak,
                                             kraj=kraj, dan=dan, datum=datum, raspored_polaganja=raspored_polaganja)
                    termin.save()
                    if mapa_termina.__len__() == 0:
                        mapa_termina.append(raspored_polaganja.id)
                    mapa_termina.append(termin.id)
                line += 1
        if izvestaj:
            context['greske'] = izvestaj
            context['termini'] = mapa_termina
            context['losi_redovi'] = losi_redovi
            context['raspored_id'] = raspored_polaganja.id
            fs.delete(uploaded_file.name)
            return render(request, 'studserviceapp/ispravka_import.html', context)
        else:
            context['uspesno'] = 1
        fs.delete(uploaded_file.name)
        return render(request, 'studserviceapp/ispravka_import.html', context)

    return render(request, 'studserviceapp/ispravka_import.html')

def dodaj_ispravljene(request):
    raspored_id = request.POST['raspored_id']
    lista = request.POST.getlist('lista')
    lista2 = request.POST.getlist('lista2')

    raspored_polaganja = RasporedPolaganja.objects.get(id=raspored_id)
    broj_nedelje = raspored_polaganja.kolokvijumska_nedelja

    counter = 0
    izvestaj = {}

    #pretvaranje liste reprezentovane kao string u pravu listu
    mapa_termina = request.POST['ucitani_termini']
    mapa_termina = ast.literal_eval(mapa_termina)

    losi_redovi = {}
    for item in lista:
        red = item.split(',')
        poruka = ''
        if len(red) != 8:
            poruka = str(lista2[counter]) + ': Lose formatiran red, ocekivano 8 polja.'
        else:
            naziv_predmeta = red[0]
            if '-' in naziv_predmeta:
                naziv_predmeta = naziv_predmeta.split(' - ')[0]
            profesor = red[3]
            ucionice = red[4]

            pocetak = red[5].split('-')[0]
            if ':' in pocetak:
                pocetak = datetime.time(int(pocetak.split(':')[0]), int(pocetak.split(':')[1]))
            else:
                pocetak = datetime.time(int(pocetak))
            kraj = red[5].split('-')[1]
            if ':' in kraj:
                kraj = datetime.time(int(kraj.split(':')[0]), int(kraj.split(':')[1]))
            else:
                kraj = datetime.time(int(kraj))

            dan = red[6]

            # uvek ucitava u poslednje dodat semestar
            sem = Semestar.objects.order_by('-id')[0]

            datum = ''

            if broj_nedelje == '2' and sem.vrsta == 'neparan':
                datum = datetime.datetime.strptime(red[7] + str(sem.skolska_godina_kraj), '%d.%m.%Y')
            else:
                datum = datetime.datetime.strptime(red[7] + str(sem.skolska_godina_pocetak), '%d.%m.%Y')

            # provere

            if not re.fullmatch('((RAF[1-9]+)|(rg[1-9]+)|([1-9]+))(\.((RAF[1-9]+)|(rg[1-9]+)|([1-9]+)))*', ucionice):
                poruka = str(lista2[counter]) + ': Los format ucionica, ucionice mogu biti predstavljene brojem uz opcioni prefix rg ili RAF i razdvajane tackom ili zarezom, primer: 1.3.rg5.rg6.RAF7.3\n'

            predmet = Predmet.objects.filter(naziv=naziv_predmeta)
            if not predmet.exists():
                poruka += str(lista2[counter]) + ': Predmet ' + naziv_predmeta + ' ne postoji\n'
            else:
                predmet = predmet[0]

            nastavnik = Nastavnik.objects.filter(ime=profesor.split(' ')[0], prezime=profesor.split(' ')[1])
            if not nastavnik.exists():
                poruka += str(lista2[counter]) + ': Profesor ' + profesor + ' ne postoji\n'
            else:
                nastavnik = nastavnik[0]

            # print(naziv_predmeta + ', ' + profesor + ', ' + ucionice + ', ' + pocetak.strftime('%H:%M:%S') + ', '+ kraj.strftime('%H:%M:%S') + ', ' + dan + ', ' + datum.strftime('%d.%m.%Y'))

        if poruka != '':
            izvestaj[lista2[counter]] = poruka
            losi_redovi[lista2[counter]] = item
        else:
            termin = TerminPolaganja(predmet=predmet, nastavnik=nastavnik, ucionice=ucionice, pocetak=pocetak,
                                     kraj=kraj, dan=dan, datum=datum, raspored_polaganja=raspored_polaganja)
            termin.save()
            if mapa_termina.__len__() == 0:
                mapa_termina.append(raspored_polaganja.id)
            mapa_termina.append(termin.id)
        counter += 1
    context = {}
    if izvestaj:
        context['greske'] = izvestaj
        context['termini'] = mapa_termina
        context['losi_redovi'] = losi_redovi
        context['raspored_id'] = raspored_polaganja.id
        return render(request, 'studserviceapp/ispravka_import.html', context)
    else:
        context['uspesno'] = 1
        return render(request, 'studserviceapp/ispravka_import.html', context)

def mail(request, username):
    nalog = Nalog.objects.filter(username=username)
    if not nalog.exists():
        raise Exception('Nalog ne postoji')
    nalog = nalog[0]
    combo_lista = []
    context = {}
    if nalog.uloga == 'sekretar' or nalog.uloga == 'administrator':
        combo_lista.append('svi')
        combo_lista.append('smer - RN')
        combo_lista.append('smer - RI')
        predmeti = Predmet.objects.all()
        for p in predmeti:
            combo_lista.append('predmet - ' + p.naziv)

        grupe = Grupa.objects.all()
        for g in grupe:
            combo_lista.append('grupa - ' + g.oznaka_grupe)

    if nalog.uloga == 'nastavnik':
        nastavnik = Nastavnik.objects.get(nalog=nalog)
        context['nastavnik'] = nastavnik
        for p in nastavnik.predmet.all():
            combo_lista.append('predmet - ' + p.naziv)

        termini = Termin.objects.filter(nastavnik=nastavnik)
        grupe = set()
        for t in termini:
            for g in t.grupe.all():
                grupe.add(g)

        for g in grupe:
            combo_lista.append('grupa - ' + g.oznaka_grupe)

    if nalog.uloga == 'student':
        raise Exception('Student ne moze slati mailove')

    context['combo_lista'] = combo_lista
    context['nalog_id'] = nalog.id
    context['email'] = nalog.username.lower() + '@raf.rs'
    context['funkcionalnosti'] = get_funkcionalnosti(nalog.uloga)
    context['username'] = nalog.username
    return render(request, 'studserviceapp/mail.html', context)

def pomocna(poruka, username, request):
    nalog = Nalog.objects.filter(username=username)
    if not nalog.exists():
        raise Exception('Nalog ne postoji')
    nalog = nalog[0]
    combo_lista = []
    context = {}
    if nalog.uloga == 'sekretar' or nalog.uloga == 'administrator':
        combo_lista.append('svi')
        combo_lista.append('smer - RN')
        combo_lista.append('smer - RI')
        predmeti = Predmet.objects.all()
        for p in predmeti:
            combo_lista.append('predmet - ' + p.naziv)

        grupe = Grupa.objects.all()
        for g in grupe:
            combo_lista.append('grupa - ' + g.oznaka_grupe)

    if nalog.uloga == 'nastavnik':
        nastavnik = Nastavnik.objects.get(nalog=nalog)
        context['nastavnik'] = nastavnik
        for p in nastavnik.predmet.all():
            combo_lista.append('predmet - ' + p.naziv)

        termini = Termin.objects.filter(nastavnik=nastavnik)
        grupe = set()
        for t in termini:
            for g in t.grupe.all():
                grupe.add(g)

        for g in grupe:
            combo_lista.append('grupa - ' + g.oznaka_grupe)

    if nalog.uloga == 'student':
        raise Exception('Student ne moze slati mailove')

    context['combo_lista'] = combo_lista
    context['nalog_id'] = nalog.id
    context['email'] = nalog.username.lower() + '@raf.rs'
    context['funkcionalnosti'] = get_funkcionalnosti(nalog.uloga)
    context['username'] = nalog.username
    context['uspesno'] = poruka
    return render(request, 'studserviceapp/mail.html', context)

def slanje_maila(request):
    opcija = request.POST['opcija']

    subject = request.POST['naslov']
    text = request.POST['tekst']

    sender = request.POST['email']

    print('Izabrana opcija: ' + opcija)

    lista_studenata = []

    if opcija == 'svi':
        for student in Student.objects.all():
            student_email = student.nalog.username.lower() + '@raf.rs'
            lista_studenata.append(student_email)
    elif opcija.startswith('smer - '):
        #RN ili RI
        opcija = opcija[7:len(opcija)]
        for student in Student.objects.filter(smer=opcija).all():
            student_email = student.nalog.username.lower() + '@raf.rs'
            lista_studenata.append(student_email)
    elif opcija.startswith('predmet - '):
        opcija = opcija[10:len(opcija)]
        predmet = Predmet.objects.filter(naziv=opcija)[0]
        for termin in Termin.objects.filter(predmet=predmet):
            for grupa in termin.grupe.all():
                for student in Student.objects.filter(grupa=grupa):
                    email = student.nalog.username.lower() + '@raf.rs'
                    if email not in lista_studenata:
                        lista_studenata.append(email)
    elif opcija.startswith('grupa - '):
        opcija = opcija[8:len(opcija)]
        grupa = Grupa.objects.filter(oznaka_grupe=opcija)[0]
        for student in Student.objects.filter(grupa=grupa):
            student_email = student.nalog.username.lower() + '@raf.rs'
            lista_studenata.append(student_email)

    attachment = False
    if 'attachment' in request.FILES:
        attachment = request.FILES['attachment']

    poruka = ''

    text = 'sender: ' + sender + '\n' + text

    if 'ime' in request.POST and 'prezime' in request.POST:
        text = 'Poslao nastavnik: ' + request.POST['ime'] + ' ' + request.POST['prezime'] + '\n\n' + text;

    for mail in lista_studenata:
        print('Sending mail to ' + mail)
        if attachment:
            send_gmails.create_and_send_message(sender, mail, subject, text, attachment)
        else:
            try:
                send_gmails.create_and_send_message(sender, mail, subject, text)
            except:
                poruka += 'Greska pri slanju na mail ' + mail

    if poruka == '':
        poruka = 'Uspesno poslat mail odgovarajucim studentima'

    return pomocna(poruka, request.session['user'], request)

def login(request):
    return render(request, 'studserviceapp/login.html')

def authenticate(request):
    username = ''
    if request.method == 'POST':
        username = request.POST['username']
    else:
        username = request.session['user']
    nalog = Nalog.objects.filter(username=username)
    if not nalog.exists():
        return render(request, 'studserviceapp/login.html', context={'msg':'Invalid username'})
    nalog = nalog[0]

    funkcionalnosti = get_funkcionalnosti(nalog.uloga)

    request.session['funk'] = funkcionalnosti
    request.session['user'] = username

    raspored, header = get_raspored(nalog, nalog.uloga)

    obavestenja = Obavestenje.objects.order_by('-id')
    for item in obavestenja:
        item.datum_postavljanja = item.datum_postavljanja.strftime("%d. %b %Y.")

    context = {'raspored':raspored, 'header':header, 'obavestenja':obavestenja}
    return render(request, 'studserviceapp/home.html', context)

def prikaz_celog_rasporeda(request, username):
    nalog = Nalog.objects.filter(username=username)
    if not nalog.exists():
        return render(request, 'studserviceapp/login.html', context={'msg': 'Invalid username'})
    nalog = nalog[0]

    funkcionalnosti = get_funkcionalnosti(nalog.uloga)

    raspored, header = get_raspored(nalog, 'administrator')

    obavestenja = Obavestenje.objects.order_by('-id')
    for item in obavestenja:
        item.datum_postavljanja = item.datum_postavljanja.strftime("%d. %b %Y.")

    context = {'username': username, 'funkcionalnosti': funkcionalnosti, 'raspored': raspored, 'header': header,
               'obavestenja': obavestenja}
    return render(request, 'studserviceapp/home.html', context)

def get_funkcionalnosti(uloga):
    funkcionalnosti = {}
    if uloga == 'administrator':
        funkcionalnosti = {'Upload rasporeda predavanja': 'upload_rasporeda',
                           'Upload raspored polaganja': 'import_kolokvijumske_nedelje',
                           'Unos obavestenja': 'forma', 'Slanje maila': 'mail',
                           'Unos izbornih grupa': 'dodavanje_izbornih_grupa',
                           'Pregled izabranih grupa': 'izabrane_grupe', 'Pregled studenata': 'nastavnik_raspored', 'Logout':'logout'}
    elif uloga == 'sekretar':
        funkcionalnosti = {'Unos obavestenja': 'forma', 'Slanje maila': 'mail',
                           'Pregled izabranih grupa': 'izabrane grupe',
                           'Pregled studenata': 'nastavnik_raspored', 'Logout':'logout'}
    elif uloga == 'nastavnik':
        funkcionalnosti = {'Prikaz celog rasporeda nastave': 'prikaz_celog_rasporeda',
                           'Pregled studenata': 'nastavnik_raspored', 'Slanje maila': 'mail', 'Logout':'logout'}
    elif uloga == 'student':
        funkcionalnosti = {'Prikaz celog rasporeda nastave': 'prikaz_celog_rasporeda',
                           'Upload slike': 'student_profile', 'Izbor grupe': 'izbor_grupe', 'Logout':'logout'}
    return funkcionalnosti

def get_raspored(nalog, uloga):
    header = ['Predmet', 'Dan', 'Vreme', 'Ucionica', 'Tip nastave']
    raspored = []
    if uloga == 'student':
        student = Student.objects.filter(nalog=nalog)[0]
        termini = Termin.objects.all()
        for t in termini:
                if student.grupa in t.grupe.all():
                    lista = [t.predmet.naziv, t.dan, t.pocetak.strftime("%H:%M") + ' - ' + t.zavrsetak.strftime("%H:%M"), t.oznaka_ucionice, t.tip_nastave]
                    raspored.append(lista)
    elif uloga == 'nastavnik':
        nastavnik = Nastavnik.objects.filter(nalog=nalog)[0]
        termini = Termin.objects.all()
        for t in termini:
            if t.nastavnik == nastavnik and t.predmet in nastavnik.predmet.all():
                lista = [t.predmet.naziv, t.dan, t.pocetak.strftime("%H:%M") + ' - ' + t.zavrsetak.strftime("%H:%M"), t.oznaka_ucionice, t.tip_nastave]
                raspored.append(lista)
    else:
        termini = Termin.objects.all()
        header = ['Predmet', 'Nastavnik', 'Dan', 'Vreme', 'Ucionica', 'Tip nastave']
        for t in termini:
            lista = [t.predmet.naziv, t.nastavnik.ime + ' ' + t.nastavnik.prezime, t.dan, t.pocetak.strftime("%H:%M") + ' - ' + t.zavrsetak.strftime("%H:%M"), t.oznaka_ucionice, t.tip_nastave]
            raspored.append(lista)
    return raspored, header

def student_izbor_grupe_info(request, username):
    if request.method == 'POST':
        ime = request.POST['ime']
        prezime = request.POST['prezime']
        indeks = request.POST['indeks']

        izbor = None
        context = {'username':username}

        if indeks != '':
            indeks = indeks.split('/')
            if len(indeks) == 3:
                student = Student.objects.filter(smer=indeks[0], broj_indeksa=indeks[1], godina_upisa=indeks[2])
                if student.exists():
                    student = student[0]
                    izbor = IzborGrupe.objects.get(student=student)
                    context = {'username':username, 'izbor':izbor, 'search':True, 'student':student}
        elif ime != '' and prezime != '':
            student = Student.objects.filter(ime=ime, prezime=prezime)
            if student.exists():
                student = student[0]
                izbor = IzborGrupe.objects.get(student=student)
                context = {'username':username, 'izbor':izbor, 'search':True, 'student':student}
        return render(request, 'studserviceapp/student_izbor_grupe_info.html', context)
    else:
        context = {'username':username}
        return render(request, 'studserviceapp/student_izbor_grupe_info.html', context)

def home(request):
    print('home')

def logout(request):
    django_logout(request)
    return redirect(login)