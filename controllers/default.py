# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
import git
import csv
import sqlite3
import datetime

DEFAULT_COUNTRY='France'
#column_list_str=cache.ram('column_list_str', lambda: dict(content=str(columns[4:]).replace('[','').replace(']','')) , time_expire=60*60)
column_list_str={}
countries=[]
kriko=1
country_values={}
#session.selected_countries_id=[]


def _init_log():
    import os,logging,logging.handlers,time
    logger = logging.getLogger(request.application)
    logger.setLevel(logging.INFO)
    #py2to3
    # ajout du param encoding
    handler = logging.handlers.RotatingFileHandler(os.path.join(
        request.folder,'logs','applog.log'),'a',1024*1024,1,encoding='utf-8')
    handler.setLevel(logging.INFO) #or DEBUG
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(filename)s %(lineno)d %(funcName)s(): %(message)s'))
    logger.addHandler(handler)
    return logger

app_logging = cache.ram('app_wide_log',lambda:_init_log(),time_expire=None)


def index():
    response.flash = T("Hello World")
    return dict(message=T('Welcome to web2py!'))


def compo_refresh_repo():
    # refresh datas with git pull
    # load database



    application_path=request.env.app_folders
    application=request.application
    c='request.application}/static/data/'
    #
    path_list=[x for x in application_path if application in x]
    path_final=f'{path_list[0]}/static/data/'
    timestamp=datetime.datetime.now().strftime("%A, %d. %B %Y @ %H:%M:%S")
    try:
        pull_status_raw=git.Git(path_final).pull()
    except:
        message=f"<BR>Refresh failed on {timestamp}"
        if "pull_status_raw" in locals():
             pull_status_raw+=message
        else:
            pull_status_raw=message
    
    # a revoir si on veut garder la date du dernier refresh successfull
    # parser dans des DIV différentes success et failure

    pull_status=f'Last successful refresh was recorded on {timestamp}: {pull_status_raw} <BR>'

    # reload database

    input_file=f'{path_final}/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'

    # get columns names from input file
    with open(input_file, newline='') as csvfile:
         reader = csv.DictReader(csvfile)
         colu=reader.fieldnames

    # create database in memory with shared cache to reuse connection
    con = sqlite3.connect("bimbamboum")
    cur = con.cursor()

    cur.execute(''' DROP TABLE IF EXISTS t ''')

    # define columns of the table
    columns=['Province', 'Country']
    columns.extend(colu[2:])
    

    # construit la requete : chaine avec autant de colonnes que ds le csv  : (?,?,?,?,?)
    ncol=len(columns)
    vals=f'({("?,"*ncol)[:-1]})'


    # column_list_str : cleaner
    app_logging.info(str(columns))
    column_list_str=str(columns).replace('[','').replace(']','')
    #session.column_list_str=str(columns[4:]).replace('[','').replace(']','').replace(' ','').replace(",",";").replace("'","").replace('/',',') # on memorise une version sans les 4 premiers champs    
    session.column_list_str=str(columns[4:])
    
    # pas besoin des noms de colonnes
    cur.execute("CREATE TABLE t (%s);" % column_list_str)
    # parse le fichier dans une liste de dictionnaires. 1 distionnaire = 1 ligne
    with open(input_file,'r') as fin: # `with` statement available in 2.5+
        # csv.DictReader uses first line in file for column headings by default
        dr = csv.DictReader(fin) # comma is default delimiter
        to_db = [ list(i.values()) for i in dr] # 
        #to_db = [(i['Province/State'], i['Country/Region']) for i in dr]
    # ce qui est important : avouir le bon nombre de colonnes 
    cur.executemany("INSERT INTO t VALUES %s;" % vals, to_db)
    #cur.executemany("INSERT INTO t ('Province', 'Country') VALUES (?, ?);", to_db)
    con.commit()
    #country_values=cache.ram('country_values',lambda: dict([(x[1],x[4:]) for x in cur.execute('select * from t ' )]))
    #app_logging.info("creation for france: %s" % str(country_values['France']))
    #
    # database is loaded
    # memorise la liste des pays en env
    cur=con.execute("SELECT Country FROM t WHERE Province='' ")
    x=cur.fetchall()
    countries=[c[0] for c in x]
    session.countries=countries

    # reset current country list for charts 
    session.selected_countries_id=[]
    app_logging.info(session.selected_countries_id)
    #
    # creer la combo de selection du pays
    # 
    # combo countries : important : donner un nom à la combo pour recuperer sa valeur dans le DOM!
    # il faut supprimer les champs cachés car s'ils ont été créés par la procédure d'import
    # les nouveaux créés par la requete pays s'ajoutent et on n'a que le pays par défaut
    # PLUS BESOIN mais conservé pour mémoire
    #fieds_to_remove=['array_dataset0','array_dataset1','scountry']
    #jscleanup=';'.join(['var fieldObject=document.getElementById("%s");fieldObject.remove()' % f for f in fieds_to_remove])
    jscleanup = '' # pas de cleanup nécessaire 
    #    
    # tout commence là   :    chgt de pays ds la combo. On recupere l'id du nouveau pays selectionné.
    #
    on_change=' %s ; var scountry=document.getElementById("countries");  web2py_component("%s/"+scountry.value,target="draw_ph")' % (jscleanup, URL("compo_get_array_dataset.load"))
    flux_retour=f"<select id='countries' onchange='{on_change}'"

    # ic : index pour le pays dans la liste
    ic=0
    for c in countries:
        # selected = valeur de theme préselectionnée dans la combo. option du tag select
        selected="selected='selected'>" if c == DEFAULT_COUNTRY else '>'
        if selected != '>': pass # selectionné par défaut
        #app_logging.info("str(c.id),selected,t.theme) = %s, %s, %s" % (str(t.id),selected,t.theme))
        flux_retour+="""<option value='%s' %s %s</option>""" % (ic,selected,c)
        ic+=1
    flux_retour+="</select>"
    XMLcon=XML(flux_retour)
    # met à dispo de la communauté la liste des pays

    return dict(pull_status=XML(pull_status),country_count=len(countries),XMLcon=XMLcon)

