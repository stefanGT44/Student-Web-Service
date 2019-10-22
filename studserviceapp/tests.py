from django.test import TestCase

# Create your tests here.
from studserviceapp import send_gmails
from studserviceapp.loadfromcsv import load_from_csv, printCSV
from studserviceapp.skripta_za_unos_studenta import uneti_studenta


#load_from_csv('D:\\rasporedCSV.csv')

#uneti_studenta('Stefan', 'Ginic', 'sginic15', 'stegin39', '403', 43, 2015, 'RN')
#uneti_studenta('Ivana', 'Borisavljevic', 'iborisavljevic39', 'ivabor39', '407', 44, 2015, 'RI')
#uneti_studenta('Dzoni', 'Brat', 'dzonibrat', 'dzonibrat', '111', 45, 2016, 'RN')
#uneti_studenta('Nikola', 'Nikolic', 'nnikolic', 'nnikolic', '106', 34, 2017, 'RI')

uneti_studenta('Marko', 'Markovic', 'mmarkovic', 'mmarkovic', '403', 54, 2018, 'RN')


#send_gmails.create_and_send_message('photobase.gt@gmail.com', 'stefangwars@gmail.com', 'testiranje', 'ovo je tekst')