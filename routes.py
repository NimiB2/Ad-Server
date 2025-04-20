from controller.ad_entrypoints import ad_routes_blueprint

def init_routes(app):
    app.register_blueprint(ad_routes_blueprint)