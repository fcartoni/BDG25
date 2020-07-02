from flask import Flask, render_templqate, request, abort, json
from bson import json_util
from pymongo import MongoClient, TEXT
import pandas as pd
import matplotlib.pyplot as plt
import os

# Para este ejemplo pediremos la id
# y no la generaremos automáticamente
USER_KEYS = ['uid', 'name', 'last_name',
            'occupation', 'follows', 'age']

USER = "grupo25"
PASS = "grupo25"
DATABASE = "grupo25"

# El cliente se levanta en la URL de la wiki
# URL = "mongodb://grupoXX:grupoXX@gray.ing.puc.cl/grupoXX"
URL = f"mongodb://{USER}:{PASS}@gray.ing.puc.cl/{DATABASE}"
client = MongoClient(URL)

# Utilizamos la base de datos del grupo
db = client["grupo25"]

# Seleccionamos la collección de usuarios
usuarios = db.users
mensajes = db.messages

# Iniciamos la aplicación de flask
app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>¡Bienvenidoa la Entrega 4 del Grupo 25!</h1>"

@app.route("/users")
def get_users():
    resultados = list(usuarios.find({}, {"_id": 0}))
    return json.jsonify(resultados)

@app.route("/messages", methods=['GET'])
def get_message_ids():
    uid1 = request.args.get('id1', None)
    uid2 = request.args.get('id2', None)
    if not uid1 and not uid2:
        resultados = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(resultados)
    else:
        if not list(usuarios.find({"uid": int(uid1)}, {"_id": 0})) and not list(usuarios.find({"uid": int(uid2)}, {"_id": 0})):
            return json.jsonify({'respuesta': "Los ids de los usuarios que ingresaste no existe"})
        if not list(usuarios.find({"uid": int(uid1)}, {"_id": 0})):
            return json.jsonify({'respuesta': "El id del primer usuario que ingresaste no existe"})
        if not list(usuarios.find({"uid": int(uid2)}, {"_id": 0})):
            return json.jsonify({'respuesta': "El id del segundo usuario que ingresaste no existe"})
        else:
            messages1 = list(mensajes.find({"sender": int(uid1), "receptant": int(uid2)}, {"_id": 0}))
            messages2 = list(mensajes.find({"sender": int(uid2), "receptant": int(uid1)},  {"_id": 0}))
            messages = messages1 + messages2
            return json.jsonify(messages)

@app.route("/users/<int:uid>")
def get_user(uid):
    users = list(usuarios.find({"uid": uid}, {"_id": 0}))
    if not users:
        return json.jsonify({'respuesta': "El id del usuario que ingresaste no existe"})
    else:
        messages = list(mensajes.find({"sender": int(uid)}, {"_id": 0}))
        return json.jsonify(users + messages)

@app.route("/messages/<int:mid>")
def get_message(mid):
    messages = list(mensajes.find({"mid": mid}, {"_id": 0}))
    if not messages:
        return json.jsonify({'respuesta': "El id del mensaje que ingresaste no existe"})
    else:
        return json.jsonify(messages)



def filter_not_in_message(prohibidas, id=None):
    if id:
        todo = list(mensajes.find({"sender": id}, {"_id": 0}))
    else:
        todo = list(mensajes.find({}, {"_id": 0}))
    str_malos = " ".join(prohibidas)
    if id:
        malos = mensajes.find({"$text": {"$search": str_malos}, "sender": id}, {"_id": 0})
    else:
        malos = mensajes.find({"$text": {"$search": str_malos}}, {"_id": 0})
    json_docs = []
    for doc in malos:
        print(doc, type(doc))
        json_doc = json.dumps(doc, default=json_util.default)
        json_docs.append(json_doc)
    final = []
    for a in json_docs:
        cosa = json.loads(a)
        final.append(cosa)

    filtrados = []

    for mensaje in todo:
        if mensaje not in final:
            filtrados.append(mensaje)
    return filtrados




def filter_id_message(id, parcial):
    filtrados = []
    for mensaje in parcial:
        if id == mensaje["sender"]:
            filtrados.append(mensaje)
    return filtrados

@app.route("/text-search")
def arreglo_filter_messages():
    try:
        data = request.get_json()
        try:
            desired = data["desired"]
        except KeyError:
            desired = None
        try:
            required = data["required"]
        except KeyError:
            required = None
        try:
            forbidden = data["forbidden"]
        except KeyError:
            forbidden = None
        try:
            id = data["userId"]
        except KeyError:
            id = None
        str_total = ""
        if required:
            str_required = ""
            for frase in required:
                str_required += "\"{}\"".format(frase)
            str_total += str_required
        if desired:
            str_total += " ".join(desired)
        if forbidden:
            str_forbidden = ""
            for palabra in forbidden:
                str_forbidden += " -{}".format(palabra)
            str_total += str_forbidden
        if not required and not desired and forbidden:
            if id:
                final = filter_not_in_message(forbidden, id=id)
            else:
                final = filter_not_in_message(forbidden, id=None)
        elif str_total != "":
            mensajes.create_index([("message", TEXT)])
            if id:
                parcial = mensajes.find({"$text": {"$search": str_total}, "sender": id}, {"_id": 0})
                print("ejecute parcial con id")
            else:
                parcial = mensajes.find({"$text": {"$search": str_total}}, {"_id": 0})
                print("ejecute parcial sin id")
            json_docs = []
            for doc in parcial:
                print(doc, type(doc))
                json_doc = json.dumps(doc, default=json_util.default)
                json_docs.append(json_doc)
            final = []
            for a in json_docs:
                cosa = json.loads(a)
                final.append(cosa)
        elif not required and not desired and not forbidden and id:
            final = list(mensajes.find({"sender": id}, {"_id": 0}))
        else:
            final = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(final)
    except:
        final = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(final)