def db_select_countries():
    # recupere de la base la liste des pays
    con = sqlite3.connect("bimbamboum")
    cur = con.cursor()
    cur=con.execute("SELECT Country FROM t WHERE Province='' ")
    x=cur.fetchall()
    # app_logging.info(str(x))
    return [c[0] for c in x]

def db_select_values(loc,lt='sc'):
    # recupere les valeurs d'un pays ou d'une region
    con = sqlite3.connect("bimbamboum")
    cur = con.cursor()
    
    if lt=='c':
        location=loc.replace("'","''")
        cur=con.execute(f"select * from t where Country ='{location}' and Province='' ")
    elif lt=='p':
        location=loc.replace("'","''")
        cur=con.execute(f"select * from t where Province='{location}' ")
    elif lt== 'mc':
        #app_logging.info("**** session.selected_countries_id %s" % session.selected_countries_id)
        #app_logging.info("**** session.countries %s" % session.countries[1:4])

        #countries_clause=" or Country='".join([session.countries[x] for x in session.selected_countries_id])
        countries_clause=' or Country="'.join([session.countries[x]+'"' for x in loc])
        app_logging.info("CC %s" % countries_clause)
        cur=con.execute(f'select * from t where (Country="{countries_clause} ) and Province="" ')
        #cur=con.execute(f"select * from t where (Country='France' or Country='Denmark') and Province='' ")
        
    elif lt=='mp':
        pass
    else:
        return 'Error'

    # ignore les 4 premieres colonnes    
    rs= [ x[4:] for x in cur.fetchall() ]
    #app_logging.info('rs: %s'%rs)


    res=[]
    for f in rs:
        #print (res)
        e=[]
        for g in f:
            #print (g)
            e.append(int(g))
        #print (e)
        # nettoie.
        t=str(e).replace("]","").replace("[","").replace(' ','').replace("'","")

        res.append(t)


    #values=str([int(s) for s in res]).replace("]","").replace("[","").replace(' ','')
    app_logging.info('**************res: %s'%len(res))
    return res


def compo_del_country(): 
    # retire le dernker pays a la liste

    sc=session.selected_countries_id
    if sc: sc.pop()


    return dict(sc=sc)  



def compo_add_country(): 
    # ajoute un pays a la liste

    cc=int(request.args[0])
    cc_name=session.countries[cc]

    # l'ajoute accumulateur si pas deja present
    if cc not in session.selected_countries_id: session.selected_countries_id.append(cc)

    return dict(cc=cc)  

def compo_get_array_dataset():
    # recupère la valeur combo
    # recupère les données des pays : sélectionnés + combo
    # pour les renvoyer au grapheur
    # app_logging.info("len %s"%len(request.args))

    app_logging.info("en entree session.selected_coutries *** %s" % session.selected_countries_id)
    # combo ou défaut (apres chargmement init)
    cc=int(request.args[0]) if len(request.args) else session.countries.index(DEFAULT_COUNTRY)
    # scope =  combo + selected
    countries=session.selected_countries_id.copy() # on copie la liste origine pour pas la modifier
    countries.append(cc)

    #if session.selected_coutries_id is None: session.selected_countries_id=[cc]


    app_logging.info("selected_country %s"%cc)

    #countries=db_select_countries()
    #selected_country=session.countries[selected_country_id
    

    # graph datas
    xdataset=session.column_list_str
    app_logging.info("je cherche comme coutries *** %s" % countries)
    ydataset=db_select_values(countries,'mc')
    #=["1,2,20,30,10,20","1,2,4,5,7,10"]
    # passe de '2','3',.. a '2,3,4..'
    
    app_logging.info("Yda=%s"%ydataset)
    
    #app_logging.info("xda TR=%s"% xdattr)
    
    #ydataset=str([int(s) for s in series]).replace("]","").replace("[","").replace(' ','')
    #xdataset="'1/2/20','1/3/20','1/4/20','1/5/20','1/6/20','1/7/20'"
    #moment("12/25/1995", "MM-DD-YYYY");
    #new Date(2017, 08, 16)
    #xdataset="'1/22/20','1/23/20','1/24/20','1/25/20','1/26/20','1/27/20'"
    # xdataset="2017,08,16;2017,08,17;2017,08,18;2017,08,19;2017,08,20"
    # xdataset="1,22,20;1,23,20;1,24,20;1,25,20;1,26,20"
    #xdataset=xdattr
    #ydataset="1,2,4,5,7,10"
    #ydataset="0,1,3,5,7"
    selected_countries=[ session.countries[i] for i in countries]
    app_logging.info('les pay sont %s' % selected_countries)
    return dict(selected_countries=selected_countries,dataset=(xdataset,ydataset))

