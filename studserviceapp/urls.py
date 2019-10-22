from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('timetable/<str:username>', views.timetableforuser, name='timetableforuser'),
    path('nastavnik/<str:username>', views.nastavnik_details, name='nastavnik'),
    path('raspored/<str:username>', views.raspored_nastave, name='raspored_nastave'),
    path('nastavnici', views.nastavnici, name='nastavnici'),
    path('nastavnici_template', views.nastavnici_template, name='nastavnici_template'),
    path('forma/<str:user>', views.unos_obavestenja_form, name='forma'),
    path('saveobavestenje', views.save_obavestenje, name='saveobavestenje'),
    path('dodavanje_izbornih_grupa', views.dodavanje_izbornih_grupa, name='dodavanje_izbornih_grupa'),
    path('dodaj_semestar', views.dodaj_semestar, name='dodaj_semestar'),
    path('dodaj_izbornu', views.dodaj_izbornu, name='dodaj_izbornu'),
    path('izmena_izborne_grupe/<str:oznaka_grupe>', views.izmena_izborne_grupe, name='izmena_izborne_grupe'),
    path('sacuvaj_promene_izborne', views.sacuvaj_promene_izborne, name='sacuvaj_promene_izborne'),
    path('izbor_grupe/<str:username>', views.izbor_grupe, name='izbor_grupe'),
    path('sacuvaj_grupu', views.sacuvaj_grupu, name='sacuvaj_grupu'),
    path('izabrane_grupe', views.prikaz_izabranih_grupa, name='izabrane_grupe'),
    path('detalji_grupe/<str:oznaka>', views.detalji_grupe, name='detalji_grupe'),
    path('student_profile/<str:username>', views.student_profile, name='student_profile'),
    path('nastavnik_raspored/<str:username>', views.nastavnik_raspored, name='nastavnik_raspored'),
    path('grupa/<str:oznaka>', views.grupa, name='grupa'),
    path('slika/<str:id>', views.slika, name='slika'),
    path('import_kolokvijumske_nedelje', views.import_kolokvijumske_nedelje, name='import_kolokvijumske_nedelje'),
    path('ispravka_import', views.ispravka_import, name='ispravka_import'),
    path('dodaj_ispravljene', views.dodaj_ispravljene, name='dodaj_ispravljene'),
    path('mail/<str:username>', views.mail, name='mail'),
    path('slanje_maila', views.slanje_maila, name='slanje_maila'),
    path('login', views.login, name='login'),
    path('authenticate', views.authenticate, name='authenticate'),
    path('home', views.home, name='home'),
    path('prikaz_celog_rasporeda/<str:username>', views.prikaz_celog_rasporeda, name='prikaz_celog_rasporeda'),
    path('student_izbor_grupe_info/<str:username>', views.student_izbor_grupe_info, name='student_izbor_grupe_info'),
    path('logout', views.logout, name='logout')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)