def filter_messages():
    data = request.get_json()
    m1 = mensajes.find()
    m2 = mensajes.find()
    m3 = mensajes.find()
    desired = data["desired"]
    required = data["required"]
    forbidden = data["forbidden"]
    id = data["userId"]
    requeridas = []
    deseadas = []
    prohibidas = []

    if required != []:
        for i in required:
            for mensaje in m1:
                if id:
                    if i in mensaje["message"] and id == mensaje["sender"]:
                        msj = mensaje
                        del msj["_id"]
                        requeridas.append(msj)
                else:
                    if i in mensaje["message"]:
                        msj = mensaje
                        del msj["_id"]
                        requeridas.append(msj)
    else:
        requeridas = m1

    for i in desired:
        for mensaje in m2:
            if i in mensaje["message"] and id == mensaje["sender"]:
                msj = mensaje
                del msj["_id"]
                deseadas.append(msj)
    for i in forbidden:
        for mensaje in m3:
            if i in mensaje["message"] and id == mensaje["sender"]:
                msj = mensaje
                del msj["_id"]
                prohibidas.append(msj)

    final = []

    for mensaje in requeridas:
        if mensaje not in prohibidas:
            final.append(mensaje)

    for mensaje in deseadas:
        if mensaje not in prohibidas:
            final.append(mensaje)

    return json.jsonify(final)

@app.route("/messages", methods=['POST'])
def insert_message():
    data = request.get_json()
    error = False
    try:
        mensaje = data["message"]
    except KeyError:
        error = True
        return json.jsonify({'respuesta': 'No ingresaste un mensaje'})
    try:
        sender = data["sender"]
    except KeyError:
        error = True
        return json.jsonify({'respuesta': 'No ingresaste un sender'})
    try:
        receptant = data["receptant"]
    except KeyError:
        error = True
        return json.jsonify({'respuesta': 'No ingresaste un receptant'})
    try:
        lat = data["lat"]
    except KeyError:
        error = True
        return json.jsonify({'respuesta': 'No ingresaste una latitud'})
    try:
        long = data["long"]
    except KeyError:
        error = True
        return json.jsonify({'respuesta': 'No ingresaste una longitud'})
    try:
        date = data["date"]
    except KeyError:
        error = True
        return json.jsonify({'respuesta': 'No ingresaste una fecha'})
    if not list(usuarios.find({"uid": sender}, {"_id": 0})):
        error = True
        return json.jsonify({'respuesta': 'El id de sender ingresado no existe'})
    if not list(usuarios.find({"uid": receptant}, {"_id": 0})):
        error = True
        return json.jsonify({'respuesta': 'El id de receptant ingresado no existe'})

    if not error:
        ids = list(mensajes.find({}, {"_id": 0, "sender": 0, "receptant": 0, "lat": 0, "long": 0,
                                      "date": 0, "message": 0}))
        id_max = -1
        for diccionario in ids:
            val = diccionario["mid"]
            if val > id_max:
                id_max = val
        mensajes.insert_one({"mid": id_max + 1, "message": data["message"], "sender": data["sender"],
                             "receptant": data["receptant"], "lat": data["lat"], "long": data["long"],
                             "date": data["date"]})
        respuesta = "Tu mensaje fue insertado correctamente"
        return json.jsonify({'respuesta': respuesta})


@app.route("/message/<int:mid>", methods=["DELETE"])
def delete_message(mid):
    if type(mid) == int:
        messages = list(mensajes.find({"mid": mid}, {"_id": 0}))
        eliminado = mensajes.delete_one({'mid': mid})
        if messages:
            respuesta = "Mensaje eliminado correctamente"
        else:
            respuesta= "Id inválido"
    else:
        respuesta = "Error en el formato"
    return json.jsonify({'respuesta': respuesta})


@app.route("/test")
def test():
    # Obtener un parámero de la URL
    # Ingresar desde Params en Postman
    # O agregando ?name=... a URL
    param = request.args.get('name', False)
    print("URL param:", param)

    # Obtener un header
    # Ingresar desde Headers en Postman
    param2 = request.headers.get('name', False)
    print("Header:", param2)

    # Obtener el body
    # Ingresar desde Body en Postman
    body = request.data
    print("Body:", body)

    return f'''
            OK
            <p>parámetro name de la URL: {param}<p>
            <p>header: {param2}</p>
            <p>body: {body}</p>
            '''
            
if __name__ == "__main__":
    app.run()
    app.run(debug=True, port=5000) 