def compo_refreshed_data():
    # refresh datas with git pull
    #w2p_path=request.env.applications_parent
    app_logging.info("comminin from the cold")

    x=db_select_countries()
    return dict(refreshed_data=str(x))

def dataim():

    import csv

    with open('files/names.csv', newline='') as csvfile:
         reader = csv.DictReader(csvfile)
         print(reader.fieldnames)
         """
         for row in reader:
             p=row['Province/State']
             c=row['Country/Region']
             if (p and c):
                print (p,c)
         """

@auth.requires_login()
def ajax_cascade_province_only():
    # NOT USED SO FAR
    # specifique à la selection de la matiere et de la cascade sur le province
    # appelé depuis la vue quand on change la valeur de la combo matiere
    #
    # on recupere la matiere
    # on en déduit les provinces de la combo
    #app_logging.info('ajax_cascade_province_collections matiere = %s' % request.vars.matiere_id)
    #app_logging.info('ajax_cascade_province_collections province = %s' % request.vars.province_id)
    provinces = db(db.province.matiere==request.vars.matiere_id).select(db.province.ALL,orderby=db.province.province)
    #
    # le province selectionné est soit le premier de la liste lorsque l'on a changé de matière [1]
    # soit la valeur du province quand on a selectioné un nouveau province dans la combo [2}

    sprovince_1= db.province[request.vars.province_id] if request.vars.province_id else provinces.first()
    sprovince=sprovince_1.id

    #app_logging.info('** ajax_cascade_province_collections province = %s' % sprovince)


    # &&&& le specifique est la
    result=tab_provinces(sprovince)
    session.province_to_select=sprovince
    session.matiere_to_select=db.province[sprovince].matiere

    # le resultat est une combo avec 2 drop down matiere et theme
    # reinjectée dans la vue

    return XML(result)



def grp():
    if request.env.request_uri[-1]=='/': redirect (URL())

    #if request.args(0): redirect (URL())
    groupid=request.args(0)

    fi20=Field('serie',requires=IS_IN_SET([1,2]),default=1,widget=SQLFORM.widgets.radio.widget)
    fields=[fi20]
    form = SQLFORM.factory(*fields,
         submit_button=T('Generate the graph'),
               formstyle='table2cols'
                )
    #form[0].insert(1,XML('<BR>'))
    #form.add_button(T("Pick up verbs"),URL(f='list_verbs',args='new'))

    form.element('input[type=submit]')['_class']="btn btn-success btn-xs"
    #_onchange="ajax('ajax_cascade_theme_exams', ['matiere_id','theme_id','mybutton_1'], 'shadow_clone');")

    #form.element(_name='serie')['_onchange'] = XML("ajax('ajax_change_serie', [], ':eval');")
    #form.element(_name='serie')['_onchange'] = XML("alert();")


    pattern='web2py_component("%s"+"/"+$("#serie1").prop("checked")+"/"+$("#serie2").prop("checked"),target="%s");'
    # on appelle 3 composants tres semblables. ce qui les distingue : leur nom et la div dans laquelle ils injectent leur résultat
    # a chaque changement clic radio : load image, load titre du plantu , load code plantu
    x=pattern % (URL("compo_change_serie.load"),"serie_ph")
    app_logging.info(x)
    form.element(_name='serie')['_onchange'] = x 

    return dict(form=form,groupid=groupid,countries=[],XMLcon="")

def compo_change_serie():
    series=["1,2,20,30,10,20","1,2,4,5,7,10"]
    serie_id=request.args
    selected= serie_id.index('true')
    app_logging.info(selected)
    
    return dict(serie_id=selected+1,laserie=series[selected])


# ---- API (example) -----
@auth.requires_login()
def api_get_user_email():
    if not request.env.request_method == 'GET': raise HTTP(403)
    return response.json({'status':'success', 'email':auth.user.email})

# ---- Smart Grid (example) -----
@auth.requires_membership('admin') # can only be accessed by members of admin groupd
def grid():
    response.view = 'generic.html' # use a generic view
    tablename = request.args(0)
    if not tablename in db.tables: raise HTTP(403)
    grid = SQLFORM.smartgrid(db[tablename], args=[tablename], deletable=False, editable=False)
    return dict(grid=grid)

# ---- Embedded wiki (example) ----
def wiki():
    auth.wikimenu() # add the wiki to the menu
    return auth.wiki() 

# ---- Action for login/register/etc (required for auth) -----
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())

# ---- action to server uploaded static content (required) ---
@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)
