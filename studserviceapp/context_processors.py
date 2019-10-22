

def user_info(request):
    username = ''
    if request.session.has_key('user'):
        username = request.session['user']
    if request.session.has_key('funk'):
        funkcionalnosti = request.session['funk']
        return {'user':username, 'funk':funkcionalnosti}
    return {'user':username}