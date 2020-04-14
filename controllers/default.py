# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
def index():
    response.flash = T("Hello World")
    return dict(message=T('Welcome to web2py!'))

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
    x=pattern % (URL("compo_change_serie.load"),"shadow_clone")
    app_logging.info(x)
    form.element(_name='serie')['_onchange'] = x 

    return dict(form=form,groupid=groupid)

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
