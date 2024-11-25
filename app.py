from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import os
import json
import firebase_admin
from firebase_admin import credentials, messaging

# Initialiser l'application Flask
app = Flask(__name__)

# Configuration MongoDB
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://admin:admin@cluster0.314tv.mongodb.net/home_security?retryWrites=true&w=majority&appName=Cluster0&tls=true&tlsAllowInvalidCertificates=true")

try:
    mongo = PyMongo(app)
    alerts_collection = mongo.db.alerts  # Collection MongoDB pour les alertes
except Exception as e:
    print("Erreur de connexion à MongoDB :", e)

# Configuration Firebase
try:
    firebase_credentials = os.getenv("FIREBASE_CREDENTIALS")
    if firebase_credentials:
        creds_dict = json.loads(firebase_credentials)
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
    else:
        raise Exception("La variable d'environnement FIREBASE_CREDENTIALS est manquante.")
except Exception as e:
    print("Erreur de configuration Firebase :", e)


# Route pour tester MongoDB
@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        # Insérer un document de test
        test_data = {"message": "Connexion réussie avec MongoDB!"}
        alerts_collection.insert_one(test_data)

        # Lire tous les documents de la collection
        alerts = list(alerts_collection.find({}, {"_id": 0}))  # Exclut le champ `_id` de la réponse
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Fonction pour envoyer des notifications via Firebase
def send_notification(title, body):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic="alerts"  # Topic par défaut
        )
        response = messaging.send(message)
        print("Notification envoyée :", response)
    except Exception as e:
        print("Erreur lors de l'envoi de la notification :", e)


# Route pour tester Firebase
@app.route('/test-notification', methods=['POST'])
def test_notification():
    try:
        data = request.json
        send_notification(data.get("title", "Test Notification"), data.get("body", "Notification envoyée avec succès"))
        return jsonify({"message": "Notification envoyée."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route pour créer une alerte
@app.route('/alert', methods=['POST'])
def alert():
    try:
        data = request.json
        # Sauvegarder l'alerte dans MongoDB
        alert_id = alerts_collection.insert_one(data).inserted_id

        # Envoyer une notification
        send_notification(data.get("title", "Alerte"), data.get("body", "Un mouvement a été détecté"))

        return jsonify({"message": "Alerte créée.", "alert_id": str(alert_id)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route pour récupérer les alertes
@app.route('/alerts', methods=['GET'])
def get_alerts():
    try:
        alerts = list(alerts_collection.find({}, {"_id": 0}))  # Exclut le champ `_id`
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Point d'entrée principal
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
