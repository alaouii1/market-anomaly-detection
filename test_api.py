import requests

# URL de l'API Binance
url = "https://api.binance.com/api/v3/ticker/price"

# Paramètres : quelle crypto on veut
params = {
    "symbol": "BTCUSDT"
}

# Envoyer la requête
response = requests.get(url, params=params)

# Vérifier le statut
print(f"Status code: {response.status_code}")

# Si succès, afficher les données
if response.status_code == 200:
    # data = response.json()
    # print(f"✅ Succès !")
    # print(f"Symbol: {data['symbol']}")
    # print(f"Prix: ${data['price']}")
    print(response)
    
    # Convertir en nombre pour calculs
    # prix = float(data['price'])
    # print(f"Prix (float): {prix}")
    # print(f"Prix + 1000: {prix + 1000}")
else:
    print(f"❌ Erreur: {response.status_code}")
    print(response.text)